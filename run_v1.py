"""Run V1 agent on development set."""
import os
import json
import csv
from pathlib import Path
from dotenv import load_dotenv

from src.data_loader import BrandFacts, Answers, GoldLabels
from src.agent_v1_rulebased import ClaimExtractionAgentV1
from src.evaluator import Evaluator
from src.utils import extract_model_id


def main():
    load_dotenv()
    
    # Load data
    print("Loading data...")
    brand_facts = BrandFacts('brand_facts.csv')
    answers = Answers('answers.csv')
    gold_labels = GoldLabels('development_gold.csv')
    
    # Initialize agent
    print("Initializing V1 agent...")
    agent = ClaimExtractionAgentV1(brand_facts)
    
    # Initialize evaluator
    evaluator = Evaluator()
    
    # Get development answers
    dev_answers = answers.get_development_answers()
    print(f"Found {len(dev_answers)} development answers")
    
    # Process each answer
    all_predictions = {}
    all_results = []
    
    for answer_id, answer_data in dev_answers:
        print(f"\nProcessing {answer_id}...")
        
        answer_text = answer_data['ai_answer']
        brand_id = answer_data['brand_id']
        question = answer_data['question']
        
        # Extract model_id from question
        model_id = extract_model_id(question, brand_id)
        print(f"  Brand: {brand_id}, Model: {model_id}")
        
        # Process answer
        try:
            predictions = agent.process_answer(answer_id, answer_text, brand_id, model_id)
            all_predictions[answer_id] = predictions
            
            # Get gold labels
            gold = gold_labels.get_labels(answer_id)
            
            # Evaluate
            results = evaluator.evaluate(predictions, gold)
            all_results.append({
                'answer_id': answer_id,
                'metrics': results,
            })
            
            print(f"  Extracted {len(predictions)} claims")
            print(f"  Extraction F1: {results['extraction']['f1']:.3f} ({results['extraction']['f1']*100:.1f}%)")
            print(f"  Classification Macro F1: {results['classification']['macro_f1']:.3f} ({results['classification']['macro_f1']*100:.1f}%)")
            print(f"  Overall Combined F1: {results['overall']['combined_f1']:.3f} ({results['overall']['combined_f1']*100:.1f}%)")
            
        except Exception as e:
            print(f"  Error processing {answer_id}: {e}")
            import traceback
            traceback.print_exc()
    
    # Calculate aggregate metrics
    print("\n" + "="*80)
    print("AGGREGATE METRICS")
    print("="*80)
    
    total_tp = sum(r['metrics']['extraction']['true_positives'] for r in all_results)
    total_fp = sum(r['metrics']['extraction']['false_positives'] for r in all_results)
    total_fn = sum(r['metrics']['extraction']['false_negatives'] for r in all_results)
    
    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0.0
    
    print(f"\nExtraction:")
    print(f"  True Positives: {total_tp}")
    print(f"  False Positives: {total_fp}")
    print(f"  False Negatives: {total_fn}")
    print(f"  Precision: {overall_precision:.3f} ({overall_precision*100:.1f}%)")
    print(f"  Recall: {overall_recall:.3f} ({overall_recall*100:.1f}%)")
    print(f"  F1: {overall_f1:.3f} ({overall_f1*100:.1f}%)")
    
    # Save results
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    
    # Save predictions
    with open(results_dir / 'v1_predictions.json', 'w') as f:
        json.dump(all_predictions, f, indent=2)
    
    # Save metrics
    with open(results_dir / 'v1_metrics.json', 'w') as f:
        json.dump({
            'aggregate': {
                'extraction': {
                    'true_positives': total_tp,
                    'false_positives': total_fp,
                    'false_negatives': total_fn,
                    'precision': overall_precision,
                    'recall': overall_recall,
                    'f1': overall_f1,
                },
                'per_answer': all_results,
            }
        }, f, indent=2)
    
    # Save predictions as CSV for easier review
    with open(results_dir / 'v1_predictions.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['answer_id', 'start_char', 'end_char', 'quote', 'classification'])
        for answer_id, predictions in all_predictions.items():
            for pred in predictions:
                writer.writerow([
                    answer_id,
                    pred['start_char'],
                    pred['end_char'],
                    pred['quote'],
                    pred['classification']
                ])
    
    print(f"\nResults saved to {results_dir}")
    print("\nV1 run complete!")


if __name__ == '__main__':
    main()
