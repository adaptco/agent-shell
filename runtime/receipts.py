from __future__ import annotations

from typing import Any
from pathlib import Path

from runtime.config import resolve_path
from runtime.utils import utc_now, sha256_hex, write_json


class ReceiptWriter:
    def __init__(self, cfg):
        self.cfg = cfg
        self.root = resolve_path(cfg, cfg["receipts"]["dir"])

    def emit(
        self,
        task_id: str,
        step: str,
        status: str,
        inputs=None,
        outputs=None,
        error=None,
        memory_snapshot=None,
    ) -> Path:
        created_at = utc_now()
        date_part = created_at.split("T", 1)[0].replace("-", "")
        target_dir = self.root / date_part
        target_dir.mkdir(parents=True, exist_ok=True)
        # Scrub credentials from inputs and outputs
        inputs = self._scrub(inputs or {})
        outputs = self._scrub(outputs or {})

        receipt = {
            "receipt_id": f"{task_id}-{step}-{created_at.replace(':', '').replace('+', '_')}",
            "task_id": task_id,
            "step": step,
            "status": status,
            "created_at": created_at,
            "inputs_sha256": sha256_hex(inputs),
            "outputs_sha256": sha256_hex(outputs),
            "inputs": inputs,
            "outputs": outputs,
            "error": error,
            "memory_snapshot": self._scrub(memory_snapshot or []),
        }
        path = target_dir / f"{receipt['receipt_id']}.json"
        write_json(path, receipt)
        return path

    def _scrub(self, data: Any) -> Any:
        """Recursively scrub sensitive keys from data"""
        sensitive_keys = {"api_key", "token", "secret", "password", "auth", "bearer", "authorization"}
        if isinstance(data, dict):
            return {k: (self._scrub(v) if k.lower() not in sensitive_keys else "[REDACTED]") for k, v in data.items()}
        elif isinstance(data, list):
            return [self._scrub(item) for item in data]
        return data
