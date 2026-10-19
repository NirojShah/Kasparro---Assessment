"""LLM-based V1 agent for claim extraction and classification."""
import json
import os
from typing import Dict, List, Optional

from google import genai
from google.genai import types

from .data_loader import BrandFacts


class ClaimExtractionAgentV1LLM:
    """Extract and classify factual claims with the Gemini API."""

    def __init__(
        self,
        brand_facts: BrandFacts,
        api_key: Optional[str] = None,
        client: Optional[genai.Client] = None,
    ):
        self.brand_facts = brand_facts
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if client is None and not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is required to use the LLM agent. "
                "Set it in the environment or in the project .env file."
            )

        self.client = client if client is not None else genai.Client(api_key=self.api_key)
        self.model_name = "gemini-3.8-flash"

    def get_brand_facts(self, brand_id: str, model_id: str) -> List[Dict]:
        """Get brand facts for a specific model."""
        return self.brand_facts.get_facts_by_model(brand_id, model_id)

    def _generate_json(self, prompt: str, max_output_tokens: int) -> object:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=max_output_tokens,
                response_mime_type="application/json",
            ),
        )
        if not response.text:
            raise ValueError("Gemini returned an empty response.")
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise ValueError("Gemini returned invalid JSON.") from exc

    def extract_claims(
        self, answer_text: str, brand_id: str, model_id: str
    ) -> List[Dict]:
        """Extract factual claim sentences and their character offsets."""
        prompt = f"""Extract factual claim sentences from this text about a speaker product.

Text:
{answer_text}

Instructions:
1. Identify sentences that make factual claims (price, specs, warranty, features, etc.)
2. IGNORE: General advice, instructions, opinions, sentences starting with "Keep", "Ask", "Before"
3. Extract the exact sentence text and its zero-based start and end character positions in the original text. The end position is exclusive.

Return a JSON array with this structure:
[
  {{
    "start_char": <integer>,
    "end_char": <integer>,
    "quote": "<exact sentence text>"
  }}
]

Return [] if no claims are found."""

        result = self._generate_json(prompt, max_output_tokens=2048)
        if not isinstance(result, list):
            raise ValueError("Gemini claim extraction response must be a JSON array.")

        claims = []
        for index, claim in enumerate(result):
            if not isinstance(claim, dict):
                raise ValueError(f"Gemini claim at index {index} must be a JSON object.")
            start = claim.get("start_char")
            end = claim.get("end_char")
            quote = claim.get("quote")
            if (
                type(start) is not int
                or type(end) is not int
                or not isinstance(quote, str)
                or start < 0
                or end <= start
                or answer_text[start:end] != quote
            ):
                raise ValueError(
                    f"Gemini claim at index {index} has invalid offsets or quote."
                )
            claims.append({"start_char": start, "end_char": end, "quote": quote})
        return claims

    def classify_claims_batch(
        self, claims: List[Dict], brand_id: str, model_id: str
    ) -> List[Dict]:
        """Classify claims in one Gemini request using the model's known facts."""
        if not claims:
            return []

        facts = self.get_brand_facts(brand_id, model_id)
        facts_summary = self._summarize_facts(facts)
        quotes = [claim["quote"] for claim in claims]
        prompt = f"""Classify each claim based only on the facts provided.

Context:
- Brand: {brand_id}
- Model: {model_id}
- Available facts about this model:
{facts_summary}

Claims list:
{json.dumps(quotes)}

Rules:
- "supported": directly supported by the facts
- "contradicted": directly contradicted by the facts
- "unknown": the facts do not provide enough information

Return a JSON array of labels in the exact same order as the claims. Each label
must be "supported", "contradicted", or "unknown"."""

        result = self._generate_json(prompt, max_output_tokens=1024)
        valid_labels = {"supported", "contradicted", "unknown"}
        if (
            not isinstance(result, list)
            or len(result) != len(claims)
            or any(
                not isinstance(label, str) or label not in valid_labels
                for label in result
            )
        ):
            raise ValueError(
                "Gemini classification response must contain one valid label "
                "per claim."
            )

        for claim, label in zip(claims, result):
            claim["classification"] = label
        return claims

    def process_answer(
        self, answer_id: str, answer_text: str, brand_id: str, model_id: str
    ) -> List[Dict]:
        """Extract and classify all claims in an answer."""
        claims = self.extract_claims(answer_text, brand_id, model_id)
        classified_claims = self.classify_claims_batch(claims, brand_id, model_id)
        for claim in classified_claims:
            claim["answer_id"] = answer_id
        return classified_claims

    def _summarize_facts(self, facts: List[Dict]) -> str:
        """Format facts for inclusion in the classification prompt."""
        if not facts:
            return "No facts available for this model."

        return "\n".join(
            f"- {fact.get('field')}: {fact.get('value')} {fact.get('unit', '')} "
            f"(condition: {fact.get('condition') or 'none'})"
            for fact in facts
        )
