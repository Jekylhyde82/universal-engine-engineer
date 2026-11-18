import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import time
from universal_engine.contracts import ContractViolation, PolicyDecision, ProviderRequest, ProviderResult, ResultStatus
from universal_engine.runtime import dispatch

class RecordingProvider:
    def __init__(self, result=None):
        self.calls = 0
        self.result = result
    def execute(self, request):
        self.calls += 1
        return self.result or ProviderResult(request.correlation_id, ResultStatus.SUCCEEDED)

def make_request(**overrides):
    values = dict(correlation_id=str(uuid4()), capability_id="test.echo", operation="echo",
        policy=PolicyDecision(True, "approved", "test-policy"))
    values.update(overrides)
    return ProviderRequest(**values)

class DispatchTests(unittest.TestCase):
    def test_allowed_request_reaches_provider(self):
        provider = RecordingProvider()
        result = dispatch(provider, make_request())
        self.assertEqual(provider.calls, 1)
        self.assertEqual(result.status, ResultStatus.SUCCEEDED)
    def test_denied_request_never_reaches_provider(self):
        provider = RecordingProvider()
        request = make_request(policy=PolicyDecision(False, "not approved", "deny"))
        result = dispatch(provider, request)
        self.assertEqual(provider.calls, 0)
        self.assertEqual(result.status, ResultStatus.DENIED)
    def test_expired_deadline_never_reaches_provider(self):
        provider = RecordingProvider()
        request = make_request(deadline=datetime.now(timezone.utc)+timedelta(milliseconds=5))
        time.sleep(0.01)  # Simulate a request waiting in a queue past its deadline.
        result = dispatch(provider, request)
        self.assertEqual(provider.calls, 0)
        self.assertEqual(result.status, ResultStatus.TIMED_OUT)
    def test_rejects_mismatched_correlation(self):
        request = make_request()
        provider = RecordingProvider(ProviderResult(str(uuid4()), ResultStatus.SUCCEEDED))
        with self.assertRaises(ContractViolation):
            dispatch(provider, request)

if __name__ == "__main__":
    unittest.main()
