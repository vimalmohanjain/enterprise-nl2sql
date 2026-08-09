from training.config import QLoRAConfig


def test_qlora_config_defaults_match_proposal():
    config = QLoRAConfig()

    assert config.r == 16
    assert config.alpha == 32
    assert config.dropout == 0.05
    assert config.seed == 42

def test_qlora_config_training_defaults():
    config = QLoRAConfig()

    assert config.learning_rate == 2e-4
    assert config.epochs == 3
    assert config.batch_size == 2
    assert config.gradient_accumulation_steps == 8
    assert config.max_seq_length == 2048
    assert config.target_modules == (
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    )

def test_qlora_config_builds_lora_kwargs():
    config = QLoRAConfig()

    kwargs = config.to_lora_kwargs()

    assert kwargs == {
        "r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "target_modules": [
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        "bias": "none",
        "task_type": "CAUSAL_LM",
    }

def test_qlora_config_builds_trainer_kwargs():
    config = QLoRAConfig()

    kwargs = config.to_trainer_kwargs()

    assert kwargs == {
        "learning_rate": 2e-4,
        "num_train_epochs": 3,
        "per_device_train_batch_size": 2,
        "gradient_accumulation_steps": 8,
        "seed": 42,
    }