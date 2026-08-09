from training.config import QLoRAConfig
from training.train_qlora import build_training_plan
from training.config import QLoRAConfig
from training.train_qlora import TrainingRunner

# QLoRAConfig
#      │
#      ├── model
#      │
#      ├── LoRA settings
#      │      r=16
#      │      alpha=32
#      │
#      ├── trainer settings
#      │
#      └── max sequence length
#              ↓
#        Training Plan
#              ↓
#       Unsloth / TRL


def test_build_training_plan():
    config = QLoRAConfig()

    plan = build_training_plan(config)

    assert plan["model_name"] == "Qwen/Qwen2.5-Coder-7B-Instruct"

    assert plan["lora"] == config.to_lora_kwargs()
    assert plan["trainer"] == config.to_trainer_kwargs()

    assert plan["max_seq_length"] == 2048
    
class FakeBackend:
    def __init__(self):
        self.calls = []

    def train(
        self,
        *,
        train_records,
        validation_records,
        plan,
        output_dir,
    ):
        self.calls.append(
            {
                "train_records": train_records,
                "validation_records": validation_records,
                "plan": plan,
                "output_dir": output_dir,
            }
        )

        return output_dir


def test_training_runner_delegates_to_backend():
    backend = FakeBackend()
    config = QLoRAConfig()

    runner = TrainingRunner(
        backend=backend,
        config=config,
    )

    train_records = [{"text": "train example"}]
    validation_records = [{"text": "validation example"}]

    result = runner.run(
        train_records=train_records,
        validation_records=validation_records,
        output_dir="adapters/qwen-nl2sql",
    )

    assert result == "adapters/qwen-nl2sql"

    assert len(backend.calls) == 1

    call = backend.calls[0]

    assert call["train_records"] == train_records
    assert call["validation_records"] == validation_records

    assert call["plan"]["model_name"] == (
        "Qwen/Qwen2.5-Coder-7B-Instruct"
    )

    assert call["output_dir"] == "adapters/qwen-nl2sql"