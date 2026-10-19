"""Data loading utilities for the claim extraction system."""
import csv
from pathlib import Path
from typing import Dict, List, Optional


class BrandFacts:
    """Container for brand facts catalogue."""
    
    def __init__(self, facts_path: str):
        self.facts: Dict[str, Dict] = {}
        self._load_facts(facts_path)
    
    def _load_facts(self, facts_path: str):
        """Load facts from CSV."""
        with open(facts_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                fact_id = row['fact_id']
                self.facts[fact_id] = {
                    'fact_id': fact_id,
                    'brand_id': row['brand_id'],
                    'model_id': row['model_id'],
                    'field': row['field'],
                    'value': row['value'],
                    'value_type': row['value_type'],
                    'unit': row['unit'],
                    'condition': row['condition'],
                    'valid_from': row['valid_from'],
                    'valid_to': row['valid_to'],
                }
    
    def get_fact(self, fact_id: str) -> Optional[Dict]:
        """Get a specific fact by ID."""
        return self.facts.get(fact_id)
    
    def get_facts_by_model(self, brand_id: str, model_id: str) -> List[Dict]:
        """Get all facts for a specific model."""
        return [
            fact for fact in self.facts.values()
            if fact['brand_id'] == brand_id and fact['model_id'] == model_id
        ]
    
    def get_facts_by_brand(self, brand_id: str) -> List[Dict]:
        """Get all facts for a specific brand."""
        return [
            fact for fact in self.facts.values()
            if fact['brand_id'] == brand_id
        ]


class Answers:
    """Container for AI answers."""
    
    def __init__(self, answers_path: str):
        self.answers: Dict[str, Dict] = {}
        self._load_answers(answers_path)
    
    def _load_answers(self, answers_path: str):
        """Load answers from CSV."""
        with open(answers_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                answer_id = row['answer_id']
                self.answers[answer_id] = {
                    'split': row['split'],
                    'brand_id': row['brand_id'],
                    'question': row['question'],
                    'ai_answer': row['ai_answer'],
                }
    
    def get_answer(self, answer_id: str) -> Optional[Dict]:
        """Get a specific answer by ID."""
        return self.answers.get(answer_id)
    
    def get_development_answers(self) -> List[Dict]:
        """Get all development split answers."""
        return [
            (aid, ans) for aid, ans in self.answers.items()
            if ans['split'] == 'development'
        ]
    
    def get_test_answers(self) -> List[Dict]:
        """Get all test split answers."""
        return [
            (aid, ans) for aid, ans in self.answers.items()
            if ans['split'] in ['test', 'check']
        ]


class GoldLabels:
    """Container for gold standard labels."""
    
    def __init__(self, gold_path: str):
        self.labels: Dict[str, List[Dict]] = {}
        self._load_gold(gold_path)
    
    def _load_gold(self, gold_path: str):
        """Load gold labels from CSV."""
        with open(gold_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                answer_id = row['answer_id']
                if answer_id not in self.labels:
                    self.labels[answer_id] = []
                self.labels[answer_id].append({
                    'claim_id': row['claim_id'],
                    'start_char': int(row['start_char']),
                    'end_char': int(row['end_char']),
                    'quote': row['quote'],
                    'expected_label': row['expected_label'],
                    'evidence_fact_ids': row['evidence_fact_ids'].split('|') if row['evidence_fact_ids'] else [],
                    'explanation': row['explanation'],
                    'difficulty_tags': row['difficulty_tags'].split('|') if row['difficulty_tags'] else [],
                })
    
    def get_labels(self, answer_id: str) -> List[Dict]:
        """Get all labels for a specific answer."""
        return self.labels.get(answer_id, [])
