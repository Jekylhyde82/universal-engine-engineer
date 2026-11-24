import unittest
from uuid import uuid4

from universal_engine.contracts import PolicyDecision, ProviderRequest, ResultStatus
from universal_engine.providers.langgraph import LangGraphWorkflowAdapter


class FakeGraph:
    def __init__(self):
        self.calls = []
    def invoke(self, value, config):
        self.calls.append((value, config))
        return {"answer": "done"}


class FakeBuilder:
    def __init__(self):
        self.checkpointer = None
        self.graph = FakeGraph()
    def compile(self, *, checkpointer):
        self.checkpointer = checkpointer
        return self.graph


class LangGraphAdapterTests(unittest.TestCase):
    def make_request(self, operation, payload, policy=None):
        return ProviderRequest(
            correlation_id=str(uuid4()),
            capability_id="workflow.langgraph",
            operation=operation,
            payload=payload,
            policy=policy or PolicyDecision(True, "approved", "test-policy"),
        )

    def test_requires_explicit_checkpointer(self):
        with self.assertRaises(ValueError):
            LangGraphWorkflowAdapter(FakeBuilder(), checkpointer=None)

    def test_compiles_builder_with_checkpointer(self):
        builder = FakeBuilder()
        checkpointer = object()
        LangGraphWorkflowAdapter(builder, checkpointer=checkpointer)
        self.assertIs(builder.checkpointer, checkpointer)

    def test_runs_graph_with_thread_id(self):
        builder = FakeBuilder()
        adapter = LangGraphWorkflowAdapter(builder, checkpointer=object())
        request = self.make_request("run", {"thread_id": "thread-1", "input": {"question": "hello"}})
        result = adapter.execute(request)
        self.assertEqual(result.status, ResultStatus.SUCCEEDED)
        self.assertEqual(builder.graph.calls[0][1]["configurable"]["thread_id"], "thread-1")

    def test_resumes_graph_with_command_factory(self):
        builder = FakeBuilder()
        adapter = LangGraphWorkflowAdapter(builder, checkpointer=object(), resume_command_factory=lambda value: {"resume": value})
        request = self.make_request("resume", {"thread_id": "thread-1", "resume_value": "yes"})
        result = adapter.execute(request)
        self.assertEqual(result.status, ResultStatus.SUCCEEDED)
        self.assertEqual(builder.graph.calls[0][0], {"resume": "yes"})

    def test_resume_uses_requested_checkpoint_id(self):
        builder = FakeBuilder()
        adapter = LangGraphWorkflowAdapter(builder, checkpointer=object(), resume_command_factory=lambda value: {"resume": value})
        request = self.make_request("resume", {"thread_id": "thread-1", "resume_value": "yes"})
        result = adapter.resume("checkpoint-7", request)
        self.assertEqual(result.status, ResultStatus.SUCCEEDED)
        self.assertEqual(builder.graph.calls[0][1]["configurable"]["checkpoint_id"], "checkpoint-7")

    def test_denied_request_never_invokes_graph(self):
        builder = FakeBuilder()
        adapter = LangGraphWorkflowAdapter(builder, checkpointer=object())
        request = self.make_request("run", {"thread_id": "thread-1", "input": {}}, PolicyDecision(False, "denied", "deny"))
        result = adapter.execute(request)
        self.assertEqual(result.status, ResultStatus.DENIED)
        self.assertEqual(builder.graph.calls, [])

    def test_requires_thread_id(self):
        adapter = LangGraphWorkflowAdapter(FakeBuilder(), checkpointer=object())
        result = adapter.execute(self.make_request("run", {"input": {}}))
        self.assertEqual(result.error_code, "INVALID_WORKFLOW_REQUEST")


if __name__ == "__main__":
    unittest.main()
