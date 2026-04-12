from __future__ import annotations

from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
STORE_ROOT = ROOT / ".runtime-store" / "objects"
LEGACY_DIRS = ("logs", "memory", "queue", "receipts", "state")


def _merge_tree(src: Path, dst: Path, skipped: list[str]) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            _merge_tree(item, target, skipped)
            try:
                item.rmdir()
            except OSError:
                pass
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            item.replace(target)
        except PermissionError:
            try:
                shutil.copy2(item, target)
            except PermissionError:
                skipped.append(str(item))
                continue
            try:
                item.unlink()
            except PermissionError:
                skipped.append(str(item))
    try:
        src.rmdir()
    except OSError:
        pass


def migrate() -> tuple[list[tuple[str, str]], list[str]]:
    moves: list[tuple[str, str]] = []
    skipped: list[str] = []
    STORE_ROOT.mkdir(parents=True, exist_ok=True)
    for legacy_name in LEGACY_DIRS:
        src = ROOT / legacy_name
        if not src.exists():
            continue
        dst = STORE_ROOT / legacy_name
        _merge_tree(src, dst, skipped)
        moves.append((str(src), str(dst)))
    return moves, skipped


def main() -> int:
    moves, skipped = migrate()
    if not moves:
        print("No legacy runtime directories found to migrate.")
        return 0
    print("Migrated runtime artifacts:")
    for src, dst in moves:
        print(f"- {src} -> {dst}")
    if skipped:
        print("Skipped locked files:")
        for path in skipped:
            print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
