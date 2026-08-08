import requests

from src.schema_graph.evaluator import SQLEvaluator
from src.schema_graph.models import EvaluationExample
from src.schema_graph.ollama_client import OllamaClient
from src.schema_graph.parser import SchemaParser
from src.schema_graph.service import NL2SQLService


ddl = """
CREATE TABLE departments (
    department_id INT PRIMARY KEY,
    name TEXT
);

CREATE TABLE employees (
    employee_id INT PRIMARY KEY,
    name TEXT,
    salary REAL,
    department_id INT,
    FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
);
"""

benchmark = [
    EvaluationExample(
        question="Show all employees",
        expected_sql="SELECT * FROM employees",
    ),
    EvaluationExample(
        question="Show employee names",
        expected_sql="SELECT name FROM employees",
    ),
    EvaluationExample(
        question="Show employee salaries",
        expected_sql="SELECT salary FROM employees",
    ),
    EvaluationExample(
        question="Show employees with salary greater than 50000",
        expected_sql="SELECT * FROM employees WHERE salary > 50000",
    ),
    EvaluationExample(
        question="How many employees are there?",
        expected_sql="SELECT COUNT(*) FROM employees",
    ),
    EvaluationExample(
        question="What is the average employee salary?",
        expected_sql="SELECT AVG(salary) FROM employees",
    ),
    EvaluationExample(
        question="What is the minimum employee salary?",
        expected_sql="SELECT MIN(salary) FROM employees",
    ),
    EvaluationExample(
        question="What is the maximum employee salary?",
        expected_sql="SELECT MAX(salary) FROM employees",
    ),
    EvaluationExample(
        question="What is the total employee salary?",
        expected_sql="SELECT SUM(salary) FROM employees",
    ),
    EvaluationExample(
        question="Show the top 10 employees by salary",
        expected_sql=(
            "SELECT * FROM employees "
            "ORDER BY salary DESC LIMIT 10"
        ),
    ),
    EvaluationExample(
        question="Show employee names and their department names",
        expected_sql=(
            "SELECT employees.name, departments.name "
            "FROM employees "
            "JOIN departments "
            "ON employees.department_id = departments.department_id"
        ),
    ),
    EvaluationExample(
        question="Show employees earning more than 50000 and their department names",
        expected_sql=(
            "SELECT employees.name, departments.name "
            "FROM employees "
            "JOIN departments "
            "ON employees.department_id = departments.department_id "
            "WHERE employees.salary > 50000"
        ),
    ),
    EvaluationExample(
        question="Show average salary by department",
        expected_sql=(
            "SELECT departments.name, AVG(employees.salary) "
            "FROM employees "
            "JOIN departments "
            "ON employees.department_id = departments.department_id "
            "GROUP BY departments.name"
        ),
    ),
    EvaluationExample(
        question="Show all departments",
        expected_sql="SELECT * FROM departments",
    ),
    EvaluationExample(
        question="Show department names",
        expected_sql="SELECT name FROM departments",
    ),
]


schema = SchemaParser().parse(ddl)

client = OllamaClient(
    http_client=requests,
    model="qwen2.5-coder:7b",
)

service = NL2SQLService(client=client)

predictions = []

for index, example in enumerate(benchmark, start=1):
    prediction = service.generate(
        question=example.question,
        schema=schema,
    )

    predictions.append(prediction)

    print(f"\n[{index}] {example.question}")
    print(f"EXPECTED:  {example.expected_sql}")
    print(f"PREDICTED: {prediction}")


evaluator = SQLEvaluator()

result = evaluator.evaluate_batch(
    examples=benchmark,
    predictions=predictions,
)

print("\n==============================")
print("BASELINE RESULTS")
print("==============================")
print(f"Total:    {result.total}")
print(f"Correct:  {result.correct}")
print(f"Accuracy: {result.accuracy:.2%}")