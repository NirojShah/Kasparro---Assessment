"""FastAPI service for claim extraction API."""
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from .database import engine, get_db, Run, Answer, Prediction, create_tables
from .data_loader import BrandFacts, Answers
from .agent_v1_rulebased import ClaimExtractionAgentV1
from .agent_v2 import ClaimExtractionAgentV2
from .evaluator import Evaluator
from .utils import extract_model_id

app = FastAPI(title="Kasparo Claim Extraction API")


@app.on_event("startup")
async def startup_event():
    """Initialize database and brand facts on startup."""
    # Create tables (will fail if PostgreSQL not running, but that's OK)
    try:
        create_tables()
    except Exception as e:
        print(f"Warning: Could not create database tables: {e}")
        print("PostgreSQL may not be running. API will work but database features will be disabled.")
    
    # Initialize brand facts
    global brand_facts, answers_data
    brand_facts = BrandFacts('brand_facts.csv')
    answers_data = Answers('answers.csv')


@app.on_event("startup")
async def startup_event():
    """Initialize brand facts on startup."""
    global brand_facts, answers_data
    brand_facts = BrandFacts('brand_facts.csv')
    answers_data = Answers('answers.csv')


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Kasparo Claim Extraction API", "versions": ["v1", "v2"]}


@app.post("/run/{version}")
async def run_agent(
    version: str,
    answer_id: str,
    db: Session = Depends(get_db)
):
    """
    Run agent on a single answer.
    
    Args:
        version: "v1" or "v2"
        answer_id: ID of the answer to process
    
    Returns:
        Predictions for the answer
    """
    if version not in ["v1", "v2"]:
        raise HTTPException(status_code=400, detail="Version must be 'v1' or 'v2'")
    
    # Get answer data
    answer_data = answers_data.get_answer(answer_id)
    if not answer_data:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    # Initialize agent
    if version == "v1":
        agent = ClaimExtractionAgentV1(brand_facts)
    else:
        agent = ClaimExtractionAgentV2(brand_facts)
    
    # Extract model_id
    model_id = extract_model_id(answer_data['question'], answer_data['brand_id'])
    
    # Process answer
    predictions = agent.process_answer(
        answer_id,
        answer_data['ai_answer'],
        answer_data['brand_id'],
        model_id
    )
    
    # Store in database
    run_id = str(uuid.uuid4())
    
    # Store answer
    db_answer = Answer(
        id=str(uuid.uuid4()),
        run_id=run_id,
        answer_id=answer_id,
        brand_id=answer_data['brand_id'],
        model_id=model_id,
        text=answer_data['ai_answer']
    )
    db.add(db_answer)
    
    # Store predictions
    for pred in predictions:
        db_pred = Prediction(
            id=str(uuid.uuid4()),
            run_id=run_id,
            answer_id=answer_id,
            start_char=pred['start_char'],
            end_char=pred['end_char'],
            quote=pred['quote'],
            classification=pred['classification']
        )
        db.add(db_pred)
    
    db.commit()
    
    return {
        "run_id": run_id,
        "answer_id": answer_id,
        "predictions": predictions
    }


@app.post("/evaluate/{version}")
async def evaluate_agent(
    version: str,
    db: Session = Depends(get_db)
):
    """
    Run agent on all development answers and evaluate.
    
    Args:
        version: "v1" or "v2"
    
    Returns:
        Evaluation metrics
    """
    if version not in ["v1", "v2"]:
        raise HTTPException(status_code=400, detail="Version must be 'v1' or 'v2'")
    
    # Load gold labels
    from .data_loader import GoldLabels
    gold_labels = GoldLabels('development_gold.csv')
    
    # Initialize agent and evaluator
    if version == "v1":
        agent = ClaimExtractionAgentV1(brand_facts)
    else:
        agent = ClaimExtractionAgentV2(brand_facts)
    
    evaluator = Evaluator()
    
    # Get development answers
    dev_answers = answers_data.get_development_answers()
    
    # Process all answers
    run_id = str(uuid.uuid4())
    all_predictions = {}
    all_results = []
    
    for answer_id, answer_data in dev_answers:
        model_id = extract_model_id(answer_data['question'], answer_data['brand_id'])
        
        predictions = agent.process_answer(
            answer_id,
            answer_data['ai_answer'],
            answer_data['brand_id'],
            model_id
        )
        
        all_predictions[answer_id] = predictions
        
        # Store in database
        db_answer = Answer(
            id=str(uuid.uuid4()),
            run_id=run_id,
            answer_id=answer_id,
            brand_id=answer_data['brand_id'],
            model_id=model_id,
            text=answer_data['ai_answer']
        )
        db.add(db_answer)
        
        for pred in predictions:
            db_pred = Prediction(
                id=str(uuid.uuid4()),
                run_id=run_id,
                answer_id=answer_id,
                start_char=pred['start_char'],
                end_char=pred['end_char'],
                quote=pred['quote'],
                classification=pred['classification']
            )
            db.add(db_pred)
        
        # Evaluate
        gold = gold_labels.get_labels(answer_id)
        results = evaluator.evaluate(predictions, gold)
        all_results.append({
            'answer_id': answer_id,
            'metrics': results
        })
    
    # Calculate aggregate metrics
    total_tp = sum(r['metrics']['extraction']['true_positives'] for r in all_results)
    total_fp = sum(r['metrics']['extraction']['false_positives'] for r in all_results)
    total_fn = sum(r['metrics']['extraction']['false_negatives'] for r in all_results)
    
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # Store run record
    db_run = Run(
        id=run_id,
        version=version,
        timestamp=datetime.utcnow(),
        total_answers=len(dev_answers),
        extraction_f1=f1,
        classification_macro_f1=0.0,  # Will calculate if needed
        combined_f1=0.0
    )
    db.add(db_run)
    db.commit()
    
    return {
        "run_id": run_id,
        "version": version,
        "aggregate_metrics": {
            "extraction": {
                "true_positives": total_tp,
                "false_positives": total_fp,
                "false_negatives": total_fn,
                "precision": precision,
                "recall": recall,
                "f1": f1
            }
        },
        "per_answer_results": all_results
    }


@app.get("/runs")
async def list_runs(db: Session = Depends(get_db)):
    """List all runs."""
    runs = db.query(Run).order_by(Run.timestamp.desc()).all()
    return runs


@app.get("/runs/{run_id}")
async def get_run(run_id: str, db: Session = Depends(get_db)):
    """Get details of a specific run."""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    predictions = db.query(Prediction).filter(Prediction.run_id == run_id).all()
    answers = db.query(Answer).filter(Answer.run_id == run_id).all()
    
    return {
        "run": run,
        "answers": answers,
        "predictions": predictions
    }
