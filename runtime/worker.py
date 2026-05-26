import time
from runtime.service import AgentService


def run_worker(
    service: AgentService, backend_name: str, count: int, worker_id: str | None = None
) -> list[dict]:
    results = []
    for _ in range(count):
        results.append(service.run_next(backend_name, worker_id=worker_id))
        service.heartbeat(worker_id=worker_id)
        time.sleep(service.cfg["queue"]["poll_seconds"])
    return results
