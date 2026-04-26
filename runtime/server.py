from __future__ import annotations
import argparse
import uvicorn
from runtime.config import load_config


def main(argv=None) -> int:
    cfg = load_config()
    parser = argparse.ArgumentParser(prog="agent-shell-api")
    parser.add_argument(
        "--host", default=cfg.get("service", {}).get("host", "127.0.0.1")
    )
    parser.add_argument(
        "--port", type=int, default=cfg.get("service", {}).get("port", 0)
    )
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args(argv)
    uvicorn.run(
        "runtime.api:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
