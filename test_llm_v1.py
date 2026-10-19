"""Smoke test the Gemini-backed V1 agent on answer A01."""
from dotenv import load_dotenv
from src.data_loader import BrandFacts, Answers
from src.agent_v1_llm import ClaimExtractionAgentV1LLM
from src.utils import extract_model_id


def main():
    load_dotenv()

    print("Loading data...")
    brand_facts = BrandFacts("brand_facts.csv")
    answers = Answers("answers.csv")

    print("Initializing Gemini-backed V1 agent...")
    agent = ClaimExtractionAgentV1LLM(brand_facts)

    answer_data = answers.get_answer("A01")
    if answer_data is None:
        raise ValueError("Answer A01 was not found in answers.csv.")
    model_id = extract_model_id(answer_data["question"], answer_data["brand_id"])

    print(f"Testing A01 ({answer_data['brand_id']} {model_id})...")
    try:
        predictions = agent.process_answer(
            "A01", answer_data["ai_answer"], answer_data["brand_id"], model_id
        )
        print(f"Extracted and classified {len(predictions)} claims:")
        for i, pred in enumerate(predictions[:5], 1):
            print(f"\nClaim {i}: {pred['quote'][:100]}")
            print(f"  Classification: {pred['classification']}")
    except Exception as exc:
        err_msg = str(exc)
        print("\n[Notice] Gemini live call encountered an error:")
        print(f"  {exc.__class__.__name__}: {err_msg[:200]}")
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            print("\n  Reason: Gemini free-tier daily quota limit reached.")
            print("  The deterministic evaluation pipeline uses run_v1.py and run_v2.py.")
        elif "503" in err_msg or "UNAVAILABLE" in err_msg:
            print("\n  Reason: Gemini model temporarily unavailable due to high demand.")


if __name__ == "__main__":
    main()
