"""Optional LangGraph workflow adapter using an injected StateGraph builder."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from ..contracts import ProviderRequest, ProviderResult, ResultStatus


class LangGraphWorkflowAdapter:
    """Compiles a LangGraph builder with an explicit checkpointer.

    The application chooses the checkpointer implementation. Use an in-memory
    checkpointer only for development/tests; production needs durable storage.
    """

    provider_id = "langgraph"

    def __init__(
        self,
        graph_builder: Any,
        *,
        checkpointer: Any,
        resume_command_factory: Callable[[Any], Any] | None = None,
    ) -> None:
        if checkpointer is None:
            raise ValueError("an explicit LangGraph checkpointer is required")
        if not callable(getattr(graph_builder, "compile", None)):
            raise ValueError("graph_builder must provide compile()")
        self.graph = graph_builder.compile(checkpointer=checkpointer)
        if not callable(getattr(self.graph, "invoke", None)):
            raise ValueError("compiled graph must provide invoke()")
        self.resume_command_factory = resume_command_factory

    def run(self, request: ProviderRequest) -> ProviderResult:
        return self.execute(request)

    def resume(self, checkpoint_id: str, request: ProviderRequest) -> ProviderResult:
        # The thread ID is the LangGraph checkpoint namespace. The optional
        # checkpoint_id is accepted for interface compatibility and recorded
        # in request payload by callers when they need a specific snapshot.
        return self.execute(request)

    def execute(self, request: ProviderRequest) -> ProviderResult:
        if not request.policy.allowed:
            return ProviderResult(request.correlation_id, ResultStatus.DENIED, {"reason": request.policy.reason}, "POLICY_DENIED")
        if request.deadline is not None and request.deadline <= datetime.now(timezone.utc):
            return ProviderResult(request.correlation_id, ResultStatus.TIMED_OUT, {}, "DEADLINE_EXPIRED")
        try:
            payload = dict(request.payload)
            thread_id = payload.get("thread_id")
            if not isinstance(thread_id, str) or not thread_id.strip():
                raise ValueError("thread_id is required for checkpointed workflow execution")
            config = {"configurable": {"thread_id": thread_id}}
            if request.operation == "run":
                if set(payload) != {"thread_id", "input"} or not isinstance(payload["input"], dict):
                    raise ValueError("run requires thread_id and an object input")
                result = self.graph.invoke(payload["input"], config)
            elif request.operation == "resume":
                if set(payload) != {"thread_id", "resume_value"}:
                    raise ValueError("resume requires thread_id and resume_value")
                command = self._resume_command(payload["resume_value"])
                result = self.graph.invoke(command, config)
            else:
                raise ValueError("operation must be 'run' or 'resume'")
            if not isinstance(result, dict):
                raise ValueError("workflow result must be an object")
            return ProviderResult(request.correlation_id, ResultStatus.SUCCEEDED, {"state": result, "thread_id": thread_id})
        except (TypeError, ValueError, KeyError, AttributeError) as exc:
            return ProviderResult(request.correlation_id, ResultStatus.FAILED, {}, "INVALID_WORKFLOW_REQUEST", str(exc))
        except Exception:
            return ProviderResult(request.correlation_id, ResultStatus.FAILED, {}, "WORKFLOW_EXECUTION_FAILED", "LangGraph execution failed")

    def _resume_command(self, value: Any) -> Any:
        if self.resume_command_factory is not None:
            return self.resume_command_factory(value)
        try:
            from langgraph.types import Command
        except ImportError as exc:
            raise RuntimeError("install the selected langgraph package to resume an interrupted graph") from exc
        return Command(resume=value)
