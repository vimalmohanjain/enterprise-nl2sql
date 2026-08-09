from training.adapter_loader import AdapterLoader
from training.artifacts import TrainedAdapter


class FakeModelLoader:
    @classmethod
    def from_pretrained(
        cls,
        *,
        model_name,
        max_seq_length,
        load_in_4bit,
    ):
        return "model", "tokenizer"


class FakePeftLoader:
    @classmethod
    def from_pretrained(
        cls,
        model,
        adapter_path,
    ):
        return f"{model}+adapter"


def test_adapter_loader_loads_base_model_and_adapter():
    adapter = TrainedAdapter(
        base_model="Qwen/Qwen2.5-Coder-7B-Instruct",
        adapter_path="/models/bird-qlora",
    )

    loader = AdapterLoader(
        model_loader=FakeModelLoader,
        peft_loader=FakePeftLoader,
        max_seq_length=2048,
    )

    model, tokenizer = loader.load(adapter)

    assert model == "model+adapter"
    assert tokenizer == "tokenizer"