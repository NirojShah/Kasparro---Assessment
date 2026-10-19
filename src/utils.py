"""Utility functions for the claim extraction system."""
import re
from typing import Optional


def extract_model_id(question: str, brand_id: str) -> str:
    """
    Extract model_id from the question text based on brand.
    
    Maps brand names to their model suffixes.
    """
    brand_model_map = {
        'cleartrail': ['mini', 'plus'],
        'cloudnote': ['air', 'studio'],
        'stonewave': ['go', 'max'],
    }
    
    question_lower = question.lower()
    
    for model in brand_model_map.get(brand_id, []):
        # Look for model name in question
        pattern = rf'\b{model}\b'
        if re.search(pattern, question_lower):
            return model
    
    # Default: try to extract from question
    if 'mini' in question_lower:
        return 'mini'
    elif 'plus' in question_lower:
        return 'plus'
    elif 'air' in question_lower:
        return 'air'
    elif 'studio' in question_lower:
        return 'studio'
    elif 'go' in question_lower:
        return 'go'
    elif 'max' in question_lower:
        return 'max'
    
    # Fallback to first available model for the brand
    models = brand_model_map.get(brand_id, ['mini'])
    return models[0]


def clean_claim_text(text: str) -> str:
    """Clean claim text by removing extra whitespace."""
    return ' '.join(text.split())
