from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
print("Zipapp packaging is intentionally disabled for this build.")
print(
    "Reason: the runtime needs a writable workspace containing infra/, tools/, hooks/, queue/, state/, and memory/."
)
print(
    "Supported deployment mode: extract the workspace and optionally run 'python -m pip install -e .' from the root."
)
print(ROOT)
