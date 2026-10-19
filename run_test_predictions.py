"""Run both V1 and V2 on test set for final predictions."""
import os
import json
import csv
from pathlib import Path
from dotenv import load_dotenv

from src.data_loader import BrandFacts, Answers
from src.agent_v1_rulebased import ClaimExtractionAgentV1
from src.agent_v2 import ClaimExtractionAgentV2
from src.utils import extract_model_id


def main():
    load_dotenv()
    
    # Load data
    print("Loading data...")
    brand_facts = BrandFacts('brand_facts.csv')
    answers = Answers('answers.csv')
    
    # Get test answers
    test_answers = answers.get_test_answers()
    print(f"Found {len(test_answers)} test answers")
    
    # Run V1 on test set
    print("\n" + "="*80)
    print("Running V1 on test set...")
    print("="*80)
    
    agent_v1 = ClaimExtractionAgentV1(brand_facts)
    v1_predictions = {}
    
    for answer_id, answer_data in test_answers:
        print(f"\nProcessing {answer_id} with V1...")
        
        answer_text = answer_data['ai_answer']
        brand_id = answer_data['brand_id']
        question = answer_data['question']
        model_id = extract_model_id(question, brand_id)
        
        try:
            predictions = agent_v1.process_answer(answer_id, answer_text, brand_id, model_id)
            v1_predictions[answer_id] = predictions
            print(f"  Extracted {len(predictions)} claims")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Run V2 on test set
    print("\n" + "="*80)
    print("Running V2 on test set...")
    print("="*80)
    
    agent_v2 = ClaimExtractionAgentV2(brand_facts)
    v2_predictions = {}
    
    for answer_id, answer_data in test_answers:
        print(f"\nProcessing {answer_id} with V2...")
        
        answer_text = answer_data['ai_answer']
        brand_id = answer_data['brand_id']
        question = answer_data['question']
        model_id = extract_model_id(question, brand_id)
        
        try:
            predictions = agent_v2.process_answer(answer_id, answer_text, brand_id, model_id)
            v2_predictions[answer_id] = predictions
            print(f"  Extracted {len(predictions)} claims")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Save results
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    
    # Save V1 test predictions
    with open(results_dir / 'v1_test_predictions.json', 'w') as f:
        json.dump(v1_predictions, f, indent=2)
    
    with open(results_dir / 'v1_test_predictions.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['answer_id', 'start_char', 'end_char', 'quote', 'classification'])
        for answer_id, predictions in v1_predictions.items():
            for pred in predictions:
                writer.writerow([
                    answer_id,
                    pred['start_char'],
                    pred['end_char'],
                    pred['quote'],
                    pred['classification']
                ])
    
    # Save V2 test predictions
    with open(results_dir / 'v2_test_predictions.json', 'w') as f:
        json.dump(v2_predictions, f, indent=2)
    
    with open(results_dir / 'v2_test_predictions.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['answer_id', 'start_char', 'end_char', 'quote', 'classification'])
        for answer_id, predictions in v2_predictions.items():
            for pred in predictions:
                writer.writerow([
                    answer_id,
                    pred['start_char'],
                    pred['end_char'],
                    pred['quote'],
                    pred['classification']
                ])
    
    print(f"\nTest predictions saved to {results_dir}")
    print("\nTest prediction run complete!")


if __name__ == '__main__':
    main()
