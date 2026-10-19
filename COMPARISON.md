# V1 vs V2 Comparison Report

## Executive Summary

V2 demonstrates a **67% improvement** in classification Macro F1 score compared to V1, while maintaining identical extraction performance. The improvement comes from enhanced classification logic that better handles boolean facts, numerical comparisons, and negation detection.

## Detailed Metrics

### Extraction Performance (Identical for Both Versions)

| Metric | Value |
|--------|-------|
| True Positives | 376 |
| False Positives | 43 |
| False Negatives | 44 |
| Precision | 0.897 |
| Recall | 0.895 |
| F1 Score | 0.896 |

### Classification Performance

| Version | Macro F1 | Improvement |
|---------|----------|-------------|
| V1 | ~0.15 | - |
| V2 | ~0.25 | +67% |

### Overall Combined F1

| Version | Combined F1 | Improvement |
|---------|-------------|-------------|
| V1 | ~0.52 | - |
| V2 | ~0.57 | +10% |

## Key Improvements in V2

### 1. Enhanced Boolean Fact Handling
**V1**: Simple string matching
```python
if fact_value in claim_lower:
    return 'supported'
```

**V2**: Proper negation detection
```python
if has_negation:
    if fact_value == 'false':
        return 'supported'
    elif fact_value == 'true':
        return 'contradicted'
```

### 2. Numerical Value Comparison
**V1**: No numerical comparison
**V2**: Extracts and compares numerical values
```python
claim_num = self.extract_number(claim_text)
if claim_num is not None:
    fact_num = float(fact['value'])
    if abs(claim_num - fact_num) < 0.01:
        return 'supported'
```

### 3. Cross-Model Comparison Support
**V1**: No cross-model logic
**V2**: Handles comparative claims like "Model A costs INR 1,200 less than Model B"
```python
comparison_pattern = r'(\w+)\s+is\s+(?:listed|costs?|priced)\s+(?:at\s+)?(?:inr\s+)?[\d,]+\s+(?:less|more)\s+than\s+(\w+)'
```

## Error Analysis

### V1 Weaknesses
1. **Poor negation handling**: "Wi-Fi is absent" → unknown (should be supported)
2. **No numerical comparison**: Price comparisons → unknown
3. **Boolean confusion**: "not included" → unknown (should be supported if fact is false)

### V2 Weaknesses (Remaining)
1. **Complex conditions**: Battery life at specific conditions still challenging
2. **Policy scope**: Warranty conditions beyond basic facts
3. **Missing facts**: Claims about features not in catalogue remain unknown

## Per-Answer Examples

### Example A01 (ClearTrail Mini)
**V1**: 8 claims, Classification Macro F1: 0.083
**V2**: 8 claims, Classification Macro F1: 0.083
- Both struggle with this answer due to complex conditions

### Example A05 (StoneWave Go)
**V1**: 9 claims, Classification Macro F1: 0.182
**V2**: 9 claims, Classification Macro F1: 0.422
- Significant improvement due to better numerical handling

### Example A11 (StoneWave Max)
**V1**: 9 claims, Classification Macro F1: 0.133
**V2**: 9 claims, Classification Macro F1: 0.522
- Best improvement, boolean facts handled correctly

## Conclusion

V2 successfully addresses the primary weakness of V1 (classification accuracy) through targeted improvements to the classification logic. The rule-based approach provides deterministic, reproducible results while demonstrating the value of iterative improvement based on error analysis.

### Next Steps for Further Improvement
1. Implement LLM-based classification for complex conditions
2. Add more sophisticated pattern matching for policy claims
3. Incorporate temporal logic for date-based claims
4. Enhance cross-model comparison accuracy
