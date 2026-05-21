"""ApmMixin — APM rollup and APM anomaly detection methods."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from elastic_config.deployer_base import _es_headers, ProgressCallback

logger = logging.getLogger("deployer")


class ApmMixin:

    def _deploy_apm_rollup(self, client: httpx.Client, notify: ProgressCallback):
        """Step 4: Generate synthetic APM rollup data and deploy DB ingest pipeline."""
        from elastic_config.apm_rollup import ApmRollupGenerator

        step = self._step(6)
        step.status = "running"
        notify(self.progress)

        try:
            gen = ApmRollupGenerator(self.scenario, self.elastic_url, self.api_key)
            counts = gen.generate_all(hours=12)
            total = sum(counts.values())

            self._deploy_db_ingest_pipeline(client)
            self._set_metrics_look_back_time(client)

            step.status = "ok"
            step.detail = (
                f"Inserted {total} rollup docs "
                f"(tx={counts.get('transaction_1m', 0)}, "
                f"sd={counts.get('service_destination_1m', 0)}, "
                f"sum={counts.get('service_summary_1m', 0)})"
            )
        except Exception as exc:
            step.status = "failed"
            step.detail = str(exc)
            logger.warning("APM rollup generation failed (non-fatal): %s", exc)
        notify(self.progress)

    def _build_db_pipeline_name(self) -> str:
        return f"{self.scenario.scenario_id}-db-dependency-names"

    def _deploy_db_ingest_pipeline(self, client: httpx.Client) -> None:
        """Install an ingest pipeline that rewrites span.destination.service.resource
        for DB CLIENT spans to use the logical DB service name instead of the
        generic postgresql resource string."""
        db_ops = self.scenario.db_operations
        services = self.scenario.services
        topology = self.scenario.service_topology

        # Build service → db_service_name map from topology
        db_services = {
            name for name, cfg in services.items()
            if cfg.get("subsystem") == "database"
        }
        svc_to_db: dict[str, str] = {}
        for caller, calls in topology.items():
            for callee, *_ in calls:
                if callee in db_services:
                    svc_to_db[caller] = callee

        if not db_ops or not svc_to_db:
            return  # Nothing to rewrite

        # Build Painless conditions: for each service with DB ops, rewrite resource
        conditions: list[str] = []
        for svc in db_ops:
            db_svc = svc_to_db.get(svc)
            if not db_svc:
                continue
            conditions.append(
                f"if (ctx.resource?.attributes?.['service.name'] == '{svc}') {{"
                f" ctx.attributes['span.destination.service.resource'] = '{db_svc}'; }}"
            )

        if not conditions:
            return

        script_source = (
            "if (ctx.attributes?.containsKey('span.destination.service.resource') != true) { return; }"
            " String res = ctx.attributes['span.destination.service.resource'];"
            " if (!res.startsWith('postgresql')) { return; }"
            " " + " else ".join(conditions)
        )

        pipeline_name = self._build_db_pipeline_name()
        pipeline_body = {
            "description": f"Rewrite DB resource names for {self.scenario.scenario_id} APM Service Map",
            "processors": [
                {
                    "script": {
                        "lang": "painless",
                        "source": script_source,
                        "ignore_failure": True,
                    }
                }
            ],
        }
        try:
            client.put(
                f"{self.elastic_url}/_ingest/pipeline/{pipeline_name}",
                headers=_es_headers(self.api_key),
                json=pipeline_body,
            )
            logger.info("Deployed DB ingest pipeline: %s", pipeline_name)
        except Exception as exc:
            logger.warning("DB ingest pipeline deploy failed (non-fatal): %s", exc)

    def _set_metrics_look_back_time(self, client: httpx.Client) -> None:
        """Set index.look_back_time: 7d on the metrics@custom component template
        so APM rollup data is visible in the Service Map."""
        try:
            client.put(
                f"{self.elastic_url}/_component_template/metrics@custom",
                headers=_es_headers(self.api_key),
                json={
                    "template": {
                        "settings": {
                            "index": {
                                "look_back_time": "7d",
                            }
                        }
                    }
                },
            )
        except Exception as exc:
            logger.warning("metrics@custom look_back_time update failed (non-fatal): %s", exc)

    def _deploy_apm_anomaly_detection(self, client: httpx.Client, notify: ProgressCallback):
        """Create APM ML anomaly detection job and start datafeed.

        Modelled after the job created by the Kibana APM ML module:
        - Single job, three detectors (latency / throughput / failure-rate)
        - Composite aggregation (date_histogram + transaction.type + service.name)
        - summary_count_field_name: "doc_count" (composite bucket doc_count)
        """
        step = self._step(16)
        step.status = "running"
        notify(self.progress)

        try:
            ns = self.scenario.namespace
            env = f"production-{ns}"
            job_id = f"apm-{ns}-transaction-metrics"

            job_cfg = {
                "job_id": job_id,
                "description": (
                    "Detects anomalies in transaction latency, throughput and error "
                    f"percentage for {env}."
                ),
                "groups": ["apm"],
                "custom_settings": {
                    "created_by": "elastic-launch-demo",
                    "job_tags": {
                        "environment": env,
                        "apm_ml_version": 3,
                    },
                },
                "analysis_config": {
                    "bucket_span": "15m",
                    "summary_count_field_name": "doc_count",
                    "detectors": [
                        {
                            "detector_description": "high latency by transaction type for an APM service",
                            "function": "high_mean",
                            "field_name": "transaction_latency",
                            "by_field_name": "attributes.transaction.type",
                            "partition_field_name": "resource.attributes.service.name",
                        },
                        {
                            "detector_description": "transaction throughput for an APM service",
                            "function": "mean",
                            "field_name": "transaction_throughput",
                            "by_field_name": "attributes.transaction.type",
                            "partition_field_name": "resource.attributes.service.name",
                        },
                        {
                            "detector_description": "failed transaction rate for an APM service",
                            "function": "high_mean",
                            "field_name": "failed_transaction_rate",
                            "by_field_name": "attributes.transaction.type",
                            "partition_field_name": "resource.attributes.service.name",
                        },
                    ],
                    "influencers": [
                        "attributes.transaction.type",
                        "resource.attributes.service.name",
                    ],
                    "model_prune_window": "30d",
                },
                "analysis_limits": {"model_memory_limit": "64mb"},
                "data_description": {"time_field": "@timestamp", "time_format": "epoch_ms"},
                "model_plot_config": {"enabled": True, "annotations_enabled": True},
                "model_snapshot_retention_days": 10,
                "daily_model_snapshot_retention_after_days": 1,
                "results_index_name": "custom-apm",
                "allow_lazy_open": True,
            }

            datafeed_cfg = {
                "job_id": job_id,
                "indices": ["metrics-transaction.1m.otel-default"],
                "chunking_config": {"mode": "off"},
                "indices_options": {
                    "ignore_unavailable": True,
                    "expand_wildcards": ["open"],
                    "allow_no_indices": True,
                },
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"attributes.metricset.name": "transaction"}},
                            {"term": {"resource.attributes.deployment.environment": env}},
                        ]
                    }
                },
                "aggregations": {
                    "buckets": {
                        "composite": {
                            "size": 5000,
                            "sources": [
                                {
                                    "date": {
                                        "date_histogram": {
                                            "field": "@timestamp",
                                            "fixed_interval": "60s",
                                        }
                                    }
                                },
                                {
                                    "attributes.transaction.type": {
                                        "terms": {"field": "attributes.transaction.type"}
                                    }
                                },
                                {
                                    "resource.attributes.service.name": {
                                        "terms": {"field": "resource.attributes.service.name"}
                                    }
                                },
                            ],
                        },
                        "aggs": {
                            "@timestamp": {"max": {"field": "@timestamp"}},
                            "transaction_throughput": {"rate": {"unit": "minute"}},
                            "transaction_latency": {
                                "avg": {"field": "metrics.transaction.duration.histogram"}
                            },
                            "error_count": {
                                "filter": {"term": {"attributes.event.outcome": "failure"}},
                                "aggs": {
                                    "actual_error_count": {
                                        "value_count": {"field": "attributes.event.outcome"}
                                    }
                                },
                            },
                            "success_count": {
                                "filter": {"term": {"attributes.event.outcome": "success"}}
                            },
                            "failed_transaction_rate": {
                                "bucket_script": {
                                    "buckets_path": {
                                        "failure_count": "error_count>_count",
                                        "success_count": "success_count>_count",
                                    },
                                    "script": (
                                        "if ((params.failure_count + params.success_count)==0)"
                                        "{return 0;}else{return 100 * (params.failure_count/"
                                        "(params.failure_count + params.success_count));}"
                                    ),
                                }
                            },
                        },
                    }
                },
                "scroll_size": 1000,
                "delayed_data_check_config": {"enabled": True},
            }

            # Delete existing job+datafeed so we can recreate cleanly
            client.post(
                f"{self.elastic_url}/_ml/datafeeds/datafeed-{job_id}/_stop",
                headers=_es_headers(self.api_key),
            )
            client.delete(
                f"{self.elastic_url}/_ml/datafeeds/datafeed-{job_id}",
                headers=_es_headers(self.api_key),
            )
            client.post(
                f"{self.elastic_url}/_ml/anomaly_detectors/{job_id}/_close",
                headers=_es_headers(self.api_key),
                json={"force": True},
            )
            client.delete(
                f"{self.elastic_url}/_ml/anomaly_detectors/{job_id}",
                headers=_es_headers(self.api_key),
            )

            # Create job
            resp = client.put(
                f"{self.elastic_url}/_ml/anomaly_detectors/{job_id}",
                headers=_es_headers(self.api_key),
                json=job_cfg,
            )
            if resp.status_code >= 300:
                raise RuntimeError(f"ML job create failed: {resp.text}")

            # Create datafeed
            resp = client.put(
                f"{self.elastic_url}/_ml/datafeeds/datafeed-{job_id}",
                headers=_es_headers(self.api_key),
                json=datafeed_cfg,
            )
            if resp.status_code >= 300:
                raise RuntimeError(f"ML datafeed create failed: {resp.text}")

            # Open job
            resp = client.post(
                f"{self.elastic_url}/_ml/anomaly_detectors/{job_id}/_open",
                headers=_es_headers(self.api_key),
            )
            if resp.status_code >= 300:
                raise RuntimeError(f"ML job open failed: {resp.text}")

            # Start datafeed from rollup start so historical data trains the model
            start_body: dict[str, Any] = {}
            rollup_start = self._get_apm_rollup_start(client)
            if rollup_start:
                start_body["start"] = rollup_start
            resp = client.post(
                f"{self.elastic_url}/_ml/datafeeds/datafeed-{job_id}/_start",
                headers=_es_headers(self.api_key),
                json=start_body,
            )
            if resp.status_code >= 300:
                raise RuntimeError(f"ML datafeed start failed: {resp.text}")

            step.status = "ok"
            step.detail = f"Started ML job: {job_id}"
        except Exception as exc:
            step.status = "failed"
            step.detail = str(exc)
            logger.warning("APM anomaly detection setup failed (non-fatal): %s", exc)
        notify(self.progress)

    def _get_apm_rollup_start(self, client: httpx.Client) -> str | None:
        """Query the earliest @timestamp in the transaction rollup index."""
        try:
            resp = client.post(
                f"{self.elastic_url}/metrics-transaction.1m.otel-default/_search",
                headers=_es_headers(self.api_key),
                json={
                    "size": 0,
                    "aggs": {
                        "min_ts": {"min": {"field": "@timestamp"}}
                    },
                },
            )
            if resp.status_code < 300:
                val = resp.json().get("aggregations", {}).get("min_ts", {}).get("value_as_string")
                if val:
                    return val
        except Exception:
            pass
        return None

    def _cleanup_apm_ml(self, client: httpx.Client, namespace: str | None = None) -> None:
        """Delete APM ML jobs and datafeeds for the given namespace (or self.ns)."""
        ns = namespace or self.ns
        job_ids = [
            f"apm-{ns}-transaction-metrics",
            # Legacy job IDs — cleaned up in case of leftover state from prior deploys
            f"apm-{ns}-latency",
            f"apm-{ns}-throughput",
            f"apm-{ns}-failure-rate",
        ]
        for job_id in job_ids:
            try:
                client.post(
                    f"{self.elastic_url}/_ml/datafeeds/datafeed-{job_id}/_stop",
                    headers=_es_headers(self.api_key),
                )
                client.delete(
                    f"{self.elastic_url}/_ml/datafeeds/datafeed-{job_id}",
                    headers=_es_headers(self.api_key),
                )
                client.post(
                    f"{self.elastic_url}/_ml/anomaly_detectors/{job_id}/_close",
                    headers=_es_headers(self.api_key),
                    json={"force": True},
                )
                client.delete(
                    f"{self.elastic_url}/_ml/anomaly_detectors/{job_id}",
                    headers=_es_headers(self.api_key),
                )
            except Exception:
                pass
        # Also delete DB ingest pipeline
        try:
            pipeline_name = f"{self.scenario.scenario_id}-db-dependency-names"
            client.delete(
                f"{self.elastic_url}/_ingest/pipeline/{pipeline_name}",
                headers=_es_headers(self.api_key),
            )
        except Exception:
            pass
