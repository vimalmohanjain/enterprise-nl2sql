from training.unsloth_backend import UnslothBackend, UnslothTrainingStack


def test_unsloth_backend_requires_gpu_dependencies_only_when_training():
    backend = UnslothBackend()

def test_unsloth_backend_builds_training_components():
    calls = {}

    class FakeStack:
        def train(
            self,
            *,
            train_records,
            validation_records,
            plan,
            output_dir,
        ):
            calls["train_records"] = train_records
            calls["validation_records"] = validation_records
            calls["plan"] = plan
            calls["output_dir"] = output_dir

            return output_dir

    backend = UnslothBackend(
        stack=FakeStack(),
    )

    result = backend.train(
        train_records=[{"text": "train"}],
        validation_records=[{"text": "validation"}],
        plan={
            "model_name": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "lora": {},
            "trainer": {},
            "max_seq_length": 2048,
        },
        output_dir="adapters/qwen-nl2sql",
    )

    assert result == "adapters/qwen-nl2sql"
    assert calls["train_records"] == [{"text": "train"}]
    assert calls["validation_records"] == [{"text": "validation"}]
    assert calls["output_dir"] == "adapters/qwen-nl2sql"

def test_training_stack_builds_datasets():
    class FakeDataset:
        @classmethod
        def from_list(cls, records):
            return {
                "records": records,
            }

    stack = UnslothTrainingStack(
        dataset_class=FakeDataset,
    )

    train_dataset, validation_dataset = stack.build_datasets(
        train_records=[
            {
                "prompt": "Question: train\nSQL:\n",
                "completion": "SELECT 1",
            },
        ],
        validation_records=[
            {
                "prompt": "Question: validation\nSQL:\n",
                "completion": "SELECT 2",
            },
        ],
    )

    assert train_dataset == {
        "records": [
            {
                "prompt": "Question: train\nSQL:\n",
                "completion": "SELECT 1",
            }
        ]
    }

    assert validation_dataset == {
        "records": [
            {
                "prompt": "Question: validation\nSQL:\n",
                "completion": "SELECT 2",
            }
        ]
    }

def test_training_stack_loads_model_in_4bit():
    calls = {}

    class FakeModelLoader:
        @classmethod
        def from_pretrained(
            cls,
            *,
            model_name,
            max_seq_length,
            load_in_4bit,
        ):
            calls["model_name"] = model_name
            calls["max_seq_length"] = max_seq_length
            calls["load_in_4bit"] = load_in_4bit

            return "model", "tokenizer"

    from training.unsloth_backend import UnslothTrainingStack

    stack = UnslothTrainingStack(
        dataset_class=None,
        model_loader=FakeModelLoader,
    )

    model, tokenizer = stack.load_model(
        model_name="Qwen/Qwen2.5-Coder-7B-Instruct",
        max_seq_length=2048,
    )

    assert model == "model"
    assert tokenizer == "tokenizer"

    assert calls["model_name"] == (
        "Qwen/Qwen2.5-Coder-7B-Instruct"
    )
    assert calls["max_seq_length"] == 2048
    assert calls["load_in_4bit"] is True

def test_training_stack_applies_lora_adapter():
    calls = {}

    class FakeModelLoader:
        @classmethod
        def get_peft_model(cls, model, **kwargs):
            calls["model"] = model
            calls["kwargs"] = kwargs
            return "lora-model"

    stack = UnslothTrainingStack(
        dataset_class=None,
        model_loader=FakeModelLoader,
    )

    model = stack.apply_lora(
        model="base-model",
        lora_kwargs={
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
        },
    )

    assert model == "lora-model"
    assert calls["model"] == "base-model"
    assert calls["kwargs"]["r"] == 16
    assert calls["kwargs"]["lora_alpha"] == 32

def test_training_stack_builds_trainer():
    calls = {}

    class FakeTrainer:
        def __init__(
            self,
            *,
            model,
            args,
            train_dataset,
            eval_dataset,
            processing_class,
        ):
            calls["model"] = model
            calls["args"] = args
            calls["train_dataset"] = train_dataset
            calls["eval_dataset"] = eval_dataset
            calls["processing_class"] = processing_class

    class FakeSFTConfig:
        def __init__(self, **kwargs):
            calls["config_kwargs"] = kwargs
            self.kwargs = kwargs

    stack = UnslothTrainingStack(
        dataset_class=None,
        model_loader=None,
        trainer_class=FakeTrainer,
        trainer_config_class=FakeSFTConfig,
    )

    trainer = stack.build_trainer(
        model="lora-model",
        tokenizer="tokenizer",
        train_dataset="train-dataset",
        validation_dataset="validation-dataset",
        trainer_kwargs={
            "learning_rate": 2e-4,
            "num_train_epochs": 3,
            "per_device_train_batch_size": 2,
            "gradient_accumulation_steps": 8,
            "seed": 42,
        },
        max_seq_length=2048,
        output_dir="adapters/qwen-nl2sql",
    )

    assert trainer is not None
    assert calls["model"] == "lora-model"
    assert calls["train_dataset"] == "train-dataset"
    assert calls["eval_dataset"] == "validation-dataset"
    assert calls["processing_class"] == "tokenizer"

    assert calls["config_kwargs"]["max_length"] == 2048
    assert calls["config_kwargs"]["output_dir"] == "adapters/qwen-nl2sql"
    assert calls["config_kwargs"]["completion_only_loss"] is True

def test_training_stack_runs_training_and_saves_adapter():
    calls = []

    class FakeDataset:
        @classmethod
        def from_list(cls, records):
            return f"dataset:{records[0]['text']}"

    class FakeModelLoader:
        @classmethod
        def from_pretrained(
            cls,
            *,
            model_name,
            max_seq_length,
            load_in_4bit,
        ):
            calls.append("load_model")
            return FakeModel(), "tokenizer"

        @classmethod
        def get_peft_model(cls, model, **kwargs):
            calls.append("apply_lora")
            return model

    class FakeModel:
        def save_pretrained(self, output_dir):
            calls.append(("save_adapter", output_dir))

    class FakeTrainer:
        def __init__(self, **kwargs):
            calls.append("build_trainer")

        def train(self):
            calls.append("train")

    class FakeSFTConfig:
        def __init__(self, **kwargs):
            pass

    stack = UnslothTrainingStack(
        dataset_class=FakeDataset,
        model_loader=FakeModelLoader,
        trainer_class=FakeTrainer,
        trainer_config_class=FakeSFTConfig,
    )

    result = stack.train(
        train_records=[{"text": "train"}],
        validation_records=[{"text": "validation"}],
        plan={
            "model_name": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "lora": {
                "r": 16,
                "lora_alpha": 32,
            },
            "trainer": {},
            "max_seq_length": 2048,
        },
        output_dir="adapters/qwen-nl2sql",
    )

    assert result == "adapters/qwen-nl2sql"

    assert calls == [
        "load_model",
        "apply_lora",
        "build_trainer",
        "train",
        ("save_adapter", "adapters/qwen-nl2sql"),
    ]