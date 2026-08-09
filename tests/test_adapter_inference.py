from training.adapter_inference import AdapterInference


class FakeTokenizer:
    def __call__(
        self,
        prompt,
        return_tensors,
    ):
        return {
            "input_ids": [[1, 2, 3]],
        }

    def decode(
        self,
        tokens,
        skip_special_tokens=True,
    ):
        return (
            "Prompt text\n"
            "SELECT name FROM employees;"
        )


class FakeModel:
    def generate(
        self,
        **kwargs,
    ):
        return [[1, 2, 3, 4]]


def test_adapter_inference_generates_text():
    inference = AdapterInference(
        model=FakeModel(),
        tokenizer=FakeTokenizer(),
    )

    result = inference.generate(
        "Show employee names"
    )

    assert "SELECT name FROM employees;" in result


def test_adapter_inference_returns_only_generated_completion():
    class CompletionTokenizer:
        def __call__(
            self,
            prompt,
            return_tensors,
        ):
            return {
                "input_ids": [[1, 2, 3]],
            }

        def decode(
            self,
            tokens,
            skip_special_tokens=True,
        ):
            assert tokens == [4, 5]
            return "SELECT name FROM employees;"

    class CompletionModel:
        def generate(
            self,
            **kwargs,
        ):
            return [[1, 2, 3, 4, 5]]

    inference = AdapterInference(
        model=CompletionModel(),
        tokenizer=CompletionTokenizer(),
    )

    result = inference.generate(
        "Show employee names"
    )

    assert result == "SELECT name FROM employees;"

def test_adapter_inference_cleans_generated_sql():
    class FencedTokenizer:
        def __call__(
            self,
            prompt,
            return_tensors,
        ):
            return {
                "input_ids": [[1, 2, 3]],
            }

        def decode(
            self,
            tokens,
            skip_special_tokens=True,
        ):
            return (
                "```sql\n"
                "SELECT name FROM employees;\n"
                "```"
            )

    class FencedModel:
        def generate(
            self,
            **kwargs,
        ):
            return [[1, 2, 3, 4, 5]]

    inference = AdapterInference(
        model=FencedModel(),
        tokenizer=FencedTokenizer(),
    )

    result = inference.generate(
        "Show employee names"
    )

    assert result == "SELECT name FROM employees;"