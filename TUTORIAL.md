# Kasparo Claim Extraction System - User Tutorial

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Running the Agents](#running-the-agents)
6. [Using the FastAPI Service](#using-the-fastapi-service)
7. [Understanding the Results](#understanding-the-results)
8. [Common Use Cases](#common-use-cases)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Usage](#advanced-usage)

---

## Overview

The Kasparo Claim Extraction System is designed to:
- Extract factual claims from AI-generated answers about speaker products
- Classify each claim as **supported**, **contradicted**, or **unknown**
- Use a brand facts catalogue for evidence-based classification
- Provide evaluation metrics for performance measurement

### System Components
- **V1 Agent**: Baseline rule-based agent
- **V2 Agent**: Improved rule-based agent with better classification
- **Evaluation Harness**: Scoring system for extraction and classification
- **FastAPI Service**: REST API for interactive use
- **PostgreSQL Database**: Storage for runs, answers, and predictions

---

## Prerequisites

### Required Software
- Python 3.8 or higher
- pip (Python package manager)
- PostgreSQL 16 (optional, for database features)
- Docker (optional, for running PostgreSQL)

### Required Python Packages
All packages are listed in `requirements.txt`:
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
google-generativeai==0.3.2
pandas==2.1.3
python-dotenv==1.0.0
langfuse==2.9.0
scikit-learn==1.3.2
tenacity==8.2.3
```

---

## Installation

### Step 1: Clone or Download the Repository
```bash
cd /path/to/your/workspace
# If using git
git clone <repository-url>
cd Kasparo
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Set Up PostgreSQL (Optional but Recommended)

#### Option A: Using Docker (Recommended)
```bash
# Navigate to your docker-compose directory
cd ~/docker/pgsql

# Start PostgreSQL container
docker-compose up -d

# Verify it's running
docker ps
```

#### Option B: Using Local PostgreSQL
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib  # Ubuntu/Debian
# or
brew install postgresql  # macOS

# Start PostgreSQL service
sudo service postgresql start

# Create database
sudo -u postgres psql
CREATE DATABASE app;
CREATE USER admin WITH PASSWORD 'admin@123';
GRANT ALL PRIVILEGES ON DATABASE app TO admin;
\q
```

### Step 4: Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your values
# Required for PostgreSQL:
# DATABASE_URL=postgresql://admin:admin%40123@localhost:5432/app
# 
# Optional for LLM-based agents:
# GEMINI_API_KEY=your_key_here
```

### Step 5: Verify Installation
```bash
python3 -c "from src.data_loader import BrandFacts; print('✓ Installation successful')"
```

---

## Quick Start

### Run V1 on Development Set
```bash
python3 run_v1.py
```

**Expected Output:**
```
Loading data...
Initializing V1 agent...
Found 40 development answers

Processing A01...
  Brand: cleartrail, Model: mini
  Extracted 8 claims
  Extraction F1: 0.857
  Classification Macro F1: 0.083
  Overall Combined F1: 0.470
...
```

### Run V2 on Development Set
```bash
python3 run_v2.py
```

### Generate Test Predictions
```bash
python3 run_test_predictions.py
```

---

## Running the Agents

### Using Python Scripts

#### 1. Single Answer Processing
```python
from src.data_loader import BrandFacts, Answers
from src.agent_v2 import ClaimExtractionAgentV2
from src.utils import extract_model_id

# Load data
brand_facts = BrandFacts('brand_facts.csv')
answers = Answers('answers.csv')

# Initialize agent
agent = ClaimExtractionAgentV2(brand_facts)

# Get an answer
answer_data = answers.get_answer('A01')
model_id = extract_model_id(answer_data['question'], answer_data['brand_id'])

# Process
predictions = agent.process_answer(
    answer_id='A01',
    answer_text=answer_data['ai_answer'],
    brand_id=answer_data['brand_id'],
    model_id=model_id
)

# View results
for pred in predictions:
    print(f"Claim: {pred['quote']}")
    print(f"Classification: {pred['classification']}")
    print(f"Position: {pred['start_char']}-{pred['end_char']}")
    print("-" * 80)
```

#### 2. Batch Processing
```python
from src.data_loader import BrandFacts, Answers
from src.agent_v2 import ClaimExtractionAgentV2
from src.utils import extract_model_id

brand_facts = BrandFacts('brand_facts.csv')
answers = Answers('answers.csv')
agent = ClaimExtractionAgentV2(brand_facts)

# Get all development answers
dev_answers = answers.get_development_answers()

for answer_id, answer_data in dev_answers:
    model_id = extract_model_id(answer_data['question'], answer_data['brand_id'])
    predictions = agent.process_answer(
        answer_id,
        answer_data['ai_answer'],
        answer_data['brand_id'],
        model_id
    )
    print(f"{answer_id}: {len(predictions)} claims extracted")
```

#### 3. With Evaluation
```python
from src.data_loader import BrandFacts, Answers, GoldLabels
from src.agent_v2 import ClaimExtractionAgentV2
from src.evaluator import Evaluator
from src.utils import extract_model_id

brand_facts = BrandFacts('brand_facts.csv')
answers = Answers('answers.csv')
gold_labels = GoldLabels('development_gold.csv')
agent = ClaimExtractionAgentV2(brand_facts)
evaluator = Evaluator()

answer_id = 'A01'
answer_data = answers.get_answer(answer_id)
model_id = extract_model_id(answer_data['question'], answer_data['brand_id'])

# Process
predictions = agent.process_answer(
    answer_id,
    answer_data['ai_answer'],
    answer_data['brand_id'],
    model_id
)

# Evaluate
gold = gold_labels.get_labels(answer_id)
results = evaluator.evaluate(predictions, gold)

print(f"Extraction F1: {results['extraction']['f1']:.3f}")
print(f"Classification Macro F1: {results['classification']['macro_f1']:.3f}")
```

---

## Using the FastAPI Service

### Starting the Service

```bash
# Start the service
uvicorn src.api:app --reload

# Or specify host and port
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### API Endpoints

#### 1. Root Endpoint
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "message": "Kasparo Claim Extraction API",
  "versions": ["v1", "v2"]
}
```

#### 2. Process Single Answer
```bash
# Using V1
curl -X POST "http://localhost:8000/run/v1?answer_id=A01"

# Using V2
curl -X POST "http://localhost:8000/run/v2?answer_id=A01"
```

**Response:**
```json
{
  "run_id": "5b5c04d3-f917-4c94-b55a-c8f618219689",
  "answer_id": "A01",
  "predictions": [
    {
      "start_char": 306,
      "end_char": 460,
      "quote": "For the current India catalogue, ClearTrail Mini is listed at INR 1,200 less than ClearTrail Plus...",
      "classification": "unknown",
      "answer_id": "A01"
    }
  ]
}
```

#### 3. Evaluate on Development Set
```bash
# Using V1
curl -X POST http://localhost:8000/evaluate/v1

# Using V2
curl -X POST http://localhost:8000/evaluate/v2
```

**Response:**
```json
{
  "run_id": "xxx-xxx-xxx",
  "version": "v2",
  "aggregate_metrics": {
    "extraction": {
      "true_positives": 376,
      "false_positives": 43,
      "false_negatives": 44,
      "precision": 0.897,
      "recall": 0.895,
      "f1": 0.896
    }
  },
  "per_answer_results": [...]
}
```

#### 4. List All Runs
```bash
curl http://localhost:8000/runs
```

#### 5. Get Specific Run Details
```bash
curl http://localhost:8000/runs/{run_id}
```

### Using with Python Requests

```python
import requests

# Process single answer
response = requests.post(
    "http://localhost:8000/run/v2",
    params={"answer_id": "A01"}
)
data = response.json()
print(f"Run ID: {data['run_id']}")
print(f"Claims extracted: {len(data['predictions'])}")

# Evaluate on development set
response = requests.post("http://localhost:8000/evaluate/v2")
data = response.json()
print(f"Extraction F1: {data['aggregate_metrics']['extraction']['f1']}")
```

---

## Understanding the Results

### Prediction Format

Each prediction contains:
- `answer_id`: ID of the answer
- `start_char`: Start position in the original text
- `end_char`: End position in the original text
- `quote`: The exact extracted claim text
- `classification`: One of "supported", "contradicted", or "unknown"

### Classification Labels

- **supported**: The claim is directly supported by the brand facts
- **contradicted**: The claim directly contradicts the brand facts
- **unknown**: The facts don't provide enough information to determine

### Evaluation Metrics

#### Extraction Metrics
- **True Positives**: Correctly extracted claims
- **False Positives**: Incorrectly extracted claims (not in gold standard)
- **False Negatives**: Missed claims (in gold standard but not extracted)
- **Precision**: TP / (TP + FP) - How many extracted claims are correct
- **Recall**: TP / (TP + FN) - How many gold claims were found
- **F1**: Harmonic mean of precision and recall

#### Classification Metrics
- **Accuracy**: Percentage of correctly classified claims
- **Macro F1**: Average F1 across all three classes (supported/contradicted/unknown)
- **Combined F1**: Average of extraction F1 and classification macro F1

### Result Files

#### CSV Format
```csv
answer_id,start_char,end_char,quote,classification
A01,306,460,"For the current India catalogue...",unknown
A01,461,647,"For an authorized India purchase...",contradicted
```

#### JSON Format
```json
{
  "A01": [
    {
      "start_char": 306,
      "end_char": 460,
      "quote": "For the current India catalogue...",
      "classification": "unknown",
      "answer_id": "A01"
    }
  ]
}
```

---

## Common Use Cases

### Use Case 1: Evaluate a New Answer

**Scenario**: You have a new AI answer and want to extract and classify claims.

```python
from src.data_loader import BrandFacts
from src.agent_v2 import ClaimExtractionAgentV2

# Load brand facts
brand_facts = BrandFacts('brand_facts.csv')
agent = ClaimExtractionAgentV2(brand_facts)

# Your new answer
new_answer = """
The ClearTrail Mini costs INR 1,299 including tax.
It has a battery life of 12 hours at 50% volume.
The Wi-Fi capability is absent.
"""

# Process
predictions = agent.process_answer(
    answer_id="NEW001",
    answer_text=new_answer,
    brand_id="cleartrail",
    model_id="mini"
)

# View results
for pred in predictions:
    print(f"{pred['classification']}: {pred['quote']}")
```

### Use Case 2: Compare V1 vs V2 Performance

```python
from src.data_loader import BrandFacts, Answers, GoldLabels
from src.agent_v1_rulebased import ClaimExtractionAgentV1
from src.agent_v2 import ClaimExtractionAgentV2
from src.evaluator import Evaluator
from src.utils import extract_model_id

brand_facts = BrandFacts('brand_facts.csv')
answers = Answers('answers.csv')
gold_labels = GoldLabels('development_gold.csv')
evaluator = Evaluator()

# Initialize both agents
agent_v1 = ClaimExtractionAgentV1(brand_facts)
agent_v2 = ClaimExtractionAgentV2(brand_facts)

# Test on a specific answer
answer_id = 'A01'
answer_data = answers.get_answer(answer_id)
model_id = extract_model_id(answer_data['question'], answer_data['brand_id'])
gold = gold_labels.get_labels(answer_id)

# V1
preds_v1 = agent_v1.process_answer(answer_id, answer_data['ai_answer'], answer_data['brand_id'], model_id)
results_v1 = evaluator.evaluate(preds_v1, gold)

# V2
preds_v2 = agent_v2.process_answer(answer_id, answer_data['ai_answer'], answer_data['brand_id'], model_id)
results_v2 = evaluator.evaluate(preds_v2, gold)

# Compare
print(f"V1 Extraction F1: {results_v1['extraction']['f1']:.3f}")
print(f"V2 Extraction F1: {results_v2['extraction']['f1']:.3f}")
print(f"V1 Classification F1: {results_v1['classification']['macro_f1']:.3f}")
print(f"V2 Classification F1: {results_v2['classification']['macro_f1']:.3f}")
```

### Use Case 3: Batch Process Custom Answers

```python
import csv
from src.data_loader import BrandFacts
from src.agent_v2 import ClaimExtractionAgentV2

brand_facts = BrandFacts('brand_facts.csv')
agent = ClaimExtractionAgentV2(brand_facts)

# Read custom answers from CSV
with open('my_answers.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        predictions = agent.process_answer(
            answer_id=row['id'],
            answer_text=row['text'],
            brand_id=row['brand'],
            model_id=row['model']
        )
        
        # Save results
        with open(f'results_{row["id"]}.json', 'w') as out:
            json.dump(predictions, out, indent=2)
```

### Use Case 4: Monitor API Performance via Database

```python
from src.database import SessionLocal, Run

db = SessionLocal()
runs = db.query(Run).order_by(Run.timestamp.desc()).limit(10).all()

for run in runs:
    print(f"Run {run.id}: {run.version}")
    print(f"  Extraction F1: {run.extraction_f1}")
    print(f"  Combined F1: {run.combined_f1}")
    print(f"  Timestamp: {run.timestamp}")

db.close()
```

---

## Troubleshooting

### Issue 1: PostgreSQL Connection Failed

**Error:**
```
psycopg2.OperationalError: connection to server at "localhost" failed
```

**Solution:**
1. Check if PostgreSQL is running:
   ```bash
   docker ps  # If using Docker
   sudo service postgresql status  # If using local
   ```

2. Start PostgreSQL:
   ```bash
   docker-compose up -d  # Docker
   sudo service postgresql start  # Local
   ```

3. Verify connection string in `src/database.py` matches your setup

### Issue 2: Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'src'
```

**Solution:**
```bash
# Run from the project root directory
cd /path/to/Kasparo
python3 run_v1.py  # NOT python3 src/run_v1.py
```

### Issue 3: API Returns 404

**Error:**
```
404 Not Found
```

**Solution:**
- Ensure the API service is running
- Check the URL is correct (include http://)
- Verify the answer_id exists in answers.csv

### Issue 4: Zero Claims Extracted

**Problem**: Agent extracts 0 claims from an answer

**Possible Causes:**
1. Answer doesn't contain factual claims
2. All sentences match ignore patterns
3. Model_id extraction failed

**Solution:**
```python
# Debug: Check what model_id was extracted
from src.utils import extract_model_id
answer_data = answers.get_answer('A01')
model_id = extract_model_id(answer_data['question'], answer_data['brand_id'])
print(f"Extracted model_id: {model_id}")
```

### Issue 5: All Claims Classified as "unknown"

**Problem**: Classification accuracy is very low

**Possible Causes:**
1. Facts not available for the model
2. Claim mentions fields not in catalogue
3. Complex conditions not handled by rule-based approach

**Solution:**
- Check if facts exist for the model in brand_facts.csv
- Consider using V2 for better classification
- For complex claims, LLM-based classification may be needed

---

## Advanced Usage

### Custom Claim Extraction Patterns

Edit the patterns in `src/agent_v2.py`:

```python
# Add new claim patterns
claim_patterns = [
    r'\b(costs?|price|inr|₹)\b',
    r'\b(hours?|minutes?|battery|playback)\b',
    # Add your custom pattern
    r'\b(your_custom_keyword)\b',
]
```

### Custom Ignore Patterns

```python
ignore_patterns = [
    r'^Keep the exact model',
    # Add your custom ignore pattern
    r'^Your custom pattern',
]
```

### Database Queries

```python
from src.database import SessionLocal, Run, Answer, Prediction

db = SessionLocal()

# Get all runs with high extraction F1
high_perf_runs = db.query(Run).filter(Run.extraction_f1 > 0.9).all()

# Get predictions for a specific answer
predictions = db.query(Prediction).filter(Prediction.answer_id == 'A01').all()

# Get all predictions classified as 'contradicted'
contradictions = db.query(Prediction).filter(
    Prediction.classification == 'contradicted'
).all()

db.close()
```

### Using the Enhanced Agent with Langfuse

```python
from langfuse import Langfuse
from src.agent_v2_enhanced import ClaimExtractionAgentV2Enhanced
from src.data_loader import BrandFacts

# Initialize Langfuse (requires LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)
langfuse = Langfuse()

# Initialize enhanced agent
brand_facts = BrandFacts('brand_facts.csv')
agent = ClaimExtractionAgentV2Enhanced(brand_facts, langfuse_client=langfuse)

# Process with tracing
predictions = agent.process_answer(
    answer_id='A01',
    answer_text=answer_text,
    brand_id='cleartrail',
    model_id='mini'
)

# View traces in Langfuse dashboard
```

### Async Processing

```python
import asyncio
from src.agent_v2_enhanced import ClaimExtractionAgentV2Enhanced

async def process_multiple():
    agent = ClaimExtractionAgentV2Enhanced(brand_facts)
    
    # Process multiple answers concurrently
    tasks = [
        agent.process_answer_async(
            answer_id,
            answer_data['ai_answer'],
            answer_data['brand_id'],
            model_id
        )
        for answer_id, answer_data in dev_answers[:5]
    ]
    
    results = await asyncio.gather(*tasks)
    return results

# Run
results = asyncio.run(process_multiple())
```

---

## Best Practices

1. **Always use V2** for better classification accuracy
2. **Use the API** for interactive or production use
3. **Save results** after each run for comparison
4. **Check model_id extraction** if getting unexpected results
5. **Use PostgreSQL** for persistent storage and historical comparison
6. **Review the gold labels** to understand expected output format
7. **Test on a small sample** before batch processing
8. **Monitor database size** if processing many answers
9. **Keep API keys secure** in .env file (not in code)
10. **Use version control** to track changes to agents

---

## Support and Documentation

- **README.md**: Project overview and architecture
- **COMPARISON.md**: Detailed V1 vs V2 comparison
- **SUBMISSION.md**: Assessment submission details
- **requirements.txt**: Python dependencies
- **.env.example**: Environment variable template

---

## Summary

This tutorial covers:
- ✅ Installation and setup
- ✅ Running agents (V1 and V2)
- ✅ Using the FastAPI service
- ✅ Understanding results
- ✅ Common use cases
- ✅ Troubleshooting
- ✅ Advanced usage

For questions or issues, refer to the documentation files or check the code comments in the source files.
