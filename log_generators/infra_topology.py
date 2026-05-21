"""Shared infrastructure topology — single source of truth for service → host/pod/container placement.

Builds a deterministic, seeded mapping from service name to OTel infrastructure resource
attributes. All generators (traces, JVM metrics, APM rollup, k8s metrics) import from here
so every signal carries the same host.name / container.id / k8s.pod.* join keys. This is
what makes the APM Service Map → Infrastructure correlation panel light up.
"""
from __future__ import annotations

import random
import uuid


def build_topology(scenario_data: dict) -> dict[str, dict]:
    """Return service_name → infra attrs dict. Deterministic (seed 42 + cluster_idx).

    Mirrors the RNG call sequence of k8s_metrics_generator._init_pod_data exactly so
    pod/container IDs are identical whether read here or from the k8s metrics generator.
    """
    hosts: list[dict] = scenario_data.get("hosts", [])
    k8s_clusters: list[dict] = scenario_data.get("k8s_clusters", [])
    services: dict = scenario_data.get("services", {})
    namespace: str = scenario_data.get("namespace", "default")

    host_by_provider: dict[str, dict] = {h.get("cloud.provider", "aws"): h for h in hosts}
    topology: dict[str, dict] = {}

    for idx, cluster in enumerate(k8s_clusters):
        stable = random.Random(42 + idx)
        region = cluster["region"]

        # Mirror _init_pod_data: generate 3 node names with same 2-randint-per-node sequence
        node_names = [
            f"ip-10-0-{stable.randint(10, 200)}-{stable.randint(10, 200)}.{region}.compute.internal"
            for _ in range(3)
        ]

        host = host_by_provider.get(cluster.get("provider", "aws"), hosts[0] if hosts else {})
        zones = cluster.get("zones", [region + "-a"])

        for svc in cluster.get("services", []):
            # Mirror _init_pod_data RNG sequence per service exactly
            node_name = stable.choice(node_names)
            pod_hex1 = f"{stable.getrandbits(32):08x}"
            pod_hex2 = f"{stable.getrandbits(24):06x}"
            pod_uid = str(uuid.UUID(int=stable.getrandbits(128)))
            pod_ip = (
                f"10.{stable.randint(100, 120)}"
                f".{stable.randint(1, 10)}"
                f".{stable.randint(2, 250)}"
            )
            node_uid = str(uuid.UUID(int=stable.getrandbits(128)))
            replicaset_hex = f"{stable.getrandbits(32):08x}"
            container_id = f"containerd://{stable.getrandbits(256):064x}"

            topology[svc] = {
                "host.name": host.get("host.name", f"{svc}-host"),
                "host.id": host.get("host.id", f"{svc}-id"),
                "host.arch": host.get("host.arch", "amd64"),
                "cloud.provider": cluster.get("provider", "aws"),
                "cloud.platform": cluster.get("platform", "aws_eks"),
                "cloud.region": cluster.get("region", "us-east-1"),
                "cloud.availability_zone": zones[0],
                "cloud.account.id": host.get("cloud.account.id", ""),
                "cloud.instance.id": host.get("cloud.instance.id", ""),
                "container.id": container_id,
                "container.name": f"{svc}-container",
                "container.image.name": f"{svc}:latest",
                "k8s.pod.name": f"{svc}-{pod_hex1}-{pod_hex2}",
                "k8s.pod.uid": pod_uid,
                "k8s.pod.ip": pod_ip,
                "k8s.namespace.name": namespace,
                "k8s.deployment.name": f"{svc}-deployment",
                "k8s.replicaset.name": f"{svc}-{replicaset_hex}",
                "k8s.node.name": node_name,
                "k8s.node.uid": node_uid,
                "k8s.cluster.name": cluster.get("name", f"cluster-{idx}"),
                "_node_name": node_name,
                "_is_k8s": True,
                "_service_instance_id": pod_uid,
            }

    # Services not in any cluster — host-only placement
    for svc, cfg in services.items():
        if svc in topology:
            continue
        cloud = cfg.get("cloud_provider", "aws")
        host = host_by_provider.get(cloud, hosts[0] if hosts else {})
        topology[svc] = {
            "host.name": host.get("host.name", f"{svc}-host"),
            "host.id": host.get("host.id", f"{svc}-id"),
            "host.arch": host.get("host.arch", "amd64"),
            "cloud.provider": host.get("cloud.provider", cfg.get("cloud_provider", "aws")),
            "cloud.platform": host.get("cloud.platform", cfg.get("cloud_platform", "aws_ec2")),
            "cloud.region": host.get("cloud.region", cfg.get("cloud_region", "us-east-1")),
            "cloud.availability_zone": host.get(
                "cloud.availability_zone", cfg.get("cloud_availability_zone", "us-east-1a")
            ),
            "cloud.account.id": host.get("cloud.account.id", ""),
            "cloud.instance.id": host.get("cloud.instance.id", ""),
            "_is_k8s": False,
            "_service_instance_id": f"{svc}-001",
        }

    return topology


def get_resource_attrs(topology: dict, service_name: str) -> dict:
    """Return OTel attribute key-values for a service (suitable for _format_attributes()).

    Includes host.name / host.id and, for k8s-deployed services, full container and pod attrs.
    """
    entry = topology.get(service_name)
    if not entry:
        return {}

    attrs: dict = {
        "host.name": entry["host.name"],
        "host.id": entry["host.id"],
    }

    if entry.get("_is_k8s"):
        attrs.update({
            "container.id": entry["container.id"],
            "k8s.pod.name": entry["k8s.pod.name"],
            "k8s.pod.uid": entry["k8s.pod.uid"],
            "k8s.pod.ip": entry["k8s.pod.ip"],
            "k8s.namespace.name": entry["k8s.namespace.name"],
            "k8s.deployment.name": entry["k8s.deployment.name"],
            "k8s.replicaset.name": entry["k8s.replicaset.name"],
            "k8s.node.name": entry["k8s.node.name"],
            "k8s.node.uid": entry["k8s.node.uid"],
            "k8s.cluster.name": entry["k8s.cluster.name"],
        })

    return attrs


def to_pod_data(topology: dict, cluster: dict) -> dict:
    """Convert topology into the pod_data format expected by k8s_metrics_generator.

    Returns {"pods": {svc: {...}}, "node_names": [...]} with values from the shared
    topology so k8s metrics and traces share identical pod/container/node identifiers.
    """
    pods: dict = {}
    node_names_set: set = set()

    for svc in cluster.get("services", []):
        entry = topology.get(svc)
        if not entry or not entry.get("_is_k8s"):
            continue
        pods[svc] = {
            "pod_name": entry["k8s.pod.name"],
            "pod_uid": entry["k8s.pod.uid"],
            "pod_ip": entry["k8s.pod.ip"],
            "node_name": entry["k8s.node.name"],
            "node_uid": entry["k8s.node.uid"],
            "deployment_name": entry["k8s.deployment.name"],
            "replicaset_name": entry["k8s.replicaset.name"],
            "container_id": entry["container.id"],
        }
        node_names_set.add(entry["k8s.node.name"])

    return {"pods": pods, "node_names": list(node_names_set)}
