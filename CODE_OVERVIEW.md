# Kasparo System - Complete Code Overview

## Table of Contents
1. [High-Level Architecture](#high-level-architecture)
2. [File-by-File Breakdown](#file-by-file-breakdown)
3. [Data Flow Example](#data-flow-example)
4. [Key Algorithms](#key-algorithms)
5. [Metrics Explained](#metrics-explained)
6. [Quick Reference](#quick-reference)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    INPUT DATA                           │
│  answers.csv | brand_facts.csv | development_gold.csv │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              DATA LOADER (data_loader.py)              │
│  - Load CSV files into structured Python objects        │
│  - Provide access methods for answers, facts, gold     │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│   V1 AGENT       │    │   V2 AGENT       │
│ (agent_v1_*.py)  │    │ (agent_v2.py)    │
│                  │    │                  │
│ - Extract claims │    │ - Extract claims │
│ - Classify (simple)│   │ - Classify (improved)│
└────────┬─────────┘    └────────┬─────────┘
         │                        │
         └───────────┬────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│          EVALUATOR (evaluator.py)                       │
│  - Compare predictions vs gold labels                    │
│  - Calculate precision, recall, F1                        │
│  - Match claims using IoU (Intersection over Union)      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              RESULTS (results/)                          │
│  - JSON files with predictions                           │
│  - CSV files for easy viewing                           │
│  - Metrics JSON files                                   │
└─────────────────────────────────────────────────────────┘
```

---

## File-by-File Breakdown

### 1. data_loader.py - Data Loading

**Purpose**: Load CSV files into Python objects

**Classes and Methods:**

#### BrandFacts Class
```python
class BrandFacts:
    def __init__(facts_path):
        # Loads brand_facts.csv
        # Stores all product facts (price, specs, warranty, etc.)
        
    def get_fact(fact_id):
        # Get a specific fact by ID
        
    def get_facts_by_model(brand_id, model_id):
        # Get all facts for a specific model (e.g., cleartrail.mini)
        
    def get_facts_by_brand(brand_id):
        # Get all facts for a brand (e.g., all cleartrail models)
```

**Example Usage:**
```python
brand_facts = BrandFacts('brand_facts.csv')
facts = brand_facts.get_facts_by_model('cleartrail', 'mini')
# Returns list of facts like: price, battery, warranty, etc.
```

---

#### Answers Class
```python
class Answers:
    def __init__(answers_path):
        # Loads answers.csv
        # Stores all AI-generated answers
        
    def get_answer(answer_id):
        # Get a specific answer by ID (e.g., 'A01')
        
    def get_development_answers():
        # Get all 40 development answers
        
    def get_test_answers():
        # Get all 10 test answers
```

**Example Usage:**
```python
answers = Answers('answers.csv')
answer = answers.get_answer('A01')
# Returns: {split, brand_id, question, ai_answer}
```

---

#### GoldLabels Class
```python
class GoldLabels:
    def __init__(gold_path):
        # Loads development_gold.csv
        # Stores correct answers (ground truth)
        
    def get_labels(answer_id):
        # Get gold labels for a specific answer
```

**Example Usage:**
```python
gold = GoldLabels('development_gold.csv')
labels = gold.get_labels('A01')
# Returns list of: [{claim_id, start_char, end_char, quote, expected_label, ...}]
```

**Why Important**: This is the foundation - all other components depend on this data.

---

### 2. agent_v1_rulebased.py - V1 Agent (Baseline)

**Purpose**: Extract and classify claims using simple rules

**Key Methods:**

#### extract_claims(answer_text, brand_id, model_id)
```python
def extract_claims(answer_text, brand_id, model_id):
    # 1. Split text into sentences
    # 2. Check each sentence against claim_patterns:
    #    - price, battery, warranty, wifi, bluetooth, etc.
    # 3. Ignore sentences matching ignore_patterns:
    #    - Instructions like "Keep the exact model", "Ask whether"
    # 4. Return list of claims with start/end positions
```

**Claim Patterns:**
```python
claim_patterns = [
    r'\b(costs?|price|inr|₹)\b',      # Price-related
    r'\b(hours?|minutes?|battery)\b',   # Battery-related
    r'\b(warranty|month|year)\b',     # Warranty-related
    r'\b(includes?|adapter|cable)\b',  # Box contents
    r'\b(wifi|bluetooth|microphone)\b', # Features
    # ... more patterns
]
```

**Ignore Patterns:**
```python
ignore_patterns = [
    r'^Keep the exact model',
    r'^Ask whether',
    r'^Before choosing',
    # ... more instruction patterns
]
```

---

#### classify_claim(claim_text, brand_id, model_id)
```python
def classify_claim(claim_text, brand_id, model_id):
    # 1. Get facts for the model
    # 2. Check if claim mentions any fact field
    # 3. Simple string matching:
    #    - If fact_value in claim_text: return "supported"
    #    - Else: return "unknown"
    # 4. Very basic logic (most claims return "unknown")
```

**V1 Performance**: 
- Extraction F1: 0.896 (good)
- Classification Macro F1: ~0.15 (poor)

---

#### process_answer(answer_id, answer_text, brand_id, model_id)
```python
def process_answer(answer_id, answer_text, brand_id, model_id):
    # 1. Extract claims
    claims = extract_claims(answer_text, brand_id, model_id)
    
    # 2. Classify each claim
    for claim in claims:
        claim['classification'] = classify_claim(claim['quote'], brand_id, model_id)
        claim['answer_id'] = answer_id
    
    # 3. Return classified claims
    return claims
```

---

### 3. agent_v2.py - V2 Agent (Improved)

**Purpose**: Same extraction as V1, but better classification

**Key Methods:**

#### extract_claims()
- **Identical to V1** (no changes made)

---

#### classify_claim(claim_text, brand_id, model_id) - IMPROVED
```python
def classify_claim(claim_text, brand_id, model_id):
    # 1. Get facts for the model
    facts = get_facts_by_model(brand_id, model_id)
    
    # 2. Check for negation (not, no, never, does not)
    has_negation = bool(re.search(r'\b(not|no|never|does not)\b', claim_lower))
    
    # 3. Check each fact
    for fact in facts:
        # BOOLEAN FACTS
        if fact['value_type'] == 'boolean':
            if has_negation:
                if fact['value'] == 'false':
                    return 'supported'  # "not X" + fact=false = correct
                elif fact['value'] == 'true':
                    return 'contradicted'  # "not X" + fact=true = wrong
            else:
                if fact['value'] == 'true':
                    return 'supported'
                elif fact['value'] == 'false':
                    return 'contradicted'
        
        # NUMERICAL FACTS
        elif fact['value_type'] == 'number':
            claim_num = extract_number(claim_text)
            if claim_num is not None:
                fact_num = float(fact['value'])
                if abs(claim_num - fact_num) < 0.01:
                    return 'supported'  # Numbers match
                if abs(claim_num - fact_num) > fact_num * 0.5:
                    return 'contradicted'  # Numbers very different
        
        # STRING FACTS
        elif fact['value_type'] == 'string':
            if fact['value'] in claim_lower:
                return 'supported'
    
    # 4. Handle cross-model comparisons
    #    e.g., "Model A costs INR 1,200 less than Model B"
    #    - Extract both model names
    #    - Get both prices
    #    - Compare the difference
    
    # 5. Default to unknown if no match
    return 'unknown'
```

**V2 Performance:**
- Extraction F1: 0.896 (same as V1)
- Classification Macro F1: ~0.25 (67% improvement over V1)

**Key Improvement**: Better handling of negation, numbers, and boolean logic.

---

### 4. evaluator.py - Evaluation Harness

**Purpose**: Score how well the agent performed

**Key Methods:**

#### evaluate(predictions, gold_labels)
```python
def evaluate(predictions, gold_labels):
    # 1. Match predictions to gold labels using IoU
    matches = _match_claims(predictions, gold_labels)
    
    # 2. Calculate extraction metrics
    extraction_metrics = _calculate_extraction_metrics(predictions, gold_labels, matches)
    
    # 3. Calculate classification metrics
    classification_metrics = _calculate_classification_metrics(matches)
    
    # 4. Calculate overall combined F1
    overall_metrics = _calculate_overall_metrics(extraction_metrics, classification_metrics)
    
    return {
        'extraction': extraction_metrics,
        'classification': classification_metrics,
        'overall': overall_metrics,
        'matches': matches
    }
```

---

#### _match_claims(predictions, gold_labels)
```python
def _match_claims(predictions, gold_labels):
    # 1. Calculate IoU (Intersection over Union) for each pair
    for each prediction:
        for each gold label:
            iou = calculate_iou(pred_start, pred_end, gold_start, gold_end)
            
            # 2. If IoU >= 0.5 (50% overlap), it's a match
            if iou >= 0.5:
                mark as matched
    
    # 3. Return list of matches
    return matches
```

**IoU Calculation:**
```python
def _calculate_iou(pred_start, pred_end, gold_start, gold_end):
    intersection = max(0, min(pred_end, gold_end) - max(pred_start, gold_start))
    union = (pred_end - pred_start) + (gold_end - gold_start) - intersection
    
    if union == 0:
        return 0.0
    
    return intersection / union
```

**Example:**
- Prediction: chars 100-200 (length 100)
- Gold: chars 120-180 (length 60)
- Intersection: 60 (overlap from 120-180)
- Union: 100 + 60 - 60 = 100
- IoU: 60/100 = 0.6 (60% overlap) → **Match!**

---

#### _calculate_extraction_metrics()
```python
def _calculate_extraction_metrics(predictions, gold_labels, matches):
    true_positives = correctly matched claims
    false_positives = predictions not in gold (wrongly extracted)
    false_negatives = gold not in predictions (missed)
    
    precision = TP / (TP + FP)  # How many extracted are correct
    recall = TP / (TP + FN)      # How many gold were found
    f1 = 2 * (precision * recall) / (precision + recall)
    
    return {TP, FP, FN, precision, recall, f1}
```

---

#### _calculate_classification_metrics()
```python
def _calculate_classification_metrics(matches):
    # Only evaluate matched claims
    matched = [m for m in matches if both pred and gold exist]
    
    for each matched claim:
        if pred_label == gold_label:
            mark as correct
        else:
            mark as incorrect
    
    # Calculate per-class F1 (supported/contradicted/unknown)
    supported_f1 = 2 * (supported_precision * supported_recall) / (supported_precision + supported_recall)
    contradicted_f1 = ...
    unknown_f1 = ...
    
    # Macro F1 = average of all three
    macro_f1 = (supported_f1 + contradicted_f1 + unknown_f1) / 3
    
    return {accuracy, supported_f1, contradicted_f1, unknown_f1, macro_f1}
```

**Why Important**: Provides objective, deterministic scoring that can be compared across versions.

---

### 5. utils.py - Utility Functions

**Purpose**: Helper functions

#### extract_model_id(question, brand_id)
```python
def extract_model_id(question, brand_id):
    # 1. Check brand-specific model names
    if brand_id == 'cleartrail':
        models = ['mini', 'plus']
    elif brand_id == 'cloudnote':
        models = ['air', 'studio']
    elif brand_id == 'stonewave':
        models = ['go', 'max']
    
    # 2. Search question for model name
    for model in models:
        if model in question.lower():
            return model
    
    # 3. Fallback to first available model
    return models[0]
```

**Example:**
```python
question = "consider ClearTrail Mini for weekend packing"
brand_id = "cleartrail"
model_id = extract_model_id(question, brand_id)
# Returns: "mini"
```

---

### 6. database.py - PostgreSQL Models

**Purpose**: Database schema and connection

**Database Models:**

#### Run Model
```python
class Run(Base):
    __tablename__ = "runs"
    
    id = Column(String, primary_key)           # Unique run ID
    version = Column(String)                     # "v1" or "v2"
    timestamp = Column(DateTime)                 # When run was executed
    total_answers = Column(Integer)              # Number of answers processed
    extraction_f1 = Column(Float)                # Extraction F1 score
    classification_macro_f1 = Column(Float)     # Classification F1 score
    combined_f1 = Column(Float)                  # Overall F1 score
```

#### Answer Model
```python
class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(String, primary_key)
    run_id = Column(String)                      # Which run this belongs to
    answer_id = Column(String)                   # Original answer ID (A01, A02, etc.)
    brand_id = Column(String)
    model_id = Column(String)
    text = Column(Text)                          # Full answer text
    timestamp = Column(DateTime)
```

#### Prediction Model
```python
class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(String, primary_key)
    run_id = Column(String)                      # Which run this belongs to
    answer_id = Column(String)
    start_char = Column(Integer)                 # Start position in text
    end_char = Column(Integer)                   # End position in text
    quote = Column(Text)                         # Extracted claim text
    classification = Column(String)               # "supported"/"contradicted"/"unknown"
    timestamp = Column(DateTime)
```

**Database Functions:**
```python
def create_tables():
    # Creates all tables in PostgreSQL
    Base.metadata.create_all(bind=engine)

def get_db():
    # Database session generator
    # Used by FastAPI for database operations
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Why Important**: Enables persistence and historical comparison of runs.

---

### 7. api.py - FastAPI Service

**Purpose**: REST API for interactive use

**Key Endpoints:**

#### GET /
```python
@app.get("/")
async def root():
    return {
        "message": "Kasparo Claim Extraction API",
        "versions": ["v1", "v2"]
    }
```

#### POST /run/{version}?answer_id=X
```python
@app.post("/run/{version}")
async def run_agent(version: str, answer_id: str, db: Session):
    # 1. Validate version (v1 or v2)
    # 2. Get answer from answers.csv
    # 3. Initialize appropriate agent
    # 4. Extract model_id
    # 5. Process answer (extract + classify)
    # 6. Store in database (Answer + Prediction records)
    # 7. Return predictions
    
    return {
        "run_id": "uuid",
        "answer_id": "A01",
        "predictions": [...]
    }
```

#### POST /evaluate/{version}
```python
@app.post("/evaluate/{version}")
async def evaluate_agent(version: str, db: Session):
    # 1. Initialize agent and evaluator
    # 2. Process all 40 development answers
    # 3. Evaluate each against gold labels
    # 4. Store everything in database
    # 5. Calculate aggregate metrics
    # 6. Store Run record
    # 7. Return metrics
    
    return {
        "run_id": "uuid",
        "version": "v2",
        "aggregate_metrics": {...},
        "per_answer_results": [...]
    }
```

#### GET /runs
```python
@app.get("/runs")
async def list_runs(db: Session):
    # Return all runs from database
    runs = db.query(Run).order_by(Run.timestamp.desc()).all()
    return runs
```

#### GET /runs/{run_id}
```python
@app.get("/runs/{run_id}")
async def get_run(run_id: str, db: Session):
    # Return specific run with all answers and predictions
    run = db.query(Run).filter(Run.id == run_id).first()
    predictions = db.query(Prediction).filter(Prediction.run_id == run_id).all()
    answers = db.query(Answer).filter(Answer.run_id == run_id).all()
    
    return {"run": run, "answers": answers, "predictions": predictions}
```

**Startup Event:**
```python
@app.on_event("startup")
async def startup_event():
    # 1. Try to create database tables (fails gracefully if no PostgreSQL)
    try:
        create_tables()
    except Exception as e:
        print("PostgreSQL not available, continuing without database")
    
    # 2. Load brand facts and answers into memory
    global brand_facts, answers_data
    brand_facts = BrandFacts('brand_facts.csv')
    answers_data = Answers('answers.csv')
```

**Why Important**: Enables real-time interaction and database storage.

---

### 8. agent_v2_enhanced.py - V2 with Observability

**Purpose**: V2 + Langfuse + Async + Retries

**Key Additions:**

#### Langfuse Integration
```python
from langfuse import Langfuse

class ClaimExtractionAgentV2Enhanced:
    def __init__(self, brand_facts, langfuse_client):
        self.langfuse = langfuse_client or Langfuse()
```

#### Async Execution
```python
async def process_answer_async(answer_id, answer_text, brand_id, model_id):
    # Create Langfuse trace
    trace = self.langfuse.trace(name="claim_extraction", input={...})
    
    # Extract claims with retry
    claims = await asyncio.to_thread(self.extract_claims, ...)
    
    # Classify each claim with retry
    for claim in claims:
        classification = await asyncio.to_thread(self.classify_claim, ...)
    
    # End trace
    trace.end(output={...})
    
    return claims
```

#### Retry Logic
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def extract_claims(...):
    # Will retry up to 3 times with exponential backoff if it fails
```

**Why Important**: Production-ready features (not used in basic runs, but infrastructure is there).

---

## Main Script Files

### run_v1.py - Run V1 on Development Set

**Complete Flow:**
```python
def main():
    # 1. Load data
    brand_facts = BrandFacts('brand_facts.csv')
    answers = Answers('answers.csv')
    gold_labels = GoldLabels('development_gold.csv')
    
    # 2. Initialize V1 agent
    agent = ClaimExtractionAgentV1(brand_facts)
    
    # 3. Initialize evaluator
    evaluator = Evaluator()
    
    # 4. Get 40 development answers
    dev_answers = answers.get_development_answers()
    
    # 5. Process each answer
    for answer_id, answer_data in dev_answers:
        # Extract model_id from question
        model_id = extract_model_id(question, brand_id)
        
        # Process answer
        predictions = agent.process_answer(answer_id, answer_text, brand_id, model_id)
        
        # Get gold labels
        gold = gold_labels.get_labels(answer_id)
        
        # Evaluate
        results = evaluator.evaluate(predictions, gold)
        
        # Print metrics
        print(f"Extraction F1: {results['extraction']['f1']}")
        print(f"Classification Macro F1: {results['classification']['macro_f1']}")
    
    # 6. Calculate aggregate metrics
    total_tp = sum of all true_positives
    total_fp = sum of all false_positives
    total_fn = sum of all false_negatives
    overall_precision = total_tp / (total_tp + total_fp)
    overall_recall = total_tp / (total_tp + total_fn)
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall)
    
    # 7. Save results
    with open('results/v1_predictions.json', 'w') as f:
        json.dump(all_predictions, f)
    
    with open('results/v1_predictions.csv', 'w') as f:
        csv_writer.writerows(predictions)
    
    with open('results/v1_metrics.json', 'w') as f:
        json.dump(aggregate_metrics, f)
```

**Output Files:**
- `results/v1_predictions.json` - All predictions in JSON format
- `results/v1_predictions.csv` - All predictions in CSV format
- `results/v1_metrics.json` - Aggregate metrics

---

### run_v2.py - Run V2 on Development Set

**Flow**: Identical to run_v1.py, but uses `ClaimExtractionAgentV2` instead of V1.

**Output Files:**
- `results/v2_predictions.json`
- `results/v2_predictions.csv`
- `results/v2_metrics.json`

---

### run_test_predictions.py - Generate Test Predictions

**Complete Flow:**
```python
def main():
    # 1. Load data
    brand_facts = BrandFacts('brand_facts.csv')
    answers = Answers('answers.csv')
    
    # 2. Get 10 test answers
    test_answers = answers.get_test_answers()
    
    # 3. Run V1 on test set
    agent_v1 = ClaimExtractionAgentV1(brand_facts)
    for answer_id, answer_data in test_answers:
        predictions = agent_v1.process_answer(...)
        v1_predictions[answer_id] = predictions
    
    # 4. Run V2 on test set
    agent_v2 = ClaimExtractionAgentV2(brand_facts)
    for answer_id, answer_data in test_answers:
        predictions = agent_v2.process_answer(...)
        v2_predictions[answer_id] = predictions
    
    # 5. Save test predictions
    # v1_test_predictions.json/csv
    # v2_test_predictions.json/csv
```

**Output Files:**
- `results/v1_test_predictions.json`
- `results/v1_test_predictions.csv`
- `results/v2_test_predictions.json`
- `results/v2_test_predictions.csv`

---

## Data Flow Example

### Processing Answer A01

```
Step 1: Data Loading
├─ Load A01 from answers.csv
│  └─ Text: "Start with the exact model name before deciding..."
├─ Load ClearTrail Mini facts from brand_facts.csv
│  ├─ cleartrail.mini.price_2026: 1299
│  ├─ cleartrail.mini.battery_50_percent: 12
│  ├─ cleartrail.mini.warranty_india: 12
│  └─ ... (more facts)
└─ Load gold labels for A01 from development_gold.csv
   └─ 10 claims with expected classifications

Step 2: Model ID Extraction
├─ Question: "consider ClearTrail Mini for weekend packing"
├─ Brand: cleartrail
└─ utils.extract_model_id() returns: "mini"

Step 3: Claim Extraction
├─ Split text into sentences
├─ For each sentence:
│  ├─ Check if matches claim_patterns (price, battery, etc.)
│  ├─ Check if matches ignore_patterns (instructions)
│  └─ If factual claim → extract
└─ Result: 8 claims extracted
   ├─ Claim 1: "For the current India catalogue, ClearTrail Mini is listed at INR 1,200 less..."
   ├─ Claim 2: "For an authorized India purchase... warranty lasting 18 months..."
   └─ ... (6 more claims)

Step 4: Claim Classification (V2)
├─ For each claim:
│  ├─ Claim: "ClearTrail Mini costs INR 1,299 including tax..."
│  ├─ Check for negation: No
│  ├─ Check fact field: "price_2026"
│  ├─ Extract number: 1299
│  ├─ Compare with fact: 1299
│  ├─ Match! → Classification: "supported"
│  │
│  ├─ Claim: "Wi-Fi capability is absent"
│  ├─ Check for negation: Yes ("absent")
│  ├─ Check fact field: "wifi"
│  ├─ Fact value: false
│  ├─ Logic: "absent" + fact=false = correct
│  └─ Classification: "supported"
│
└─ Result: 8 classifications

Step 5: Evaluation
├─ Match 8 predictions to 10 gold labels
├─ Calculate IoU for each pair
│  ├─ Prediction 1 (chars 306-460) vs Gold 1 (chars 306-460)
│  │  └─ IoU: 1.0 (exact match) → Match!
│  ├─ Prediction 2 (chars 461-647) vs Gold 2 (chars 461-647)
│  │  └─ IoU: 1.0 (exact match) → Match!
│  └─ ... (6 more matches)
├─ Calculate metrics:
│  ├─ True Positives: 8 (correctly extracted)
│  ├─ False Positives: 0 (no wrong extractions)
│  ├─ False Negatives: 2 (missed 2 gold claims)
│  ├─ Precision: 8 / (8 + 0) = 1.0
│  ├─ Recall: 8 / (8 + 2) = 0.8
│  └─ F1: 2 * (1.0 * 0.8) / (1.0 + 0.8) = 0.889
└─ Result: Extraction F1: 0.889

Step 6: Save Results
├─ results/v1_predictions.json
├─ results/v1_predictions.csv
└─ results/v1_metrics.json
```

---

## Key Algorithms

### Algorithm 1: Claim Extraction (Rule-Based)

```python
INPUT: answer_text, brand_id, model_id
OUTPUT: list of claims

ALGORITHM:
1. Split answer_text into sentences using punctuation (., !, ?)
2. Initialize empty claims list
3. For each sentence:
   a. Check if sentence matches any ignore_pattern
      - If yes → skip (it's an instruction)
   b. Check if sentence matches any claim_pattern
      - If yes → extract the sentence
         - Record start_char (position in original text)
         - Record end_char (position in original text)
         - Add to claims list
4. Return claims list

CLAIM_PATTERNS:
- price, costs, INR, ₹
- hours, minutes, battery, playback
- warranty, month, year
- includes, contains, adapter, cable
- wifi, bluetooth, microphone
- weight, grams, kilograms
- water, immersion, IPX
- supported, contradicted
- listed, less, more, compare

IGNORE_PATTERNS:
- Keep the exact model
- Ask whether
- Before choosing
- For a practical decision
- When making the final choice
- After reading
- A useful shortlist
- etc.
```

---

### Algorithm 2: Claim Matching (IoU-Based)

```python
INPUT: predictions list, gold_labels list
OUTPUT: list of matches

ALGORITHM:
1. Initialize empty matches list
2. Initialize used_gold set, used_pred set
3. For each prediction:
   a. Find best matching gold label
      - Calculate IoU with every gold label
      - Keep the one with highest IoU
   b. If best IoU >= 0.5 (50% threshold):
      - Mark as matched
      - Add to matches list
      - Mark gold and prediction as used
   c. Else:
      - Mark as false positive (no match)
4. For each unused gold label:
   - Mark as false negative (was missed)
5. Return matches list

IOU CALCULATION:
IoU = Intersection / Union

Where:
- Intersection = overlap length between two spans
- Union = total length of both spans combined

EXAMPLE:
- Prediction: chars 100-200 (length 100)
- Gold: chars 120-180 (length 60)
- Intersection: 60 (from 120-180)
- Union: 100 + 60 - 60 = 100
- IoU: 60 / 100 = 0.6 (60%)
- Since 0.6 >= 0.5 → Match!
```

---

### Algorithm 3: Classification (V2)

```python
INPUT: claim_text, brand_id, model_id
OUTPUT: "supported" | "contradicted" | "unknown"

ALGORITHM:
1. Get all facts for the model
2. Convert claim_text to lowercase
3. Check for negation words (not, no, never, does not)
4. For each fact:
   a. Check if claim mentions the fact field
   b. Based on fact type:
      
      BOOLEAN FACTS:
      - If has_negation:
        - If fact == false → return "supported"
        - If fact == true → return "contradicted"
      - If no negation:
        - If fact == true → return "supported"
        - If fact == false → return "contradicted"
      
      NUMERICAL FACTS:
      - Extract number from claim_text
      - Compare with fact value
      - If difference < 0.01 → return "supported"
      - If difference > 50% of fact → return "contradicted"
      
      STRING FACTS:
      - If fact value in claim_text → return "supported"
      - If different value found → return "contradicted"
   
5. Handle cross-model comparisons:
   - Pattern: "Model A costs X less/more than Model B"
   - Extract both model names
   - Get both prices from facts
   - Calculate actual difference
   - Compare with claimed difference
   - Return supported or contradicted

6. If no match found → return "unknown"

EXAMPLES:
- Claim: "Wi-Fi is absent"
  - Fact: wifi = false
  - Negation: yes ("absent")
  - Logic: absent + false = correct
  - Result: "supported"

- Claim: "Costs INR 1,299"
  - Fact: price_2026 = 1299
  - Extracted: 1299
  - Match: exact
  - Result: "supported"

- Claim: "Warranty is 18 months"
  - Fact: warranty_india = 12
  - Extracted: 18
  - Difference: 6
  - Threshold: 12 * 0.5 = 6
  - Not > threshold
  - Result: "unknown" (can't determine if it's a contradiction)
```

---

## Metrics Explained

### Extraction Metrics

These measure how well the agent identifies factual claims.

#### Precision
**Question**: Of all the claims the agent extracted, how many were correct?

**Formula**:
```
Precision = True Positives / (True Positives + False Positives)
```

**Your V1 Result**: 0.897 (89.7%)
- True Positives: 376 (correctly extracted)
- False Positives: 43 (wrongly extracted)
- Total Extracted: 419
- Precision: 376 / 419 = 0.897

**Meaning**: Out of 100 claims extracted, about 90 are correct.

---

#### Recall
**Question**: Of all the factual claims in the gold standard, how many did the agent find?

**Formula**:
```
Recall = True Positives / (True Positives + False Negatives)
```

**Your V1 Result**: 0.895 (89.5%)
- True Positives: 376 (found)
- False Negatives: 44 (missed)
- Total Gold: 420
- Recall: 376 / 420 = 0.895

**Meaning**: The agent found about 90% of all actual factual claims.

---

#### F1 Score
**Question**: Balanced measure of precision and recall.

**Formula**:
```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

**Your V1 Result**: 0.896 (89.6%)
- Harmonic mean of precision (0.897) and recall (0.895)

**Meaning**: Overall extraction performance.

---

### Classification Metrics

These measure how well the agent classifies the extracted claims.

#### Accuracy
**Question**: What percentage of classifications are correct?

**Formula**:
```
Accuracy = Correct Classifications / Total Classifications
```

---

#### Macro F1
**Question**: Average F1 score across all three classes.

**Formula**:
```
Macro F1 = (F1_supported + F1_contradicted + F1_unknown) / 3
```

**Your V1 Result**: ~0.15 (15%)
- Very low because most claims are classified as "unknown"

**Your V2 Result**: ~0.25 (25%)
- 67% improvement over V1

---

#### Combined F1
**Question**: Overall performance combining extraction and classification.

**Formula**:
```
Combined F1 = (Extraction F1 + Classification Macro F1) / 2
```

**Your V1 Result**: ~0.52 (52%)
- (0.896 + 0.15) / 2 = 0.523

**Your V2 Result**: ~0.57 (57%)
- (0.896 + 0.25) / 2 = 0.573

---

## Quick Reference

### File Purposes

| File | Purpose | Key Output |
|------|---------|------------|
| data_loader.py | Load CSV data | Python objects |
| agent_v1_rulebased.py | Baseline agent | Claims + classifications |
| agent_v2.py | Improved agent | Claims + better classifications |
| evaluator.py | Score performance | Metrics (precision, recall, F1) |
| utils.py | Helper functions | Model IDs |
| database.py | PostgreSQL schema | Database models |
| api.py | REST service | API endpoints |
| agent_v2_enhanced.py | V2 + observability | Tracing, async, retries |
| run_v1.py | Orchestrate V1 | Result files |
| run_v2.py | Orchestrate V2 | Result files |
| run_test_predictions.py | Generate test predictions | Test result files |

### Key Concepts

1. **Claim Extraction**: Identifying factual sentences from AI answers
2. **Claim Classification**: Determining if claims are supported/contradicted/unknown
3. **IoU Matching**: Using Intersection over Union to match claims
4. **Precision**: How many extracted claims are correct
5. **Recall**: How many gold claims were found
6. **F1 Score**: Balanced measure of precision and recall
7. **Macro F1**: Average F1 across all classes
8. **Rule-Based**: Using patterns and logic instead of ML/AI

### V1 vs V2 Differences

| Aspect | V1 | V2 |
|--------|-----|-----|
| Extraction | Same (keyword patterns) | Same (keyword patterns) |
| Classification | Simple string matching | Negation detection, number comparison, boolean logic |
| Classification F1 | ~0.15 (15%) | ~0.25 (25%) |
| Improvement | Baseline | +67% |

### Running the System

```bash
# Run V1 on development set
python3 run_v1.py

# Run V2 on development set
python3 run_v2.py

# Generate test predictions
python3 run_test_predictions.py

# Start API service
uvicorn src.api:app --reload
```

### Result Files

```
results/
├── v1_predictions.json          # V1 development predictions
├── v1_predictions.csv           # V1 development predictions (CSV)
├── v1_metrics.json              # V1 development metrics
├── v2_predictions.json          # V2 development predictions
├── v2_predictions.csv           # V2 development predictions (CSV)
├── v2_metrics.json              # V2 development metrics
├── v1_test_predictions.json     # V1 test predictions
├── v1_test_predictions.csv      # V1 test predictions (CSV)
└── v2_test_predictions.json     # V2 test predictions
```

---

## Summary

This system:
1. **Loads** CSV data (answers, facts, gold labels)
2. **Extracts** factual claims using rule-based patterns
3. **Classifies** claims as supported/contradicted/unknown using brand facts
4. **Evaluates** performance using IoU-based matching
5. **Stores** results in files and optionally in PostgreSQL
6. **Provides** a REST API for interactive use

The key innovation is V2's improved classification logic, which achieves 67% better classification accuracy over the baseline V1 agent.
