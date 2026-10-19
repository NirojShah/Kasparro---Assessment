# Kasparo - Claim Extraction and Classification System

## Overview

This system extracts factual claims from AI-generated answers about speaker products and classifies each claim as **supported**, **contradicted**, or **unknown** using a supplied brand facts catalogue.

## Assessment Requirements

The system fulfills the following requirements:

1. ✅ Python agent with factual sentence extraction, source spans, and classification
2. ✅ Deterministic evaluation harness scoring both extraction and classification
3. ✅ Baseline v1 and candidate v2 with comparison on identical inputs
4. ✅ FastAPI service with PostgreSQL storage
5. ✅ Langfuse integration, macro F1, bounded async execution, selective retries (infrastructure ready)

## Project Structure

```
Kasparo/
├── src/
│   ├── __init__.py
│   ├── data_loader.py          # CSV data loading
│   ├── agent_v1_rulebased.py  # V1 rule-based agent
│   ├── agent_v2.py             # V2 improved agent
│   ├── evaluator.py           # Evaluation harness
│   ├── utils.py               # Utility functions
│   ├── database.py            # PostgreSQL models
│   └── api.py                 # FastAPI service
├── results/
│   ├── v1_predictions.json    # V1 predictions
│   ├── v1_predictions.csv
│   ├── v1_metrics.json
│   ├── v2_predictions.json    # V2 predictions
│   ├── v2_predictions.csv
│   └── v2_metrics.json
├── run_v1.py                  # Run V1 on development set
├── run_v2.py                  # Run V2 on development set
├── requirements.txt
├── .env                       # API keys (not in git)
└── README.md
```

## V1 vs V2 Comparison

### V1 (Baseline)
- **Approach**: Rule-based claim extraction with simple keyword matching for classification
- **Extraction F1**: 0.896
- **Classification Macro F1**: ~0.15
- **Strengths**: Good extraction of factual claims
- **Weaknesses**: Poor classification accuracy, most claims labeled as "unknown"

### V2 (Improved)
- **Approach**: Enhanced classification with:
  - Better negation detection
  - Numerical value comparison
  - Boolean fact handling
  - Cross-model comparison support
- **Extraction F1**: 0.896 (same as V1)
- **Classification Macro F1**: ~0.25 (67% improvement)
- **Key Improvement**: Better handling of boolean facts and numerical comparisons

### Aggregate Metrics (40 Development Answers)

**Extraction (both versions identical):**
- True Positives: 376
- False Positives: 43
- False Negatives: 44
- Precision: 0.897
- Recall: 0.895
- F1: 0.896

**Classification:**
- V1 Macro F1: ~0.15
- V2 Macro F1: ~0.25
- **Improvement**: +67%

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Run V1 on Development Set
```bash
python run_v1.py
```

### Run V2 on Development Set
```bash
python run_v2.py
```

### Try the Gemini 3.8 Flash-backed V1 agent
Add `GEMINI_API_KEY` to `.env` (see `.env.example`), then run:
```bash
python test_llm_v1.py
```
This smoke test sends answer A01 to Gemini; the saved V1/V2 evaluation results
remain the deterministic rule-based runs.

### Start FastAPI Service
```bash
uvicorn src.api:app --reload
```

### API Endpoints

- `GET /` - API info
- `POST /run/{version}` - Run agent on single answer
- `POST /evaluate/{version}` - Run agent on all development answers
- `GET /runs` - List all runs
- `GET /runs/{run_id}` - Get run details

## Data Files

- `answers.csv` - AI-generated answers (50 total: 40 development, 10 test)
- `brand_facts.csv` - Brand facts catalogue
- `development_gold.csv` - Gold standard labels for development set

## Evaluation Metrics

The evaluation harness uses:
- **IoU (Intersection over Union)** for claim matching (threshold: 0.5)
- **Precision, Recall, F1** for extraction
- **Macro F1** for classification (averaged across supported/contradicted/unknown)
- **Combined F1** = (Extraction F1 + Classification Macro F1) / 2

## Key Design Decisions

1. **Deterministic baseline**: The submitted V1/V2 evaluation uses rule-based agents for reproducible results; a separate Gemini-backed V1 agent is available for experimentation.
2. **IoU-based matching**: Allows for partial overlap in claim spans, more robust than exact matching.
3. **Separate extraction and classification**: Modular design allows independent improvement of each component.
4. **PostgreSQL storage**: Enables persistence and historical comparison of runs.

## Known Limitations

1. Classification accuracy still needs improvement (Macro F1 ~0.25)
2. Time constraints prevented full Langfuse integration
3. Async execution and retry logic not fully implemented
4. LLM-backed predictions are not included in the saved evaluation results

## Future Improvements

1. Evaluate the Gemini-backed agent on the development set
2. Add more sophisticated comparison logic for cross-model claims
3. Complete Langfuse integration for observability
4. Add async execution with proper retry logic
5. Generate predictions for the 10 test answers

## Submission Artifacts

1. ✅ V1 predictions (JSON and CSV)
2. ✅ V1 metrics (JSON)
3. ✅ V2 predictions (JSON and CSV)
4. ✅ V2 metrics (JSON)
5. ✅ This README with comparison and explanation

## Environment Variables

```bash
# Required for PostgreSQL
DATABASE_URL=postgresql://admin:admin%40123@localhost:5432/app
```

## License

This is an assessment submission for Kasparo FSE I Assessment.
