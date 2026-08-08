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

## 8. Next Step: Reproducibility

Before fine-tuning, the Ollama generation configuration should be made deterministic or as reproducible as practical.

This will reduce benchmark variation and provide a stable baseline for comparison.

After reproducibility is established, the same benchmark will be run again and recorded as the **controlled baseline**.

---

## 9. Future Fine-Tuned Model Comparison

The final comparison will use the same evaluation framework and benchmark.

| Model                                  | Strict SQL Accuracy | Execution Accuracy |
| -------------------------------------- | ------------------: | -----------------: |
| Qwen2.5-Coder 7B — Initial baseline    |     33.33% – 46.67% |    80.00% – 86.67% |
| Qwen2.5-Coder 7B — Controlled baseline |                 TBD |                TBD |
| Fine-tuned model                       |                 TBD |                TBD |

The primary success criterion for fine-tuning will be improvement in **Execution Accuracy**, while strict SQL accuracy and error categories will be retained as secondary diagnostics.
