## 2025-04-25 - [O(N) Glob Lookup in FileTaskQueue]
**Learning:** Using `Path.glob()` to find a single file by ID in a directory with thousands of files is an O(N) operation that scales poorly. For large task queues (e.g., thousands of "done" tasks), this leads to measurable latency in every `get_task` call.
**Action:** Use direct `Path / filename` lookups which are O(1) when the exact filename is known, and use more specific glob patterns (e.g., `*--{task_id}.json`) to minimize directory scanning.
