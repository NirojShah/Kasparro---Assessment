"""Evaluation harness for claim extraction and classification."""
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class ClaimMatch:
    """Represents a match between predicted and gold claims."""
    pred_claim: Dict
    gold_claim: Dict
    match_type: str  # 'exact', 'partial', or 'none'


class Evaluator:
    """Deterministic evaluation harness for claim extraction and classification."""
    
    def __init__(self):
        self.iou_threshold = 0.5  # IoU threshold for claim matching
    
    def evaluate(
        self,
        predictions: List[Dict],
        gold_labels: List[Dict]
    ) -> Dict:
        """
        Evaluate predictions against gold labels.
        
        Returns metrics for:
        - Claim extraction (precision, recall, F1)
        - Classification (accuracy, per-class metrics)
        """
        # Match predictions to gold labels
        matches = self._match_claims(predictions, gold_labels)
        
        # Calculate extraction metrics
        extraction_metrics = self._calculate_extraction_metrics(predictions, gold_labels, matches)
        
        # Calculate classification metrics (only for matched claims)
        classification_metrics = self._calculate_classification_metrics(matches)
        
        # Calculate overall F1 (macro)
        overall_metrics = self._calculate_overall_metrics(extraction_metrics, classification_metrics)
        
        return {
            'extraction': extraction_metrics,
            'classification': classification_metrics,
            'overall': overall_metrics,
            'matches': [
                {
                    'pred_claim': m.pred_claim,
                    'gold_claim': m.gold_claim,
                    'match_type': m.match_type
                } for m in matches
            ],
        }
    
    def _match_claims(
        self,
        predictions: List[Dict],
        gold_labels: List[Dict]
    ) -> List[ClaimMatch]:
        """Match predicted claims to gold claims using IoU."""
        matches = []
        used_gold = set()
        used_pred = set()
        
        for i, pred in enumerate(predictions):
            best_match = None
            best_iou = 0.0
            
            for j, gold in enumerate(gold_labels):
                if j in used_gold:
                    continue
                
                iou = self._calculate_iou(
                    pred['start_char'], pred['end_char'],
                    gold['start_char'], gold['end_char']
                )
                
                if iou > best_iou:
                    best_iou = iou
                    best_match = (j, gold)
            
            if best_match and best_iou >= self.iou_threshold:
                j, gold = best_match
                matches.append(ClaimMatch(
                    pred_claim=pred,
                    gold_claim=gold,
                    match_type='exact' if best_iou == 1.0 else 'partial'
                ))
                used_gold.add(j)
                used_pred.add(i)
        
        # Add unmatched predictions and gold labels
        for i, pred in enumerate(predictions):
            if i not in used_pred:
                matches.append(ClaimMatch(
                    pred_claim=pred,
                    gold_claim=None,
                    match_type='none'
                ))
        
        for j, gold in enumerate(gold_labels):
            if j not in used_gold:
                matches.append(ClaimMatch(
                    pred_claim=None,
                    gold_claim=gold,
                    match_type='none'
                ))
        
        return matches
    
    def _calculate_iou(
        self,
        pred_start: int, pred_end: int,
        gold_start: int, gold_end: int
    ) -> float:
        """Calculate Intersection over Union for character spans."""
        intersection = max(0, min(pred_end, gold_end) - max(pred_start, gold_start))
        union = (pred_end - pred_start) + (gold_end - gold_start) - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _calculate_extraction_metrics(
        self,
        predictions: List[Dict],
        gold_labels: List[Dict],
        matches: List[ClaimMatch]
    ) -> Dict:
        """Calculate extraction metrics (precision, recall, F1)."""
        true_positives = sum(1 for m in matches if m.gold_claim is not None)
        false_positives = sum(1 for m in matches if m.gold_claim is None and m.pred_claim is not None)
        false_negatives = sum(1 for m in matches if m.pred_claim is None and m.gold_claim is not None)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'precision': precision,
            'recall': recall,
            'f1': f1,
        }
    
    def _calculate_classification_metrics(self, matches: List[ClaimMatch]) -> Dict:
        """Calculate classification metrics for matched claims."""
        matched = [m for m in matches if m.pred_claim is not None and m.gold_claim is not None]
        
        if not matched:
            return {
                'accuracy': 0.0,
                'supported_f1': 0.0,
                'contradicted_f1': 0.0,
                'unknown_f1': 0.0,
                'macro_f1': 0.0,
            }
        
        correct = 0
        per_class = {'supported': {'tp': 0, 'fp': 0, 'fn': 0},
                    'contradicted': {'tp': 0, 'fp': 0, 'fn': 0},
                    'unknown': {'tp': 0, 'fp': 0, 'fn': 0}}
        
        for m in matched:
            pred_label = m.pred_claim.get('classification', 'unknown')
            gold_label = m.gold_claim['expected_label']
            
            if pred_label == gold_label:
                correct += 1
                per_class[gold_label]['tp'] += 1
            else:
                per_class[gold_label]['fn'] += 1
                per_class[pred_label]['fp'] += 1
        
        accuracy = correct / len(matched)
        
        # Calculate per-class F1
        class_f1 = {}
        for label, counts in per_class.items():
            precision = counts['tp'] / (counts['tp'] + counts['fp']) if (counts['tp'] + counts['fp']) > 0 else 0.0
            recall = counts['tp'] / (counts['tp'] + counts['fn']) if (counts['tp'] + counts['fn']) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            class_f1[f"{label}_f1"] = f1
        
        macro_f1 = sum(class_f1.values()) / len(class_f1)
        
        return {
            'accuracy': accuracy,
            **class_f1,
            'macro_f1': macro_f1,
        }
    
    def _calculate_overall_metrics(
        self,
        extraction_metrics: Dict,
        classification_metrics: Dict
    ) -> Dict:
        """Calculate overall combined metrics."""
        # Weight extraction and classification equally
        extraction_f1 = extraction_metrics['f1']
        classification_macro_f1 = classification_metrics['macro_f1']
        
        overall_f1 = (extraction_f1 + classification_macro_f1) / 2
        
        return {
            'combined_f1': overall_f1,
        }
