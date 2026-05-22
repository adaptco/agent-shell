# Ensure asyncio is imported at the top of runtime/api.py
import asyncio

# ... inside create_app() ...

    @app.get("/tasks/{task_id}/stream")
    async def stream_task(
        task_id: str,
        operator: OperatorIdentity = Depends(auth_operator),
        service: AgentService = Depends(svc),
    ):
        if not is_valid_id(task_id):
            raise HTTPException(status_code=400, detail="Invalid task ID format")

        # FIX: Run the initial synchronous file/DB I/O in a separate thread to avoid blocking the loop
        task_info = await asyncio.to_thread(service.get_task, task_id)
        if task_info is None:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        async def event_generator():
            import json
            from runtime.utils import read_json

            seen_receipts = set()
            while True:
                current_task = await asyncio.to_thread(service.get_task, task_id)

                if service.receipts and service.receipts.root.exists():
                    def get_new_receipts():
                        return [
                            str(p)
                            for p in service.receipts.root.rglob(f"*{task_id}*.json")
                            if str(p) not in seen_receipts
                        ]

                    new_paths = await asyncio.to_thread(get_new_receipts)
                    for path_str in sorted(new_paths):
                        try:
                            r_data = read_json(path_str)
                            yield f"event: receipt\ndata: {json.dumps(r_data)}\n\n"
                            seen_receipts.add(path_str)
                        except Exception as e:
                            # FIX: Log the exception instead of a silent 'pass' to aid troubleshooting
                            if hasattr(service, "logger"):
                                service.logger.warning(f"Error processing receipt: {path_str}", exc_info=True)
                            else:
                                print(f"Error processing receipt {path_str}: {e}")

                if current_task:
                    status = current_task.get("status")
                    if status in ("done", "failed"):
                        yield f"event: final\ndata: {json.dumps(current_task)}\n\n"
                        break

                await asyncio.sleep(2)

        from fastapi.responses import StreamingResponse
        return StreamingResponse(event_generator(), media_type="text/event-stream")