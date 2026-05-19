"""Concurrency throttle for deploy and teardown operations.

Caps concurrent operations at MAX_CONCURRENT. Excess submissions queue FIFO,
with deploys taking priority over teardowns when a slot opens.
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional

logger = logging.getLogger("op_queue")

MAX_CONCURRENT = 2

PositionCallback = Callable[[int, int], None]  # (position, total) — both 1-indexed/sized
Runner = Callable[[], None]


@dataclass
class _QueuedOp:
    kind: str  # "deploy" | "teardown"
    deployment_id: str
    runner: Runner
    on_position: Optional[PositionCallback]


class OperationQueue:
    def __init__(self, max_concurrent: int = MAX_CONCURRENT):
        self._max = max_concurrent
        # deployment_id → kind ("deploy" | "teardown"). dict preserves insertion
        # order, so iterating gives ops in the order they started running.
        self._active: dict[str, str] = {}
        self._deploy_q: deque[_QueuedOp] = deque()
        self._teardown_q: deque[_QueuedOp] = deque()
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._dispatcher = threading.Thread(target=self._dispatch_loop, daemon=True)
        self._dispatcher.start()

    # ── Submission ────────────────────────────────────────────────────────

    def submit_deploy(
        self,
        deployment_id: str,
        runner: Runner,
        on_position: Optional[PositionCallback] = None,
    ) -> bool:
        return self._submit("deploy", deployment_id, runner, on_position)

    def submit_teardown(
        self,
        deployment_id: str,
        runner: Runner,
        on_position: Optional[PositionCallback] = None,
    ) -> bool:
        return self._submit("teardown", deployment_id, runner, on_position)

    def _submit(
        self,
        kind: str,
        deployment_id: str,
        runner: Runner,
        on_position: Optional[PositionCallback],
    ) -> bool:
        with self._cond:
            if deployment_id in self._active:
                logger.info("Rejecting %s for %s: already active", kind, deployment_id)
                return False
            if any(op.deployment_id == deployment_id for op in self._deploy_q):
                logger.info("Rejecting %s for %s: already queued for deploy", kind, deployment_id)
                return False
            if any(op.deployment_id == deployment_id for op in self._teardown_q):
                logger.info("Rejecting %s for %s: already queued for teardown", kind, deployment_id)
                return False

            op = _QueuedOp(kind=kind, deployment_id=deployment_id, runner=runner, on_position=on_position)
            q = self._deploy_q if kind == "deploy" else self._teardown_q
            q.append(op)
            self._notify_positions_locked()
            self._cond.notify_all()
        return True

    # ── Cancellation ──────────────────────────────────────────────────────

    def cancel_deploy(self, deployment_id: str) -> bool:
        """Remove a queued deploy that hasn't started yet. Returns True if cancelled."""
        with self._cond:
            for i, op in enumerate(self._deploy_q):
                if op.deployment_id == deployment_id:
                    del self._deploy_q[i]
                    self._notify_positions_locked()
                    self._cond.notify_all()
                    return True
        return False

    # ── Diagnostics ───────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "active": list(self._active),  # insertion order = start order
                "deploy_queue": [op.deployment_id for op in self._deploy_q],
                "teardown_queue": [op.deployment_id for op in self._teardown_q],
            }

    def list_ordered(self, kind: str) -> list[str]:
        """Return deployment_ids for `kind` in execution order: actively running
        first (in the order they started), then queued (in queue position order).
        """
        if kind not in ("deploy", "teardown"):
            return []
        with self._lock:
            active_in_kind = [did for did, k in self._active.items() if k == kind]
            q = self._deploy_q if kind == "deploy" else self._teardown_q
            queued = [op.deployment_id for op in q]
            return active_in_kind + queued

    # ── Internals ─────────────────────────────────────────────────────────

    def _notify_positions_locked(self) -> None:
        """Call on_position for every queued op so they see their current 1-indexed slot."""
        total = len(self._deploy_q) + len(self._teardown_q)
        for i, op in enumerate(self._deploy_q):
            if op.on_position:
                try:
                    op.on_position(i + 1, total)
                except Exception:
                    logger.exception("on_position callback failed for %s", op.deployment_id)
        offset = len(self._deploy_q)
        for i, op in enumerate(self._teardown_q):
            if op.on_position:
                try:
                    op.on_position(offset + i + 1, total)
                except Exception:
                    logger.exception("on_position callback failed for %s", op.deployment_id)

    def _dispatch_loop(self) -> None:
        while True:
            with self._cond:
                while not self._can_dispatch_locked():
                    self._cond.wait()
                # Deploy queue has priority.
                if self._deploy_q:
                    op = self._deploy_q.popleft()
                else:
                    op = self._teardown_q.popleft()
                self._active[op.deployment_id] = op.kind
                self._notify_positions_locked()

            worker = threading.Thread(
                target=self._run_op, args=(op,), daemon=True,
                name=f"op-{op.kind}-{op.deployment_id}",
            )
            worker.start()

    def _can_dispatch_locked(self) -> bool:
        return len(self._active) < self._max and (self._deploy_q or self._teardown_q)

    def _run_op(self, op: _QueuedOp) -> None:
        try:
            op.runner()
        except Exception:
            logger.exception("Runner for %s %s raised", op.kind, op.deployment_id)
        finally:
            with self._cond:
                self._active.pop(op.deployment_id, None)
                self._cond.notify_all()
