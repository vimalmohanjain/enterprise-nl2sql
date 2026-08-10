class PromptTooLongError(ValueError):
    """Raised when a prompt exceeds the model input token budget."""


class PromptLengthGuard:
    """Validate prompt length before model generation."""

    def __init__(
        self,
        *,
        tokenizer,
        max_input_tokens: int,
    ):
        if max_input_tokens <= 0:
            raise ValueError(
                "max_input_tokens must be positive"
            )

        self.tokenizer = tokenizer
        self.max_input_tokens = max_input_tokens

    def count_tokens(
        self,
        prompt: str,
    ) -> int:
        return len(
            self.tokenizer.encode(
                prompt,
                add_special_tokens=True,
            )
        )

    def validate(
        self,
        prompt: str,
    ) -> int:
        token_count = self.count_tokens(prompt)

        if token_count > self.max_input_tokens:
            raise PromptTooLongError(
                "Prompt exceeds model input token budget: "
                f"{token_count} > {self.max_input_tokens}"
            )

        return token_count