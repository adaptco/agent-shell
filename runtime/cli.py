from __future__ import annotations
import argparse
import json
from runtime.service import AgentService
from runtime.worker import run_worker
from runtime.server import main as server_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-shell")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor")
    sub.add_parser("health")

    p_queue = sub.add_parser("queue-add")
    p_queue.add_argument("--task", required=True)
    p_queue.add_argument("--parent-task-id")
    p_queue.add_argument("--assigned-subagent")

    p_tasks = sub.add_parser("tasks")
    p_tasks.add_argument("--limit", type=int, default=100)
    p_tasks.add_argument("--task-id")

    p_run_next = sub.add_parser("run-next")
    p_run_next.add_argument("--backend", default="mock")
    p_run_next.add_argument("--worker-id")

    p_run_task = sub.add_parser("run-task")
    p_run_task.add_argument("--task", required=True)
    p_run_task.add_argument("--backend", default="mock")

    p_worker = sub.add_parser("worker")
    p_worker.add_argument("--backend", default="mock")
    p_worker.add_argument("--count", type=int, default=1)
    p_worker.add_argument("--worker-id")

    p_hb = sub.add_parser("heartbeat")
    p_hb.add_argument("--worker-id")

    p_serve = sub.add_parser("serve-api")
    p_serve.add_argument("--host")
    p_serve.add_argument("--port", type=int)
    p_serve.add_argument("--reload", action="store_true")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = AgentService()
    if args.cmd == "doctor":
        result = service.doctor()
    elif args.cmd == "health":
        result = service.health()
    elif args.cmd == "queue-add":
        result = service.queue_add(args.task, parent_task_id=args.parent_task_id, assigned_subagent=args.assigned_subagent)
    elif args.cmd == "tasks":
        result = service.get_task(args.task_id) if args.task_id else service.list_tasks(limit=args.limit)
    elif args.cmd == "run-next":
        result = service.run_next(args.backend, worker_id=args.worker_id)
    elif args.cmd == "run-task":
        result = service.run_task(args.task, args.backend)
    elif args.cmd == "worker":
        result = run_worker(service, args.backend, args.count, worker_id=args.worker_id)
    elif args.cmd == "heartbeat":
        result = service.heartbeat(worker_id=args.worker_id)
    elif args.cmd == "serve-api":
        server_args = []
        if args.host:
            server_args.extend(["--host", args.host])
        if args.port is not None:
            server_args.extend(["--port", str(args.port)])
        if args.reload:
            server_args.append("--reload")
        return server_main(server_args)
    else:
        parser.error("unknown command")
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
