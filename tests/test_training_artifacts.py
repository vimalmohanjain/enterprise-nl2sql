from training.artifacts import TrainedAdapter


def test_trained_adapter_contains_base_model_and_adapter_path():
    adapter = TrainedAdapter(
        base_model="Qwen/Qwen2.5-Coder-7B-Instruct",
        adapter_path="/models/bird-qlora",
    )

    assert adapter.base_model == "Qwen/Qwen2.5-Coder-7B-Instruct"
    assert adapter.adapter_path == "/models/bird-qlora"