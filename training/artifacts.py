from dataclasses import dataclass


@dataclass(slots=True)
class TrainedAdapter:
    """Reference to a fine-tuned LoRA adapter."""

    base_model: str
    adapter_path: str