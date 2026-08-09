from dataclasses import dataclass


@dataclass(slots=True)
class QLoRAConfig:
    """Configuration for QLoRA fine-tuning."""

    # LoRA / QLoRA
    r: int = 16
    alpha: int = 32
    dropout: float = 0.05

    # Training
    learning_rate: float = 2e-4
    epochs: int = 3
    batch_size: int = 2
    gradient_accumulation_steps: int = 8
    max_seq_length: int = 2048

    # Reproducibility
    seed: int = 42

    # Qwen projection modules
    target_modules: tuple[str, ...] = (
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    )

    def to_lora_kwargs(self) -> dict:
        return {
            "r": self.r,
            "lora_alpha": self.alpha,
            "lora_dropout": self.dropout,
            "target_modules": list(self.target_modules),
            "bias": "none",
            "task_type": "CAUSAL_LM",
        }

    def to_trainer_kwargs(self) -> dict:
        return {
            "learning_rate": self.learning_rate,
            "num_train_epochs": self.epochs,
            "per_device_train_batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "seed": self.seed,
        }