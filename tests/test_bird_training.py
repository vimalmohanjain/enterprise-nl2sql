from src.schema_graph.context_builder import ContextBuilder
from src.schema_graph.models import (
    BirdTrainingExample,
    Column,
    DatabaseSchema,
    DatasetExample,
    Table,
)
from src.schema_graph.prompt_builder import PromptBuilder
from training.formatter import TrainingFormatter


def test_bird_example_can_be_formatted_for_training():
    schema = DatabaseSchema()

    employees = Table(
        name="employees",
        columns=[
            Column(
                name="employee_id",
                data_type="integer",
                is_primary_key=True,
            ),
            Column(
                name="name",
                data_type="text",
            ),
        ],
    )

    schema.add_table(employees)

    bird_example = BirdTrainingExample(
        db_id="company",
        question="Show employee names",
        sql="SELECT name FROM employees",
        schema=schema,
    )

    context = ContextBuilder().build_full(
        bird_example.schema
    )

    schema_text = PromptBuilder().build_schema_context(
        context
    )

    dataset_example = DatasetExample(
        question=bird_example.question,
        sql=bird_example.sql,
    )

    record = TrainingFormatter().format(
        dataset_example,
        schema_context=schema_text,
    )

    assert "employees" in record["text"]
    assert "employee_id" in record["text"]
    assert "Show employee names" in record["text"]
    assert "SELECT name FROM employees" in record["text"]