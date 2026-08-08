# NL2SQL Evaluation

## Baseline Model

Model: Qwen2.5-Coder 7B
Runtime: Ollama
Evaluation set: 15 questions

## Baseline Run 1

### Strict SQL Match

Total: 15
Correct: 7
Accuracy: 46.67%

### Important Observation

Strict SQL matching underestimates model performance because
semantically equivalent SQL can differ syntactically.

Examples:

Expected:
SELECT AVG(salary) FROM employees

Predicted:
SELECT AVG(salary) AS average_salary FROM employees;

These queries return equivalent values but fail strict string matching.

### Observed Error Categories

1. Formatting differences
   - trailing semicolons
   - whitespace
   - SQL keyword case
   - already handled by normalization

2. Alias differences
   - AS average_salary
   - AS department_name
   - currently counted as incorrect

3. Table alias differences
   - employees vs e
   - departments vs d
   - currently counted as incorrect

4. Projection differences
   - extra/missing selected columns
   - genuine semantic differences

5. Query-structure differences
   - e.g. GROUP BY department_id vs department name
   - may still be semantically equivalent depending on schema constraints

## Next Step

Add execution-based evaluation using SQLite.

Both expected and predicted SQL will be executed against the
same test database and their result sets compared.

Metrics:

- Strict SQL Match Accuracy
- Execution Accuracy

                     Strict     Execution
Baseline Qwen 7B      46.67%       ??%
Fine-tuned Qwen 7B      ??%        ??%