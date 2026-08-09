from src.schema_graph.sql_utils import clean_sql

class AdapterInference:
    """Run inference with a fine-tuned adapter model."""

    def __init__(
        self,
        *,
        model,
        tokenizer,
        max_new_tokens: int = 256,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.max_new_tokens = max_new_tokens

    def generate(
        self,
        prompt: str,
    ) -> str:
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
        )

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
        )

        prompt_length = len(inputs["input_ids"][0])

        generated_tokens = outputs[0][prompt_length:]

        decoded = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        )

        return clean_sql(decoded)