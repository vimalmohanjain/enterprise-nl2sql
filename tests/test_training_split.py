from training.split import split_dataset


def test_split_dataset_is_reproducible():
    examples = list(range(100))

    train_1, validation_1 = split_dataset(
        examples,
        validation_ratio=0.1,
        seed=42,
    )

    train_2, validation_2 = split_dataset(
        examples,
        validation_ratio=0.1,
        seed=42,
    )

    assert train_1 == train_2
    assert validation_1 == validation_2

    assert len(train_1) == 90
    assert len(validation_1) == 10

    assert set(train_1).isdisjoint(validation_1)

    assert set(train_1 + validation_1) == set(examples)