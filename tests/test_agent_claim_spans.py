import unittest
from unittest.mock import Mock

from src.agent_v1_rulebased import ClaimExtractionAgentV1
from src.agent_v2 import ClaimExtractionAgentV2


class ClaimExtractionSpanTests(unittest.TestCase):
    def test_rule_based_agents_preserve_exact_source_spans(self):
        answer = (
            "Battery life is 10 hours.\n\n"
            "  The speaker costs INR 1,299."
        )

        for agent_type in (ClaimExtractionAgentV1, ClaimExtractionAgentV2):
            with self.subTest(agent=agent_type.__name__):
                claims = agent_type(Mock()).extract_claims(
                    answer, "cleartrail", "mini"
                )

                self.assertEqual(len(claims), 2)
                for claim in claims:
                    self.assertEqual(
                        answer[claim["start_char"]:claim["end_char"]],
                        claim["quote"],
                    )
                self.assertEqual(claims[0]["start_char"], answer.index("Battery"))
                self.assertEqual(
                    claims[1]["start_char"], answer.index("The speaker")
                )


if __name__ == "__main__":
    unittest.main()
