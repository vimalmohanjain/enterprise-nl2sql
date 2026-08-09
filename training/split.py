import random
from typing import TypeVar

T = TypeVar("T")


def split_dataset(
    examples: list[T],
    validation_ratio: float = 0.1,
    seed: int = 42,
) -> tuple[list[T], list[T]]:
    """Split examples into reproducible training and validation sets."""

    shuffled = list(examples)

    random_generator = random.Random(seed)
    random_generator.shuffle(shuffled)

    validation_size = int(len(shuffled) * validation_ratio)

    validation = shuffled[:validation_size]
    train = shuffled[validation_size:]

    return train, validation