# LangGraph Workflow Adapter

The fourth real provider adapter wraps a LangGraph StateGraph builder.

## Supported operations
- Compiles the injected graph builder with an explicitly supplied checkpointer.
- Runs a graph with an object input and required thread_id.
- Resumes an interrupted graph using Command(resume=...) or an injected command factory.
- Uses the same thread_id configuration for checkpoint lookup and continuity.

## Persistence requirements
- The adapter refuses to compile without an explicit checkpointer.
- In-memory checkpointers are for development/testing only.
- Production must supply a durable checkpointer backend and test restart/recovery behaviour.
- A thread_id is required on every run/resume operation.

## Limitations
- The adapter accepts only object graph input and object graph output.
- It does not stream events, expose state history, create threads, manage stores, or support subgraph operations.
- The synchronous invoke call cannot be forcibly interrupted by the adapter after a deadline; upstream graph nodes and infrastructure need their own timeouts.
- The adapter requires the application to install and pin a compatible LangGraph package.
- The CI tests use a fake builder; actual tests against a pinned LangGraph release and durable checkpointer remain required.

## Test method
Tests verify builder compilation, thread_id configuration, resume command handling, default-deny behaviour and malformed inputs without installing LangGraph.
