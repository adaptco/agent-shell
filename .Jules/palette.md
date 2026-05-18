
## 2026-04-25 - [Consistency in API Access and Error Feedback]
**Learning:** Developers and operators expect standard aliases like `/healthz` and immediate access to documentation from the root URL. Providing specific identifiers (like `task_id`) in 404 error messages significantly reduces debugging friction.
**Action:** Always include aliases for health checks and provide root redirects to documentation in API-first projects. Ensure error details include relevant context IDs.
