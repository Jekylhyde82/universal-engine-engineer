"""Provider-neutral structural interfaces for the approved integration domains."""
from typing import Protocol
from ..contracts import ProviderRequest, ProviderResult

class WorkflowProvider(Protocol):
    """Coordinates stateful workflows; it is not the global policy authority."""
    def run(self, request: ProviderRequest) -> ProviderResult: ...
    def resume(self, checkpoint_id: str, request: ProviderRequest) -> ProviderResult: ...

class InferenceProvider(Protocol):
    """Produces model inference results behind a provider-neutral boundary."""
    def generate(self, request: ProviderRequest) -> ProviderResult: ...

class KnowledgeProvider(Protocol):
    """Ingests and retrieves knowledge/document context."""
    def ingest(self, request: ProviderRequest) -> ProviderResult: ...
    def retrieve(self, request: ProviderRequest) -> ProviderResult: ...

class VectorStoreProvider(Protocol):
    """Persists and searches vector representations."""
    def upsert(self, request: ProviderRequest) -> ProviderResult: ...
    def search(self, request: ProviderRequest) -> ProviderResult: ...

class EvaluationProvider(Protocol):
    """Evaluates prompts, models, agents, and retrieval outputs."""
    def evaluate(self, request: ProviderRequest) -> ProviderResult: ...

class CodingAgentProvider(Protocol):
    """Produces isolated patch proposals; it does not imply merge authority."""
    def propose_patch(self, request: ProviderRequest) -> ProviderResult: ...
