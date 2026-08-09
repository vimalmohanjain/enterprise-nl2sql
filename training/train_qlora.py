from .config import QLoRAConfig


def build_training_plan(config: QLoRAConfig) -> dict:
    return {
        "model_name": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "lora": config.to_lora_kwargs(),
        "trainer": config.to_trainer_kwargs(),
        "max_seq_length": config.max_seq_length,
    }

class TrainingRunner:
    """Coordinate fine-tuning through a pluggable backend."""

    def __init__(
        self,
        backend,
        config: QLoRAConfig,
    ):
        self.backend = backend
        self.config = config

    def run(
        self,
        *,
        train_records,
        validation_records,
        output_dir: str,
    ):
        plan = build_training_plan(self.config)

        return self.backend.train(
            train_records=train_records,
            validation_records=validation_records,
            plan=plan,
            output_dir=output_dir,
        )