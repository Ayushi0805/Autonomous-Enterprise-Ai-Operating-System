from __future__ import annotations

import json
from functools import lru_cache
from urllib import request as urlrequest

from django.conf import settings


class AISummaryService:
    """Generate an executive summary with Ollama first, then local transformers."""

    def summarize(self, state: dict, draft_report: str) -> dict:
        prompt = self._build_prompt(state, draft_report)
        for provider in (self._ollama_summary, self._transformer_summary):
            try:
                summary = provider(prompt)
            except Exception:
                summary = ""
            if summary:
                return {
                    "summary": summary,
                    "provider": provider.__name__.replace("_summary", "").strip("_"),
                    "confidence": 0.84,
                }
        return {
            "summary": self._fallback_summary(state, draft_report),
            "provider": "deterministic_fallback",
            "confidence": 0.64,
        }

    def _build_prompt(self, state: dict, draft_report: str) -> str:
        payload = {
            "business_question": state.get("user_query", ""),
            "workflow_type": state.get("workflow_type", ""),
            "plan": state.get("plan", []),
            "retrieved_context": [chunk.get("chunk", "") for chunk in state.get("retrieved_chunks", [])[:5]],
            "eda_results": state.get("eda_results"),
            "ml_results": state.get("ml_results"),
            "lora_results": state.get("lora_results"),
            "vision_results": state.get("vision_results"),
            "nlp_results": state.get("nlp_results"),
            "draft_report": draft_report,
        }
        return (
            "Write a concise enterprise AI report summary. Include: executive summary, "
            "key findings, risks or anomalies, recommended next steps, and confidence. "
            "Do not invent facts beyond the supplied workflow data.\n\n"
            f"Workflow data:\n{json.dumps(payload, default=str)[:8000]}"
        )

    def _ollama_summary(self, prompt: str) -> str:
        if not getattr(settings, "OLLAMA_ENABLED", True):
            return ""
        base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        model = getattr(settings, "OLLAMA_MODEL", "llama3.1")
        data = json.dumps(
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 700},
            }
        ).encode("utf-8")
        req = urlrequest.Request(
            f"{base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        timeout = getattr(settings, "OLLAMA_TIMEOUT_SECONDS", 20)
        with urlrequest.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return self._clean(payload.get("response", ""))

    def _transformer_summary(self, prompt: str) -> str:
        summarizer = _hf_summarizer()
        if summarizer is None:
            return ""
        max_input_chars = getattr(settings, "HF_SUMMARY_MAX_INPUT_CHARS", 6000)
        result = summarizer(
            prompt[:max_input_chars],
            max_length=getattr(settings, "HF_SUMMARY_MAX_LENGTH", 360),
            min_length=getattr(settings, "HF_SUMMARY_MIN_LENGTH", 80),
            do_sample=False,
        )
        if not result:
            return ""
        return self._clean(result[0].get("summary_text", ""))

    def _fallback_summary(self, state: dict, draft_report: str) -> str:
        findings = []
        for key in ("eda_results", "ml_results", "lora_results", "vision_results", "nlp_results"):
            value = state.get(key) or {}
            if value.get("summary"):
                findings.append(value["summary"])
        if not findings and draft_report:
            findings.append(draft_report[:700])
        if not findings:
            findings.append("No sufficient workflow evidence was available for a grounded AI summary.")
        return "\n".join(
            [
                "Executive Summary",
                findings[0],
                "",
                "Recommended Next Steps",
                "Review the source outputs, validate any low-confidence items, and rerun the workflow with richer assets if more precision is needed.",
            ]
        )

    def _clean(self, text: str) -> str:
        return text.strip().replace("\r\n", "\n")


@lru_cache(maxsize=1)
def _hf_summarizer():
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

        model = getattr(settings, "HF_SUMMARY_MODEL", "sshleifer/distilbart-cnn-12-6")
        local_only = getattr(settings, "HF_SUMMARY_LOCAL_FILES_ONLY", True)
        tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=local_only)
        summary_model = AutoModelForSeq2SeqLM.from_pretrained(model, local_files_only=local_only)
        return pipeline("summarization", model=summary_model, tokenizer=tokenizer)
    except Exception:
        return None
