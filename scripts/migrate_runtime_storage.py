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
        if target.exists() or target.is_symlink():
            if target.is_dir():
                skipped.append(f"{item} (destination is a directory: {target})")
                continue
            try:
                target.unlink()
            except OSError as error:
                skipped.append(f"{item} (cannot replace destination {target}: {type(error).__name__}: {error})")
                continue
        try:
            shutil.move(str(item), str(target))
        except (OSError, shutil.Error) as error:
            skipped.append(f"{item} ({type(error).__name__}: {error})")
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
        print("Skipped files:")
        for path in skipped:
            print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
