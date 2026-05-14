from __future__ import annotations

from pathlib import Path

from django.conf import settings


class LoRAFineTuningService:
    """Fine-tune a local causal language model with PEFT LoRA adapters."""

    def train(self, documents: list[dict], query: str = "") -> dict:
        if not getattr(settings, "LORA_ENABLED", False):
            return {
                "summary": "LoRA fine-tuning is disabled. Set LORA_ENABLED=True to train adapters.",
                "status": "disabled",
                "confidence": 0.4,
            }

        texts = self._load_training_texts(documents)
        if not texts:
            return {
                "summary": "No text-like documents were available for LoRA fine-tuning.",
                "status": "skipped",
                "confidence": 0.35,
            }

        try:
            result = self._train_adapter(texts, query)
        except Exception as exc:
            return {
                "summary": f"LoRA fine-tuning could not run: {exc}",
                "status": "failed",
                "confidence": 0.35,
            }
        return result

    def _train_adapter(self, texts: list[str], query: str) -> dict:
        import torch
        from peft import LoraConfig, TaskType, get_peft_model
        from torch.utils.data import Dataset
        from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments

        base_model = getattr(settings, "LORA_BASE_MODEL", "sshleifer/tiny-gpt2")
        local_only = getattr(settings, "LORA_LOCAL_FILES_ONLY", True)
        tokenizer = AutoTokenizer.from_pretrained(base_model, local_files_only=local_only)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(base_model, local_files_only=local_only)
        config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=getattr(settings, "LORA_R", 8),
            lora_alpha=getattr(settings, "LORA_ALPHA", 16),
            lora_dropout=getattr(settings, "LORA_DROPOUT", 0.05),
            target_modules=self._target_modules(model),
        )
        model = get_peft_model(model, config)

        dataset = _TextDataset(texts, tokenizer, getattr(settings, "LORA_MAX_LENGTH", 256))
        output_dir = Path(getattr(settings, "LORA_OUTPUT_DIR", Path(settings.BASE_DIR) / "data" / "lora_adapters"))
        run_dir = output_dir / self._safe_run_name(query)
        run_dir.mkdir(parents=True, exist_ok=True)

        training_args = TrainingArguments(
            output_dir=str(run_dir),
            per_device_train_batch_size=getattr(settings, "LORA_BATCH_SIZE", 1),
            max_steps=getattr(settings, "LORA_MAX_STEPS", 10),
            learning_rate=getattr(settings, "LORA_LEARNING_RATE", 2e-4),
            logging_steps=1,
            save_steps=getattr(settings, "LORA_MAX_STEPS", 10),
            report_to=[],
            remove_unused_columns=False,
            no_cuda=not torch.cuda.is_available(),
        )
        trainer = Trainer(model=model, args=training_args, train_dataset=dataset)
        metrics = trainer.train().metrics
        model.save_pretrained(run_dir)
        tokenizer.save_pretrained(run_dir)

        return {
            "summary": f"Trained LoRA adapter for {base_model} on {len(texts)} text sample(s).",
            "status": "completed",
            "base_model": base_model,
            "adapter_path": str(run_dir),
            "samples": len(texts),
            "metrics": {key: round(float(value), 4) for key, value in metrics.items() if isinstance(value, int | float)},
            "confidence": 0.72,
        }

    def _load_training_texts(self, documents: list[dict]) -> list[str]:
        texts = []
        for doc in documents:
            if doc.get("asset_type") not in {"text", "pdf", "csv"}:
                continue
            text = self._read_text(doc)
            for chunk in self._chunk(text):
                if len(chunk.split()) >= 8:
                    texts.append(chunk)
        return texts[: getattr(settings, "LORA_MAX_SAMPLES", 64)]

    def _read_text(self, doc: dict) -> str:
        path = Path(doc["path"])
        if not path.exists():
            return ""
        if doc.get("asset_type") == "pdf":
            try:
                from pypdf import PdfReader

                return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
            except Exception:
                return ""
        return path.read_text(errors="ignore")[:50000]

    def _chunk(self, text: str, size: int = 1000) -> list[str]:
        clean = " ".join(text.split())
        return [clean[index : index + size] for index in range(0, len(clean), size) if clean[index : index + size]]

    def _target_modules(self, model) -> list[str]:
        configured = getattr(settings, "LORA_TARGET_MODULES", "")
        if configured:
            return [item.strip() for item in configured.split(",") if item.strip()]
        module_names = {name.split(".")[-1] for name, _ in model.named_modules()}
        for candidates in (["c_attn"], ["q_proj", "v_proj"], ["query", "value"]):
            if any(candidate in module_names for candidate in candidates):
                return [candidate for candidate in candidates if candidate in module_names]
        return ["c_attn"]

    def _safe_run_name(self, query: str) -> str:
        base = "".join(char.lower() if char.isalnum() else "-" for char in query[:48]).strip("-")
        return base or "workflow-lora-adapter"


class _TextDataset:
    def __init__(self, texts, tokenizer, max_length: int):
        self.examples = [
            tokenizer(text, truncation=True, padding="max_length", max_length=max_length, return_tensors="pt")
            for text in texts
        ]

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, index):
        item = {key: value.squeeze(0) for key, value in self.examples[index].items()}
        item["labels"] = item["input_ids"].clone()
        return item
