from .artifacts import TrainedAdapter


class AdapterLoader:
    """Load a base model and attach a trained LoRA adapter."""

    def __init__(
        self,
        *,
        model_loader,
        peft_loader,
        max_seq_length: int = 2048,
    ):
        self._model_loader = model_loader
        self._peft_loader = peft_loader
        self._max_seq_length = max_seq_length

    def load(
        self,
        adapter: TrainedAdapter,
    ):
        model, tokenizer = self._model_loader.from_pretrained(
            model_name=adapter.base_model,
            max_seq_length=self._max_seq_length,
            load_in_4bit=True,
        )

        model = self._peft_loader.from_pretrained(
            model,
            adapter.adapter_path,
        )

        return model, tokenizer