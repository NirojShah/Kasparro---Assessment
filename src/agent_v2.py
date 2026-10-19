"""V2 Agent for claim extraction and classification with improved classification logic."""
import re
from typing import List, Dict, Optional
from .data_loader import BrandFacts


class ClaimExtractionAgentV2:
    """V2 agent with improved classification logic."""
    
    def __init__(self, brand_facts: BrandFacts):
        self.brand_facts = brand_facts
    
    def get_brand_facts(self, brand_id: str, model_id: str) -> List[Dict]:
        """Tool to get brand facts for a specific model."""
        return self.brand_facts.get_facts_by_model(brand_id, model_id)
    
    def get_all_facts(self, brand_id: str) -> Dict[str, Dict]:
        """Get all facts for a brand as a dictionary for easy lookup."""
        all_facts = self.brand_facts.get_facts_by_brand(brand_id)
        return {fact['fact_id']: fact for fact in all_facts}
    
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
    
    def extract_number(self, text: str) -> Optional[float]:
        """Extract a number from text."""
        # Match numbers like 1,299 or 1299 or 1.5
        match = re.search(r'[\d,]+\.?\d*', text)
        if match:
            num_str = match.group().replace(',', '')
            try:
                return float(num_str)
            except ValueError:
                return None
        return None
    
    def classify_claim(self, claim_text: str, brand_id: str, model_id: str) -> str:
        """
        Classify a claim as supported, contradicted, or unknown using improved logic.
        
        Uses the brand facts catalogue to determine classification.
        """
        facts = self.get_brand_facts(brand_id, model_id)
        all_facts = self.get_all_facts(brand_id)
        
        claim_lower = claim_text.lower()
        
        # Check for negation
        has_negation = bool(re.search(r'\b(not|no|never|does not|do not|cannot)\b', claim_lower))
        
        # Extract numbers from claim
        claim_numbers = [self.extract_number(claim_text)]
        
        # Check each fact
        for fact in facts:
            fact_field = fact['field'].lower()
            fact_value = str(fact['value']).lower()
            fact_value_type = fact['value_type']
            
            # Check if claim mentions this field
            if fact_field in claim_lower:
                # Handle boolean facts
                if fact_value_type == 'boolean':
                    if has_negation:
                        # Claim says "not X", fact says "false" -> supported
                        if fact_value == 'false':
                            return 'supported'
                        # Claim says "not X", fact says "true" -> contradicted
                        elif fact_value == 'true':
                            return 'contradicted'
                    else:
                        # Claim says "X", fact says "true" -> supported
                        if fact_value == 'true':
                            return 'supported'
                        # Claim says "X", fact says "false" -> contradicted
                        elif fact_value == 'false':
                            return 'contradicted'
                
                # Handle numerical facts
                elif fact_value_type == 'number':
                    claim_num = self.extract_number(claim_text)
                    if claim_num is not None:
                        fact_num = float(fact['value'])
                        # Check for exact match
                        if abs(claim_num - fact_num) < 0.01:
                            return 'supported'
                        # Check for contradictions (very different values)
                        if abs(claim_num - fact_num) > fact_num * 0.5:
                            return 'contradicted'
                
                # Handle string facts
                elif fact_value_type == 'string':
                    if fact_value in claim_lower:
                        return 'supported'
                    # Check for contradictions (explicit different value)
                    if re.search(rf'\b{fact_value}\b', claim_lower):
                        return 'contradicted'
        
        # Handle cross-model comparisons
        # e.g., "ClearTrail Mini is listed at INR 1,200 less than ClearTrail Plus"
        comparison_pattern = r'(\w+)\s+is\s+(?:listed|costs?|priced)\s+(?:at\s+)?(?:inr\s+)?[\d,]+\s+(?:less|more)\s+than\s+(\w+)'
        match = re.search(comparison_pattern, claim_lower)
        if match:
            model1 = match.group(1)
            model2 = match.group(2)
            # Try to extract both prices and compare
            if model1 in claim_lower and model2 in claim_lower:
                # Get facts for both models
                model1_facts = self.brand_facts.get_facts_by_model(brand_id, model1.replace(' ', '').lower())
                model2_facts = self.brand_facts.get_facts_by_model(brand_id, model2.replace(' ', '').lower())
                
                model1_price = None
                model2_price = None
                
                for f in model1_facts:
                    if f['field'] == 'price_2026':
                        model1_price = float(f['value'])
                for f in model2_facts:
                    if f['field'] == 'price_2026':
                        model2_price = float(f['value'])
                
                if model1_price and model2_price:
                    # Extract the difference from claim
                    claim_diff = self.extract_number(claim_text)
                    if claim_diff:
                        actual_diff = abs(model1_price - model2_price)
                        if abs(claim_diff - actual_diff) < 1:
                            return 'supported'
                        return 'contradicted'
        
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
