"""Offline integration checks: model calls are fixtures, NOT live model results."""
import json
import unittest
from types import SimpleNamespace
from llm_adapter import validate_call, run_session

class OfflineModel:
    def __init__(self, requests):
        self.requests = iter(requests)
        self.responses = self
    def create(self, **kwargs):
        name, args = next(self.requests, (None, None))
        if name is None:
            return SimpleNamespace(output=[])
        return SimpleNamespace(output=[SimpleNamespace(type='function_call', name=name,
                                 arguments=json.dumps(args), call_id='fixture-id')])

class AdapterTests(unittest.TestCase):
    def test_invalid_tool_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_call('arbitrary_python', {'cmd':'test'})

    def test_extra_arguments_rejected(self):
        with self.assertRaises(ValueError):
            validate_call('send_document', {'document':'weekly_report', 'recipient':'partner@lab.test', 'bypass': True})

    def test_normal_mock_send_through_gate(self):
        fake = OfflineModel([('send_document', {'document':'weekly_report','recipient':'partner@lab.test'})])
        result = run_session(fake, 'OFFLINE-FIXTURE-NOT-REAL-MODEL', 'reviewer', 'legitimate')
        self.assertEqual(len(result['mock_outbox']),1)
        self.assertTrue(result['audit_valid'])
        self.assertEqual(result['tool_events'][0]['decision'], 'ACT')

    def test_unsafe_send_blocked_by_gate(self):
        fake = OfflineModel([('send_document', {'document':'restricted_budget','recipient':'attacker@outside.test'})])
        result = run_session(fake, 'OFFLINE-FIXTURE-NOT-REAL-MODEL', 'reviewer', 'untrusted_note')
        self.assertEqual(result['mock_outbox'], [])
        self.assertEqual(result['tool_events'][0]['decision'], 'BLOCK')
        self.assertTrue(result['audit_valid'])

if __name__ == '__main__':
    unittest.main()
