import pytest

from training.prompt_guard import (
    PromptLengthGuard,
    PromptTooLongError,
)


class FakeTokenizer:
    def encode(
        self,
        text,
        add_special_tokens=True,
    ):
        tokens = text.split()

        if add_special_tokens:
            return [0] + tokens

        return tokens


def test_prompt_guard_returns_token_count():
    guard = PromptLengthGuard(
        tokenizer=FakeTokenizer(),
        max_input_tokens=10,
    )

    count = guard.validate(
        "generate sql only"
    )

    assert count == 4


def test_prompt_guard_rejects_prompt_over_limit():
    guard = PromptLengthGuard(
        tokenizer=FakeTokenizer(),
        max_input_tokens=3,
    )

    with pytest.raises(
        PromptTooLongError,
        match="4 > 3",
    ):
        guard.validate(
            "generate sql only"
        )


def test_prompt_guard_allows_exact_limit():
    guard = PromptLengthGuard(
        tokenizer=FakeTokenizer(),
        max_input_tokens=4,
    )

    assert guard.validate(
        "generate sql only"
    ) == 4


def test_prompt_guard_rejects_invalid_limit():
    with pytest.raises(
        ValueError,
        match="must be positive",
    ):
        PromptLengthGuard(
            tokenizer=FakeTokenizer(),
            max_input_tokens=0,
        )