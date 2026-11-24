"""Optional local-model RAG evaluation. Skips unless configured explicitly."""
import os
import pytest

DEEPEVAL_ENV = ("LOCAL_MODEL_NAME", "LOCAL_MODEL_BASE_URL", "LOCAL_MODEL_API_KEY")
if not all(os.getenv(name) for name in DEEPEVAL_ENV):
    pytest.skip("Set LOCAL_MODEL_NAME, LOCAL_MODEL_BASE_URL and LOCAL_MODEL_API_KEY to run local DeepEval", allow_module_level=True)

from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.models import LocalModel
from deepeval.test_case import LLMTestCase


def test_local_rag_answer_relevance_and_faithfulness():
    model = LocalModel(
        model=os.environ["LOCAL_MODEL_NAME"],
        base_url=os.environ["LOCAL_MODEL_BASE_URL"],
        api_key=os.environ["LOCAL_MODEL_API_KEY"],
        temperature=0,
    )
    test_case = LLMTestCase(
        input="What is the runtime policy for a provider request?",
        actual_output="The runtime evaluates an exact-match policy and denies requests without an allow rule.",
        retrieval_context=[
            "The policy engine uses exact-match rules. No matching allow rule means deny.",
            "Dispatch evaluates policy before provider execution and does not trust caller-supplied approval decisions.",
        ],
    )
    metrics = [
        AnswerRelevancyMetric(model=model, threshold=0.7),
        FaithfulnessMetric(model=model, threshold=0.7),
    ]
    assert_test(test_case, metrics)
