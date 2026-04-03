"""X-ray image analysis using external vision APIs."""
import base64
import io
import json
import mimetypes
import os
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from groq import Groq
except ImportError:
    Groq = None


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON from model output, handling optional code fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


class XrayAnalyzer:
    """Analyze X-ray images with Gemini/Groq vision APIs."""

    XRAY_CLASSES = ("Normal", "Pneumonia", "COVID-19", "Tuberculosis", "Abnormal")

    def __init__(self, model_path: str = None):
        self.provider = os.getenv("AI_PROVIDER", "gemini").lower()
        self.backup_provider = os.getenv("BACKUP_PROVIDER", "").lower()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_vision_model = os.getenv(
            "GROQ_VISION_MODEL",
            "meta-llama/llama-4-scout-17b-16e-instruct",
        )
        self.groq_client = None

        if self._has_valid_gemini_key() and genai:
            genai.configure(api_key=self.gemini_api_key)

        if self._has_valid_groq_key() and Groq:
            self.groq_client = Groq(api_key=self.groq_api_key)

    def _has_valid_gemini_key(self) -> bool:
        if not self.gemini_api_key:
            return False
        key = self.gemini_api_key.strip()
        return key not in {"", "your_gemini_api_key_here", "your_api_key_here"}

    def _has_valid_groq_key(self) -> bool:
        if not self.groq_api_key:
            return False
        key = self.groq_api_key.strip()
        return key not in {"", "your_groq_api_key_here", "your_api_key_here"}

    def _load_image(self, image_path: str) -> Tuple[bytes, str, Image.Image]:
        with open(image_path, "rb") as handle:
            image_bytes = handle.read()

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        mime_type = mimetypes.guess_type(image_path)[0]
        if not mime_type:
            format_name = (image.format or "jpeg").lower()
            mime_type = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
                "bmp": "image/bmp",
                "tif": "image/tiff",
                "tiff": "image/tiff",
            }.get(format_name, "image/jpeg")

        return image_bytes, mime_type, image

    def _provider_order(self) -> List[str]:
        candidates: List[str] = []

        if self.provider in {"gemini", "groq"}:
            candidates.append(self.provider)

        if self.backup_provider in {"gemini", "groq"} and self.backup_provider not in candidates:
            candidates.append(self.backup_provider)

        if "gemini" not in candidates and self._has_valid_gemini_key() and genai:
            candidates.append("gemini")

        if "groq" not in candidates and self._has_valid_groq_key() and self.groq_client:
            candidates.append("groq")

        return candidates

    def _build_prompt(self) -> str:
        return (
            "You are a medical imaging assistant reviewing a chest X-ray for educational use only. "
            "Return strict JSON only with these keys: classification, confidence_score, findings, "
            "recommendations, clinical_note, all_probabilities.\n\n"
            "Rules:\n"
            f"- classification must be one of: {', '.join(self.XRAY_CLASSES)} or Uncertain.\n"
            "- confidence_score must be a number between 0 and 1.\n"
            "- all_probabilities must include Normal, Pneumonia, COVID-19, Tuberculosis, and Abnormal.\n"
            "- If the image is low quality or the finding is unclear, use classification Uncertain and conservative wording.\n"
            "- Avoid saying this is a diagnosis or a final medical opinion.\n"
            "- recommendations must be a JSON array of short follow-up suggestions.\n"
        )

    def _fallback_probability_map(self, classification: str, confidence_score: float) -> Dict[str, float]:
        if classification not in self.XRAY_CLASSES:
            return {label: 0.2 for label in self.XRAY_CLASSES}

        confidence_score = max(0.0, min(1.0, confidence_score))
        remainder = max(0.0, 1.0 - confidence_score)
        distributed = remainder / (len(self.XRAY_CLASSES) - 1)
        return {
            label: (confidence_score if label == classification else distributed)
            for label in self.XRAY_CLASSES
        }

    def _normalize_probability_map(
        self,
        raw_probabilities: Any,
        classification: str,
        confidence_score: float,
    ) -> Dict[str, float]:
        if not isinstance(raw_probabilities, dict) or not raw_probabilities:
            return self._fallback_probability_map(classification, confidence_score)

        normalized: Dict[str, float] = {}
        lookup = {str(key).lower(): value for key, value in raw_probabilities.items()}

        for label in self.XRAY_CLASSES:
            raw_value = lookup.get(label.lower(), 0.0)
            try:
                normalized[label] = max(0.0, min(1.0, float(raw_value)))
            except (TypeError, ValueError):
                normalized[label] = 0.0

        total = sum(normalized.values())
        if total <= 0:
            return self._fallback_probability_map(classification, confidence_score)

        return {label: round(value / total, 4) for label, value in normalized.items()}

    def _build_result(
        self,
        image_path: str,
        payload: Dict[str, Any],
        provider: str,
    ) -> Dict[str, Any]:
        classification = str(payload.get("classification", "Uncertain")).strip() or "Uncertain"
        if classification not in self.XRAY_CLASSES and classification != "Uncertain":
            classification = "Uncertain"

        findings = str(
            payload.get("findings")
            or payload.get("clinical_note")
            or "Unable to interpret the X-ray image confidently."
        )
        clinical_note = str(payload.get("clinical_note") or findings)

        try:
            confidence_score = float(payload.get("confidence_score", 0.58))
        except (TypeError, ValueError):
            confidence_score = 0.58

        confidence_score = max(0.0, min(1.0, confidence_score))

        recommendations = payload.get("recommendations", [])
        if not isinstance(recommendations, list):
            recommendations = [str(recommendations)] if recommendations else []

        probabilities = self._normalize_probability_map(
            payload.get("all_probabilities") or payload.get("probabilities"),
            classification,
            confidence_score,
        )

        if classification == "Uncertain" and confidence_score > 0.7:
            confidence_score = 0.58

        return {
            "status": "success",
            "image_path": image_path,
            "provider": provider,
            "classification": classification,
            "confidence_score": float(confidence_score),
            "confidence": float(confidence_score),
            "findings": findings,
            "finding": findings,
            "clinical_note": clinical_note,
            "recommendations": recommendations,
            "all_probabilities": probabilities,
            "probabilities": probabilities,
        }

    def _gemini_analyze(self, image_path: str, image: Image.Image) -> Dict[str, Any]:
        if not genai:
            raise RuntimeError("Gemini SDK is not installed")

        if not self._has_valid_gemini_key():
            raise RuntimeError("AI_PROVIDER is gemini but GEMINI_API_KEY is missing/invalid.")

        prompt = self._build_prompt()
        model = genai.GenerativeModel(self.gemini_model)
        response = model.generate_content(
            [prompt, image],
            generation_config={"temperature": 0.2, "max_output_tokens": 800},
        )
        result = _extract_json((getattr(response, "text", "") or "{}").strip())
        return self._build_result(image_path, result, "gemini")

    def _groq_analyze(self, image_path: str, image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        if not Groq or not self._has_valid_groq_key() or not self.groq_client:
            raise RuntimeError("Groq vision backup is not configured.")

        prompt = self._build_prompt()
        data_url = f"data:{mime_type or 'image/jpeg'};base64,{base64.b64encode(image_bytes).decode('ascii')}"

        completion = self.groq_client.chat.completions.create(
            model=self.groq_vision_model,
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=800,
            messages=[
                {"role": "system", "content": "You return strict JSON only."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url,
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
        )
        result = _extract_json((completion.choices[0].message.content or "{}").strip())
        return self._build_result(image_path, result, "groq")

    def analyze_xray(self, image_path: str) -> Dict[str, Any]:
        """Analyze an X-ray image using an external vision API."""
        try:
            image_bytes, mime_type, image = self._load_image(image_path)
            last_error: Optional[Exception] = None

            for provider in self._provider_order():
                try:
                    if provider == "groq":
                        return self._groq_analyze(image_path, image_bytes, mime_type)
                    return self._gemini_analyze(image_path, image)
                except Exception as exc:
                    last_error = exc

            raise last_error or RuntimeError("No X-ray vision provider is configured.")

        except Exception as exc:
            return {
                "status": "error",
                "message": str(exc),
                "image_path": image_path,
                "classification": "Error",
                "confidence_score": 0.0,
                "confidence": 0.0,
                "findings": "Unable to process image",
                "finding": "Unable to process image",
                "clinical_note": "Unable to process image",
                "recommendations": [],
                "all_probabilities": {},
                "probabilities": {},
            }

    def batch_analyze(self, image_paths: list) -> list:
        """Analyze multiple X-ray images."""
        results = []
        for image_path in image_paths:
            results.append(self.analyze_xray(image_path))
        return results