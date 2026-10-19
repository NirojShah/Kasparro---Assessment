import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.agent_v1_llm import ClaimExtractionAgentV1LLM


class ClaimExtractionAgentV1LLMTests(unittest.TestCase):
    def setUp(self):
        self.brand_facts = Mock()
        self.brand_facts.get_facts_by_model.return_value = [
            {
                "field": "battery_life",
                "value": "10",
                "unit": "hours",
                "condition": "",
            }
        ]
        self.client = Mock()
        self.agent = ClaimExtractionAgentV1LLM(
            self.brand_facts, client=self.client
        )

    def test_extract_claims_requests_json_and_validates_source_spans(self):
        answer = "Battery life is 10 hours."
        self.client.models.generate_content.return_value = SimpleNamespace(
            text=json.dumps(
                [
                    {
                        "start_char": 0,
                        "end_char": len(answer),
                        "quote": answer,
                    }
                ]
            )
        )

        claims = self.agent.extract_claims(answer, "cleartrail", "mini")

        self.assertEqual(
            claims,
            [{"start_char": 0, "end_char": len(answer), "quote": answer}],
        )
        request = self.client.models.generate_content.call_args.kwargs
        self.assertEqual(request["model"], "gemini-3.8-flash")
        self.assertEqual(request["config"].response_mime_type, "application/json")

    def test_process_answer_classifies_claims_and_adds_answer_id(self):
        answer = "Battery life is 10 hours."
        self.client.models.generate_content.side_effect = [
            SimpleNamespace(
                text=json.dumps(
                    [
                        {
                            "start_char": 0,
                            "end_char": len(answer),
                            "quote": answer,
                        }
                    ]
                )
            ),
            SimpleNamespace(text='["supported"]'),
        ]

        predictions = self.agent.process_answer(
            "A01", answer, "cleartrail", "mini"
        )

        self.assertEqual(predictions[0]["classification"], "supported")
        self.assertEqual(predictions[0]["answer_id"], "A01")
        self.assertEqual(self.client.models.generate_content.call_count, 2)

    def test_classification_rejects_wrong_number_of_labels(self):
        self.client.models.generate_content.return_value = SimpleNamespace(
            text='["supported"]'
        )
        claims = [{"quote": "First."}, {"quote": "Second."}]

        with self.assertRaisesRegex(ValueError, "one valid label per claim"):
            self.agent.classify_claims_batch(claims, "cleartrail", "mini")

    def test_missing_api_key_fails_with_setup_guidance(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "GEMINI_API_KEY"):
                ClaimExtractionAgentV1LLM(self.brand_facts)


if __name__ == "__main__":
    unittest.main()
