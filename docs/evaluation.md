# NL2SQL Evaluation

## 1. Purpose

This document records the evaluation methodology and baseline results for the Enterprise NL2SQL system.

The goal is to establish a reproducible baseline for the local model before fine-tuning and to measure whether later changes improve SQL generation quality.

---

## 2. Baseline Model

* **Model:** Qwen2.5-Coder 7B
* **Runtime:** Ollama
* **Benchmark size:** 15 questions
* **Primary metric:** Execution Accuracy
* **Secondary metric:** Strict SQL Match Accuracy

The benchmark currently covers:

* Simple SELECT queries
* Column selection
* Numeric filters
* COUNT
* AVG
* MIN
* MAX
* SUM
* ORDER BY and LIMIT
* Foreign-key joins
* Join + filter
* GROUP BY with aggregation

---

## 3. Evaluation Metrics

### 3.1 Strict SQL Match

The predicted and expected SQL are normalized before comparison.

Normalization currently handles:

* SQL keyword case differences
* Whitespace differences
* Trailing semicolons

Example:

Expected:

```
SELECT * FROM employees
```

Predicted:

```
SELECT * FROM employees;
```

These are treated as equivalent.

Strict matching can still reject semantically equivalent SQL when there are differences such as:

* Column aliases
* Table aliases
* Equivalent GROUP BY expressions
* Different but equivalent SQL structures

Therefore, strict SQL accuracy is retained as a secondary diagnostic metric rather than the primary measure of model quality.

### 3.2 Execution Accuracy

Both the expected SQL and generated SQL are executed against the same SQLite test database.

The resulting rows are compared.

This allows semantically equivalent SQL to pass even when its textual representation differs.

Example:

Expected:

```
SELECT AVG(salary) FROM employees
```

Predicted:

```
SELECT AVG(salary) AS average_salary FROM employees;
```

Strict Match: FAIL

Execution Match: PASS

Execution Accuracy is therefore the primary evaluation metric.

Invalid generated SQL is counted as an incorrect prediction rather than causing the complete benchmark run to fail.

---

## 4. Baseline Results

### Run 1 — Initial Strict Evaluation

This run was performed before execution-based evaluation was implemented.

| Metric             |      Correct | Accuracy |
| ------------------ | -----------: | -------: |
| Strict SQL Match   |       7 / 15 |   46.67% |
| Execution Accuracy | Not measured |        — |

This run demonstrated that strict string comparison significantly underestimates semantic SQL correctness.

### Run 2 — Execution Evaluation

| Metric             | Correct | Accuracy |
| ------------------ | ------: | -------: |
| Strict SQL Match   |  6 / 15 |   40.00% |
| Execution Accuracy | 12 / 15 |   80.00% |

Execution evaluation showed that many apparent strict-match failures were actually semantically correct queries.

### Run 3 — Execution Evaluation

| Metric             | Correct | Accuracy |
| ------------------ | ------: | -------: |
| Strict SQL Match   |  6 / 15 |   40.00% |
| Execution Accuracy | 13 / 15 |   86.67% |

Only two predictions produced results different from the reference queries.

### Run 4 — Detailed Evaluation Report

| Metric             | Correct | Accuracy |
| ------------------ | ------: | -------: |
| Strict SQL Match   |  5 / 15 |   33.33% |
| Execution Accuracy | 12 / 15 |   80.00% |

The detailed evaluator identified the following execution failures:

1. **Show employee salaries**

   * The model returned additional employee columns and an unnecessary department join.

2. **Show employees with salary greater than 50000**

   * The model unnecessarily joined the departments table and changed the result projection.

3. **Show the top 10 employees by salary**

   * The model selected specific employee columns instead of returning the complete employee rows requested by the reference query.

---

## 5. Baseline Summary

Measured baseline results currently fall within the following ranges:

| Metric              |  Observed Range |
| ------------------- | --------------: |
| Strict SQL Accuracy | 33.33% – 46.67% |
| Execution Accuracy  | 80.00% – 86.67% |

Execution Accuracy is the primary baseline metric.

The variation between repeated runs indicates that model generation is not yet fully deterministic under the current Ollama configuration.

Before comparing the baseline against a fine-tuned model, generation parameters should be controlled to make benchmark runs reproducible.

---

## 6. Error Analysis

### 6.1 Harmless SQL Differences

The following frequently cause strict-match failures while still producing correct results:

* Column aliases such as `AS average_salary`
* Column aliases such as `AS department_name`
* Table aliases such as `employees e`
* Table aliases such as `departments d`
* Formatting differences
* Equivalent GROUP BY expressions

These should not be treated as semantic model failures when execution results are equivalent.

### 6.2 Genuine Model Errors

The current benchmark has exposed several genuine error patterns.

#### Over-selection

The model sometimes returns additional columns that were not requested.

Example:

Requested:

```
SELECT salary FROM employees
```

Possible prediction:

```
SELECT employee_id, name, salary FROM employees
```

#### Unnecessary Joins

The model sometimes expands into related tables even when the question only requires one table.

This changes the result shape and may also alter results when foreign-key relationships are incomplete.

#### Projection Mismatch

For questions represented by `SELECT *`, the model sometimes explicitly selects only a subset of columns.

Example:

Expected:

```
SELECT *
FROM employees
ORDER BY salary DESC
LIMIT 10
```

Prediction:

```
SELECT employee_id, name, salary
FROM employees
ORDER BY salary DESC
LIMIT 10
```

Although the returned business information may appear reasonable, the result is not equivalent to the reference query.

---

## 7. Evaluation Framework Status

The evaluation framework currently supports:

* Strict normalized SQL comparison
* Batch strict evaluation
* SQLite execution-based comparison
* Batch execution evaluation
* Invalid generated SQL handling
* Per-question strict-match reporting
* Per-question execution-match reporting
* Overall accuracy calculation

The framework is now capable of comparing the baseline model with future model versions using the same benchmark.

---

## 8. BIRD Evaluation

The project now includes a second, substantially larger evaluation
track based on the BIRD NL2SQL dataset.

The complete BIRD training corpus contains 9,428 examples.

A deterministic 90/10 split using seed 42 produces:

| Split | Examples |
| --- | ---: |
| Training | 8,486 |
| Validation | 942 |
| Total | 9,428 |

The 942 validation examples are held out from QLoRA training and are
used for post-training model evaluation.

### 8.1 Evaluation Schema Handling

Training and evaluation deliberately use different schema-selection
rules where necessary.

During supervised training, oversized examples may use gold SQL to
prune schemas to fit the configured sequence length.

During held-out evaluation, gold SQL is never used for schema
selection.

The initial BIRD evaluation uses the complete database schema when
constructing each prompt.

This avoids evaluation leakage and separates model-generation quality
from schema-retrieval quality.

### 8.2 Per-Database Execution

Every BIRD evaluation example preserves its `db_id`.

The database resolver maps:

```text
db_id
↓
train_databases/<db_id>/<db_id>.sqlite
```

The predicted SQL and expected SQL are executed against the same
database.

This allows execution accuracy to be calculated across the complete
multi-database validation set.

### 8.3 Evaluation Pipeline

```text
942 held-out BIRD examples
│
▼
BirdPromptBuilder
│
▼
schema-aware prompt
│
▼
AdapterInference
│
▼
generated SQL
│
├──────────────────┐
▼                  ▼
Strict Match       Execution Match
│                  │
▼                  ▼
normalized SQL     correct BIRD SQLite DB
│                  │
└─────────┬────────┘
          ▼
   EvaluationDetail
```

The same `SQLEvaluator` normalization and execution semantics used by
the original baseline framework are reused for adapter evaluation.

---

## 9. Retrieval Coverage Evaluation

Schema retrieval is evaluated separately from SQL generation.

Across all 9,428 BIRD examples, initial retrieval achieved:

| Coverage | Examples | Percentage |
| --- | ---: | ---: |
| Full | 4,922 | 52.21% |
| Partial | 2,788 | 29.57% |
| Zero | 1,718 | 18.22% |

After retrieval improvements:

| Coverage | Examples | Percentage |
| --- | ---: | ---: |
| Full | 6,217 | 65.94% |
| Partial | 1,831 | 19.42% |
| Zero | 1,380 | 14.64% |

Full retrieval coverage therefore improved by **13.73 percentage
points**.

This metric is intentionally kept separate from model execution
accuracy because a generation failure can originate from either:

1. incorrect/incomplete schema retrieval, or
2. incorrect SQL generation despite sufficient schema context.

---

## 10. Fine-Tuning Evaluation Plan

The initial fine-tuning experiment uses
`Qwen/Qwen2.5-Coder-7B-Instruct` with QLoRA.

A 200-example smoke test completed successfully before the full
training run.

The full first-epoch experiment uses:

| Setting | Value |
| --- | ---: |
| Training examples | 8,486 |
| Validation examples | 942 |
| Epochs | 1 |
| Training steps | 2,122 |
| LoRA rank | 16 |
| LoRA alpha | 32 |
| LoRA dropout | 0 |
| Maximum sequence length | 2,048 |
| Effective batch size | 4 |

The first epoch will be evaluated before any decision is made to
continue training.

The post-training comparison will include:

| Model | Strict Accuracy | Execution Accuracy |
| --- | ---: | ---: |
| Qwen2.5-Coder 7B baseline | TBD | TBD |
| Qwen2.5-Coder 7B + QLoRA | TBD | TBD |

Execution accuracy is the primary success metric.

Additional epochs will be considered only if held-out evaluation
indicates that further training is likely to improve generalization.

---

## 11. Current Status

Completed:

- Local 15-question baseline framework
- Normalized strict SQL evaluation
- SQLite execution evaluation
- Per-question evaluation details
- BIRD ingestion
- BIRD schema conversion
- Retrieval coverage measurement
- Training-schema token profiling
- Oversized-schema pruning
- Deterministic 8,486 / 942 split
- Schema-aware training-record generation
- QLoRA configuration
- Unsloth training backend
- 200-example GPU smoke test
- Adapter inference abstraction
- Shared SQL cleanup
- BIRD validation reconstruction
- BIRD database resolution
- Per-database execution evaluator
- BIRD evaluation pipeline
- Full-schema held-out prompt builder

In progress:

- Full 8,486-example one-epoch QLoRA training run

Pending:

- Adapter sanity inference after training
- 942-example held-out BIRD evaluation
- Base-model versus fine-tuned comparison
- Error analysis of held-out failures
- Decision on additional training epochs