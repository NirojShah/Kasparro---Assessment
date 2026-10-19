"""V1 Rule-based Agent for claim extraction and classification."""
import re
from typing import List, Dict, Optional
from .data_loader import BrandFacts


class ClaimExtractionAgentV1:
    """V1 rule-based agent for extracting and classifying factual claims."""
    
    def __init__(self, brand_facts: BrandFacts):
        self.brand_facts = brand_facts
    
    def get_brand_facts(self, brand_id: str, model_id: str) -> List[Dict]:
        """Tool to get brand facts for a specific model."""
        return self.brand_facts.get_facts_by_model(brand_id, model_id)
    
    def extract_claims(self, answer_text: str, brand_id: str, model_id: str) -> List[Dict]:
        """
        Extract factual claim sentences from the AI answer using rule-based heuristics.
        
        Returns list of claims with:
        - start_char: start position in text
        - end_char: end position in text
        - quote: the extracted text
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', answer_text)
        
        claims = []
        current_pos = 0
        
        # Patterns that indicate factual claims
        claim_patterns = [
            r'\b(costs?|price|inr|₹)\b',
            r'\b(hours?|minutes?|battery|playback)\b',
            r'\b(warranty|month|year)\b',
            r'\b(includes?|contains?|adapter|cable)\b',
            r'\b(wifi|bluetooth|microphone|connector)\b',
            r'\b(weight|grams?|kilograms?|kg)\b',
            r'\b(water|immersion|ipx\d+)\b',
            r'\b(supported|supports?|contradicted|contradicts?)\b',
            r'\b(listed|less|more|compare)\b',
        ]
        
        # Patterns to ignore (instructions/advice)
        ignore_patterns = [
            r'^Keep the exact model',
            r'^Ask whether',
            r'^Before choosing',
            r'^For a practical decision',
            r'^When making the final choice',
            r'^After reading',
            r'^A useful shortlist',
            r'^Retain the original',
            r'^Ask about unresolved',
            r'^Avoid treating',
            r'^Compare the statements',
            r'^Write the relevant',
            r'^If a comparison',
        ]
        
        for sentence in sentences:
            start = current_pos
            end = current_pos + len(sentence)
            current_pos = end + 1  # +1 for the space we split on
            
            # Check if should ignore
            should_ignore = False
            for pattern in ignore_patterns:
                if re.match(pattern, sentence.strip(), re.IGNORECASE):
                    should_ignore = True
                    break
            
            if should_ignore:
                continue
            
            # Check if it looks like a factual claim
            is_claim = False
            for pattern in claim_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    is_claim = True
                    break
            
            if is_claim:
                claims.append({
                    'start_char': start,
                    'end_char': end,
                    'quote': sentence.strip()
                })
        
        return claims
    
    def classify_claim(self, claim_text: str, brand_id: str, model_id: str) -> str:
        """
        Classify a claim as supported, contradicted, or unknown using rule-based logic.
        
        Uses the brand facts catalogue to determine classification.
        """
        facts = self.get_brand_facts(brand_id, model_id)
        
        # Extract key information from claim
        claim_lower = claim_text.lower()
        
        # Check each fact to see if claim matches or contradicts
        for fact in facts:
            fact_field = fact['field'].lower()
            fact_value = str(fact['value']).lower()
            
            # Check if claim mentions this field
            if fact_field in claim_lower:
                # Simple matching logic
                if fact_value in claim_lower:
                    # Check for negation
                    if 'not' in claim_lower or 'no' in claim_lower or 'does not' in claim_lower:
                        if fact['value_type'] == 'boolean' and fact_value == 'false':
                            return 'supported'
                        elif fact['value_type'] == 'boolean' and fact_value == 'true':
                            return 'contradicted'
                    return 'supported'
                else:
                    # Value mismatch - could be contradiction or unknown
                    # For now, conservatively return unknown
                    pass
        
        # Default to unknown if no clear match
        return 'unknown'
    
    def process_answer(self, answer_id: str, answer_text: str, brand_id: str, model_id: str) -> List[Dict]:
        """
        Process a single answer: extract claims and classify them.
        
        Returns list of claims with classifications.
        """
        # Extract claims
        claims = self.extract_claims(answer_text, brand_id, model_id)
        
        # Classify each claim
        for claim in claims:
            claim['classification'] = self.classify_claim(
                claim['quote'], brand_id, model_id
            )
            claim['answer_id'] = answer_id
        
        return claims
