from .models import EvaluationExample, EvaluationResult, EvaluationDetail


class SQLEvaluator:
    """Evaluate generated SQL against expected SQL."""

    def evaluate(
        self,
        predicted_sql: str,
        expected_sql: str,
    ) -> bool:
        predicted = self._normalize(predicted_sql)
        expected = self._normalize(expected_sql)

        return predicted == expected

    def evaluate_batch(
        self,
        examples: list[EvaluationExample],
        predictions: list[str],
    ) -> EvaluationResult:
        if len(examples) != len(predictions):
            raise ValueError(
                "Examples and predictions must have the same length"
            )

        correct = sum(
            self.evaluate(
                predicted_sql=prediction,
                expected_sql=example.expected_sql,
            )
            for example, prediction in zip(
                examples,
                predictions,
            )
        )

        total = len(examples)
        accuracy = correct / total if total else 0.0

        return EvaluationResult(
            total=total,
            correct=correct,
            accuracy=accuracy,
        )

    def _normalize(self, sql: str) -> str:
        normalized = " ".join(sql.split())
        normalized = normalized.rstrip(";")
        normalized = normalized.lower()

        return normalized

    def evaluate_execution(
        self,
        predicted_sql: str,
        expected_sql: str,
        connection,
    ) -> bool:
        # Expected SQL is controlled by us.
        # If this fails, the benchmark itself is broken.
        expected_rows = connection.execute(
            expected_sql
        ).fetchall()

        # Predicted SQL comes from the model.
        # Invalid model output counts as incorrect.
        try:
            predicted_rows = connection.execute(
                predicted_sql
            ).fetchall()
        except Exception:
            return False

        return predicted_rows == expected_rows

    def evaluate_execution_batch(
        self,
        examples: list[EvaluationExample],
        predictions: list[str],
        connection,
    ) -> EvaluationResult:
        if len(examples) != len(predictions):
            raise ValueError(
                "Examples and predictions must have the same length"
            )

        correct = sum(
            self.evaluate_execution(
                predicted_sql=prediction,
                expected_sql=example.expected_sql,
                connection=connection,
            )
            for example, prediction in zip(
                examples,
                predictions,
            )
        )

        total = len(examples)
        accuracy = correct / total if total else 0.0

        return EvaluationResult(
            total=total,
            correct=correct,
            accuracy=accuracy,
        )

    def evaluate_details(
        self,
        examples: list[EvaluationExample],
        predictions: list[str],
        connection,
    ) -> list[EvaluationDetail]:
        if len(examples) != len(predictions):
            raise ValueError(
                "Examples and predictions must have the same length"
            )

        details = []

        for example, prediction in zip(
            examples,
            predictions,
        ):
            details.append(
                EvaluationDetail(
                    question=example.question,
                    expected_sql=example.expected_sql,
                    predicted_sql=prediction,
                    strict_match=self.evaluate(
                        predicted_sql=prediction,
                        expected_sql=example.expected_sql,
                    ),
                    execution_match=self.evaluate_execution(
                        predicted_sql=prediction,
                        expected_sql=example.expected_sql,
                        connection=connection,
                    ),
                )
            )

        return details