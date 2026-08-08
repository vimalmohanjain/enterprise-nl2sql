import requests

from src.schema_graph.parser import SchemaParser
from src.schema_graph.ollama_client import OllamaClient
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

schema = SchemaParser().parse(ddl)

client = OllamaClient(
    http_client=requests,
    model="qwen2.5-coder:7b",
)

service = NL2SQLService(
    client=client,
)

sql = service.generate(
    question="Show employee names and their department names",
    schema=schema,
)

print(sql)