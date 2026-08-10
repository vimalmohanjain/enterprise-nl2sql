class UnslothBackend:
    """GPU training backend using Unsloth and TRL."""

    def __init__(self, stack=None):
        self._stack = stack

    def train(
        self,
        *,
        train_records,
        validation_records,
        plan,
        output_dir,
    ):
        if self._stack is None:
            raise NotImplementedError(
                "Real Unsloth training stack is not configured yet"
            )

        return self._stack.train(
            train_records=train_records,
            validation_records=validation_records,
            plan=plan,
            output_dir=output_dir,
        )


class UnslothTrainingStack:
    """Concrete training stack used for Unsloth/TRL fine-tuning."""

    def __init__(
        self,
        dataset_class,
        model_loader=None,
        trainer_class=None,
        trainer_config_class=None,
    ):
        self._dataset_class = dataset_class
        self._model_loader = model_loader
        self._trainer_class = trainer_class
        self._trainer_config_class = trainer_config_class

    def build_trainer(
        self,
        *,
        model,
        tokenizer,
        train_dataset,
        validation_dataset,
        trainer_kwargs: dict,
        max_seq_length: int,
        output_dir: str,
    ):
        config = self._trainer_config_class(
            **trainer_kwargs,
            max_length=max_seq_length,
            output_dir=output_dir,
            completion_only_loss=True,
        )

        return self._trainer_class(
            model=model,
            args=config,
            train_dataset=train_dataset,
            eval_dataset=validation_dataset,
            processing_class=tokenizer,
        )

    def build_datasets(
        self,
        *,
        train_records,
        validation_records,
    ):
        train_dataset = self._dataset_class.from_list(
            train_records
        )

        validation_dataset = self._dataset_class.from_list(
            validation_records
        )

        return train_dataset, validation_dataset

    def load_model(
        self,
        *,
        model_name: str,
        max_seq_length: int,
    ):
        return self._model_loader.from_pretrained(
            model_name=model_name,
            max_seq_length=max_seq_length,
            load_in_4bit=True,
        )

    def apply_lora(
        self,
        *,
        model,
        lora_kwargs: dict,
    ):
        return self._model_loader.get_peft_model(
            model,
            **lora_kwargs,
        )

    def train(
        self,
        *,
        train_records,
        validation_records,
        plan,
        output_dir,
    ):
        train_dataset, validation_dataset = self.build_datasets(
            train_records=train_records,
            validation_records=validation_records,
        )

        model, tokenizer = self.load_model(
            model_name=plan["model_name"],
            max_seq_length=plan["max_seq_length"],
        )

        model = self.apply_lora(
            model=model,
            lora_kwargs=plan["lora"],
        )

        trainer = self.build_trainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=train_dataset,
            validation_dataset=validation_dataset,
            trainer_kwargs=plan["trainer"],
            max_seq_length=plan["max_seq_length"],
            output_dir=output_dir,
        )

        trainer.train()

        model.save_pretrained(output_dir)

        return output_dir