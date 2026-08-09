from training.adapter_evaluator import AdapterEvaluator
from src.schema_graph.models import EvaluationExample


class FakeInference:
    def generate(self, prompt: str) -> str:
        return "SELECT name FROM employees;"


def test_adapter_evaluator_evaluates_examples():
    examples = [
        EvaluationExample(
            question="Show employee names",
            expected_sql="SELECT name FROM employees;",
        )
    ]

    evaluator = AdapterEvaluator(
        inference=FakeInference(),
    )

    results = evaluator.evaluate(
        examples,
        prompt_builder=lambda question: question,
    )

    assert len(results) == 1

    result = results[0]

    assert result.question == "Show employee names"
    assert result.expected_sql == "SELECT name FROM employees;"
    assert result.predicted_sql == "SELECT name FROM employees;"
    assert result.strict_match is True

def test_adapter_evaluator_uses_sql_normalization():
    class FakeInference:
        def generate(self, prompt: str) -> str:
            return "select name from employees;"

    examples = [
        EvaluationExample(
            question="Show employee names",
            expected_sql="SELECT name FROM employees",
        )
    ]

    evaluator = AdapterEvaluator(
        inference=FakeInference(),
    )

    results = evaluator.evaluate(
        examples,
        prompt_builder=lambda question: question,
    )

    assert results[0].strict_match is True