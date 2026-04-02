"""Medical report summarization using Gemini/local logic"""
import os
import json
import re
import base64
from typing import Dict, Any

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

class ReportSummarizer:
    """Summarize medical reports using Gemini or local logic"""
    
    def __init__(self, api_key: str = None):
        self.provider = os.getenv("AI_PROVIDER", "local").lower()
        self.backup_provider = os.getenv("BACKUP_PROVIDER", "").lower()
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.groq_vision_model = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        self.groq_client = None
        self._resolved_gemini_model = None

        if self.provider == "gemini" and genai and self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)

        if self._has_valid_groq_key() and Groq:
            self.groq_client = Groq(api_key=self.groq_api_key)

    def _candidate_gemini_models(self):
        candidates = [
            (self.gemini_model or "").strip(),
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
        ]
        seen = set()
        ordered = []
        for name in candidates:
            if not name or name in seen:
                continue
            seen.add(name)
            ordered.append(name)
        return ordered

    def _dynamic_gemini_models(self):
        if not genai:
            return []
        discovered = []
        try:
            for model in genai.list_models():
                methods = getattr(model, "supported_generation_methods", []) or []
                if "generateContent" not in methods:
                    continue
                raw_name = getattr(model, "name", "")
                if not raw_name:
                    continue
                # API returns names like "models/gemini-2.0-flash".
                discovered.append(raw_name.split("/", 1)[-1])
        except Exception:
            return []

        seen = set()
        ordered = []
        for name in discovered:
            if name in seen:
                continue
            seen.add(name)
            ordered.append(name)
        return ordered

    def _generate_with_gemini_fallback(self, contents, generation_config):
        if not genai:
            raise RuntimeError("Gemini SDK is not installed")

        tried = set()
        model_order = []

        if self._resolved_gemini_model:
            model_order.append(self._resolved_gemini_model)
        model_order.extend(self._candidate_gemini_models())
        model_order.extend(self._dynamic_gemini_models())

        last_error = None
        for model_name in model_order:
            if model_name in tried:
                continue
            tried.add(model_name)

            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(contents, generation_config=generation_config)
                self._resolved_gemini_model = model_name
                self.gemini_model = model_name
                return response
            except Exception as exc:
                last_error = exc
                msg = str(exc).lower()
                is_model_mismatch = (
                    "not found" in msg
                    or "not supported" in msg
                    or "404" in msg
                    or "unknown model" in msg
                )
                if is_model_mismatch:
                    continue
                raise

        if last_error:
            raise last_error
        raise RuntimeError("No Gemini models available for generateContent.")

    def _has_valid_gemini_key(self) -> bool:
        if not self.gemini_api_key:
            return False
        key = self.gemini_api_key.strip()
        invalid_values = {
            "",
            "your_gemini_api_key_here",
            "your_api_key_here",
        }
        return key not in invalid_values

    def _has_valid_groq_key(self) -> bool:
        if not self.groq_api_key:
            return False
        key = self.groq_api_key.strip()
        invalid_values = {
            "",
            "your_groq_api_key_here",
            "your_api_key_here",
        }
        return key not in invalid_values

    def _should_use_groq_backup(self) -> bool:
        return self.backup_provider == "groq" and self._has_valid_groq_key() and self.groq_client is not None

    def _groq_summarize(self, report_text: str, report_type: str) -> Dict[str, Any]:
        if not Groq or not self._has_valid_groq_key() or not self.groq_client:
            return {
                "status": "error",
                "message": "Groq backup is not configured.",
                "summary": "",
                "key_findings": [],
                "abnormalities": [],
                "recommendations": [],
            }

        prompt = f"""You are a medical report analyzer. Analyze the following {report_type} report and provide:
1. A concise summary (2-3 sentences)
2. Key findings (bullet points)
3. Abnormalities or concerns (if any)
4. Recommended actions

Medical Report:
{report_text}

Respond ONLY in JSON format with keys: summary, key_findings, abnormalities, recommendations"""

        try:
            completion = self.groq_client.chat.completions.create(
                model=self.groq_model,
                response_format={"type": "json_object"},
                temperature=0.4,
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": "You return strict JSON only."},
                    {"role": "user", "content": prompt},
                ],
            )
            text = completion.choices[0].message.content or "{}"
            result = _extract_json(text)

            return {
                "status": "success",
                "summary": result.get("summary", ""),
                "key_findings": result.get("key_findings", []),
                "abnormalities": result.get("abnormalities", []),
                "recommendations": result.get("recommendations", []),
                "patient_friendly_explanation": "",
                "severity_level": "moderate",
                "possible_causes": [],
                "suggested_next_tests": [],
                "sections": {
                    "summary": result.get("summary", ""),
                    "key_issues": result.get("abnormalities", []),
                    "abnormal_values": result.get("key_findings", []),
                    "recommendations": result.get("recommendations", []),
                },
                "report_type": report_type,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "summary": "",
                "key_findings": [],
                "abnormalities": [],
                "recommendations": [],
            }

    def _groq_summarize_from_file(self, file_bytes: bytes, mime_type: str, report_type: str) -> Dict[str, Any]:
        if not Groq or not self._has_valid_groq_key() or not self.groq_client:
            return {
                "status": "error",
                "message": "Groq backup is not configured.",
                "summary": "",
                "key_findings": [],
                "abnormalities": [],
                "recommendations": [],
            }

        mime = (mime_type or "application/octet-stream").lower()
        if not (mime.startswith("image/") or mime == "application/pdf"):
            return {
                "status": "error",
                "message": f"Unsupported file type for Groq file fallback: {mime}",
                "summary": "",
                "key_findings": [],
                "abnormalities": [],
                "recommendations": [],
            }

        prompt = f"""You are a medical report analyzer.
Analyze this uploaded {report_type} report and respond ONLY in JSON with keys:
summary, key_findings, abnormalities, recommendations.

Rules:
- Ignore IDs, registration numbers, addresses, and dates unless clinically relevant.
- Focus on medical parameters and their normal/abnormal status.
- If a value is abnormal, include it in key_findings and abnormalities.
- Do not claim \"no abnormalities\" when any abnormal value exists.
"""

        try:
            b64 = base64.b64encode(file_bytes).decode("ascii")
            data_url = f"data:{mime};base64,{b64}"
            completion = self.groq_client.chat.completions.create(
                model=self.groq_vision_model,
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=1000,
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
            text = completion.choices[0].message.content or "{}"
            result = _extract_json(text)

            return {
                "status": "success",
                "summary": result.get("summary", ""),
                "key_findings": result.get("key_findings", []),
                "abnormalities": result.get("abnormalities", []),
                "recommendations": result.get("recommendations", []),
                "report_type": report_type,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "summary": "",
                "key_findings": [],
                "abnormalities": [],
                "recommendations": [],
            }

    def _gemini_summarize(self, report_text: str, report_type: str) -> Dict[str, Any]:
        if not genai:
            return {
                "status": "error",
                "message": "Gemini SDK is not installed. Install google-generativeai.",
                "summary": "",
                "key_findings": [],
                "abnormalities": [],
                "recommendations": [],
                "patient_friendly_explanation": "",
                "severity_level": "low",
                "possible_causes": [],
                "suggested_next_tests": [],
                "sections": {
                    "summary": "",
                    "key_issues": [],
                    "abnormal_values": [],
                    "recommendations": [],
                },
            }

        if not self._has_valid_gemini_key():
            return {
                "status": "error",
                "message": "AI_PROVIDER is gemini but GEMINI_API_KEY is missing/invalid.",
                "summary": "",
                "key_findings": [],
                "abnormalities": [],
                "recommendations": [],
                "patient_friendly_explanation": "",
                "severity_level": "low",
                "possible_causes": [],
                "suggested_next_tests": [],
                "sections": {
                    "summary": "",
                    "key_issues": [],
                    "abnormal_values": [],
                    "recommendations": [],
                },
            }

        prompt = f"""You are a medical report analyzer. Analyze the following {report_type} report and provide:
1. A concise summary (2-3 sentences)
2. Key findings (bullet points)
3. Abnormalities or concerns (if any)
4. Recommended actions

Medical Report:
{report_text}

Respond ONLY in JSON format with keys: summary, key_findings, abnormalities, recommendations"""

        try:
            response = self._generate_with_gemini_fallback(
                prompt,
                generation_config={"temperature": 0.4, "max_output_tokens": 1000},
            )
            result = _extract_json((response.text or "{}"))

            return {
                "status": "success",
                "summary": result.get("summary", ""),
                "key_findings": result.get("key_findings", []),
                "abnormalities": result.get("abnormalities", []),
                "recommendations": result.get("recommendations", []),
                "patient_friendly_explanation": "",
                "severity_level": "moderate",
                "possible_causes": [],
                "suggested_next_tests": [],
                "sections": {
                    "summary": result.get("summary", ""),
                    "key_issues": result.get("abnormalities", []),
                    "abnormal_values": result.get("key_findings", []),
                    "recommendations": result.get("recommendations", []),
                },
                "report_type": report_type
            }
        except Exception as e:
            if self._should_use_groq_backup():
                groq_result = self._groq_summarize(report_text, report_type)
                if groq_result.get("status") == "success":
                    return groq_result
            return {
                "status": "error",
                "message": str(e),
                "summary": "",
                "key_findings": [],
                "abnormalities": [],
                "recommendations": [],
                "patient_friendly_explanation": "",
                "severity_level": "low",
                "possible_causes": [],
                "suggested_next_tests": [],
                "sections": {
                    "summary": "",
                    "key_issues": [],
                    "abnormal_values": [],
                    "recommendations": [],
                },
            }

    def summarize_report_from_file(self, file_bytes: bytes, mime_type: str, report_type: str = "general") -> Dict[str, Any]:
        """Summarize report directly from image/PDF using Gemini multimodal input."""
        if self.provider != "gemini":
            return {
                "status": "error",
                "message": "File upload analysis is available only when AI_PROVIDER=gemini.",
                "summary": "",
                "key_findings": [],
                "abnormalities": [],
                "recommendations": [],
            }

        if not genai:
            return {
                "status": "error",
                "message": "Gemini SDK is not installed. Install google-generativeai.",
                "summary": "",
                "key_findings": [],
                "abnormalities": [],
                "recommendations": [],
            }

        if not self._has_valid_gemini_key():
            return {
                "status": "error",
                "message": "AI_PROVIDER is gemini but GEMINI_API_KEY is missing/invalid.",
                "summary": "",
                "key_findings": [],
                "abnormalities": [],
                "recommendations": [],
            }

        prompt = f"""You are a medical report analyzer.
Analyze this uploaded {report_type} report and respond ONLY in JSON with keys:
summary, key_findings, abnormalities, recommendations.

Rules:
- Ignore IDs, registration numbers, addresses, and dates unless clinically relevant.
- Focus on medical parameters and their normal/abnormal status.
- If a value is abnormal, include it in key_findings and abnormalities.
- Do not claim "no abnormalities" when any abnormal value exists.
"""

        try:
            file_part = {
                "mime_type": mime_type or "application/octet-stream",
                "data": file_bytes,
            }
            response = self._generate_with_gemini_fallback(
                [file_part, prompt],
                generation_config={"temperature": 0.3, "max_output_tokens": 1000},
            )
            result = _extract_json((response.text or "{}"))
            return {
                "status": "success",
                "summary": result.get("summary", ""),
                "key_findings": result.get("key_findings", []),
                "abnormalities": result.get("abnormalities", []),
                "recommendations": result.get("recommendations", []),
                "report_type": report_type,
            }
        except Exception as e:
            if self._should_use_groq_backup():
                groq_file_result = self._groq_summarize_from_file(file_bytes, mime_type, report_type)
                if groq_file_result.get("status") == "success":
                    return groq_file_result

                mime = (mime_type or "").lower()
                is_text_like = mime.startswith("text/") or mime in {
                    "application/json",
                    "application/xml",
                    "application/csv",
                    "text/csv",
                }
                if is_text_like:
                    extracted_text = file_bytes.decode("utf-8", errors="ignore").strip()
                    if extracted_text:
                        groq_text_result = self._groq_summarize(extracted_text, report_type)
                        if groq_text_result.get("status") == "success":
                            return groq_text_result

            return {
                "status": "error",
                "message": str(e),
                "summary": "",
                "key_findings": [],
                "abnormalities": [],
                "recommendations": [],
            }

    def _lab_reference_ranges(self) -> Dict[str, tuple]:
        return {
            "hemoglobin": (13.5, 17.5),
            "rbc": (4.7, 6.1),
            "wbc": (4000, 11000),
            "platelets": (150000, 450000),
            "mchc": (32, 36),
            "mch": (27, 33),
            "mcv": (80, 100),
            "esr": (0, 20),
            "neutrophils": (40, 70),
            "lymphocytes": (20, 40),
        }

    def _default_range_for(self, canonical: str, value: float):
        refs = self._lab_reference_ranges()
        if canonical != "platelets":
            return refs.get(canonical, (None, None))

        # Platelets can be written as 150000-450000 or 150-450 (x10^3/uL style).
        if value < 1000:
            return (150, 450)
        return (150000, 450000)

    def _canonical_lab_name(self, raw_name: str) -> str:
        n = raw_name.lower().strip()
        if "hemoglobin" in n or n in {"hb", "hb%"}:
            return "hemoglobin"
        if "rbc" in n:
            return "rbc"
        if "wbc" in n:
            return "wbc"
        if "platelet" in n:
            return "platelets"
        if "mchc" in n:
            return "mchc"
        if re.search(r"\bmch\b", n):
            return "mch"
        if "mcv" in n:
            return "mcv"
        if "esr" in n:
            return "esr"
        if "neutrophil" in n:
            return "neutrophils"
        if "lymphocyte" in n:
            return "lymphocytes"
        return ""

    def _display_lab_name(self, canonical: str) -> str:
        labels = {
            "hemoglobin": "Hemoglobin (Hb)",
            "rbc": "RBC Count",
            "wbc": "WBC Count",
            "platelets": "Platelets",
            "mchc": "MCHC",
            "mch": "MCH",
            "mcv": "MCV",
            "esr": "ESR",
            "neutrophils": "Neutrophils",
            "lymphocytes": "Lymphocytes",
        }
        return labels.get(canonical, canonical.upper())

    def _preclean_lab_text(self, report_text: str) -> str:
        """Normalize OCR-heavy report text so lab labels become parseable lines."""
        text = report_text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("–", "-").replace("—", "-")
        text = re.sub(r"[ \t]+", " ", text)

        # Common OCR term normalization for CBC-related fields.
        replacements = {
            r"(?i)hemogiobin|haemoglobin": "Hemoglobin",
            r"(?i)piatelets|plateiets": "Platelets",
            r"(?i)iymphocytes": "Lymphocytes",
            r"(?i)neutrophiis": "Neutrophils",
            r"(?i)eosinophiis": "Eosinophils",
            r"(?i)differential\s*count": "Differential Count",
            r"(?i)normal\s*[:;]": "Normal:",
        }
        for pattern, repl in replacements.items():
            text = re.sub(pattern, repl, text)

        labels = (
            "Hemoglobin|Hb|RBC Count|WBC Count|Platelets|MCHC|MCH|MCV|ESR|"
            "Neutrophils|Lymphocytes|Monocytes|Eosinophils|Impression"
        )
        text = re.sub(r"\s+(?=(?:" + labels + r")\s*:?)", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def _extract_lab_measurements(self, report_text: str) -> list:
        text = self._preclean_lab_text(report_text)
        results = []
        seen = set()

        # Parse line-wise, with optional colon after label to tolerate OCR formatting drift.
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            m = re.search(
                r"^([A-Za-z][A-Za-z /()%-]{1,50})\s*:??\s*([<>]?\d[\d,]*(?:\.\d+)?)",
                line,
            )
            if not m:
                continue

            raw_name = m.group(1).strip()
            canonical = self._canonical_lab_name(raw_name)
            if not canonical or canonical in seen:
                continue

            value = float(m.group(2).replace(",", "").replace(">", "").replace("<", ""))

            range_match = re.search(
                r"\(\s*Normal\s*:\s*(\d+(?:[\.,]\d+)?)\s*[\-\u2013\u2014]\s*(\d+(?:[\.,]\d+)?)",
                line,
                flags=re.IGNORECASE,
            )
            if range_match:
                low = float(range_match.group(1).replace(",", ""))
                high = float(range_match.group(2).replace(",", ""))
            else:
                low, high = self._default_range_for(canonical, value)

            direction = "unknown"
            if low is not None and high is not None:
                if value < low:
                    direction = "low"
                elif value > high:
                    direction = "high"
                else:
                    direction = "normal"

            results.append({
                "name": self._display_lab_name(canonical),
                "canonical": canonical,
                "value": value,
                "low": low,
                "high": high,
                "direction": direction,
                "source_line": line,
            })
            seen.add(canonical)

        return results

    def _extract_cbc_flags(self, report_text: str) -> list:
        """Return only abnormal lab values from recognized CBC-related parameters."""
        values = self._extract_lab_measurements(report_text)
        return [v for v in values if v.get("direction") in {"low", "high"}]

    def _cbc_impressions(self, flags: list, lower_text: str) -> list:
        """Generate high-level impressions from CBC abnormalities."""
        names = {f["name"].lower(): f for f in flags}
        impressions = []

        hb_low = any("hemoglobin" in n and v["direction"] == "low" for n, v in names.items())
        rbc_low = any("rbc" in n and v["direction"] == "low" for n, v in names.items())
        wbc_high = any("wbc" in n and v["direction"] == "high" for n, v in names.items())
        neut_high = any("neutrophils" in n and v["direction"] == "high" for n, v in names.items())
        esr_high = any("esr" in n and v["direction"] == "high" for n, v in names.items())
        mchc_low = any("mchc" in n and v["direction"] == "low" for n, v in names.items())

        if hb_low or rbc_low:
            impressions.append("mild-to-moderate anemia pattern")
        if mchc_low:
            impressions.append("low MCHC indicating possible mild hypochromic anemia")
        if wbc_high and neut_high:
            impressions.append("leukocytosis with neutrophilia, compatible with bacterial infection/inflammation")
        elif wbc_high:
            impressions.append("leukocytosis suggesting active infection/inflammation")
        if esr_high:
            impressions.append("elevated ESR consistent with inflammatory activity")

        return impressions

    def _severity_level(self, flags: list, lower_text: str) -> str:
        """Estimate severity for project-friendly triage messaging."""
        if not flags:
            return "low"

        by_name = {f.get("canonical", f["name"].lower()): f for f in flags}
        hb = by_name.get("hemoglobin")
        wbc = by_name.get("wbc")

        # Deterministic triage rules to avoid false high-severity from OCR text noise.
        if hb and hb.get("direction") == "low" and hb.get("value", 99) < 8:
            return "high"
        if wbc and wbc.get("direction") == "high" and wbc.get("value", 0) > 20000:
            return "high"

        mild_indices = {"mchc", "mch", "mcv"}
        if all(f.get("canonical") in mild_indices for f in flags):
            return "low"

        return "moderate"

    def _patient_friendly_explanation(self, flags: list, lower_text: str) -> str:
        """Generate a plain-language explanation suitable for patients."""
        names = {f["name"].lower(): f for f in flags}
        explanation_lines = []

        hb_low = any("hemoglobin" in n and v["direction"] == "low" for n, v in names.items())
        rbc_low = any("rbc" in n and v["direction"] == "low" for n, v in names.items())
        wbc_high = any("wbc" in n and v["direction"] == "high" for n, v in names.items())
        mchc_low = any("mchc" in n and v["direction"] == "low" for n, v in names.items())

        if hb_low or rbc_low:
            explanation_lines.append(
                "Your blood report shows low hemoglobin or red blood cell levels, which can cause weakness or fatigue (anemia)."
            )
        if wbc_high or "infection" in lower_text:
            explanation_lines.append(
                "Your white blood cell count appears increased, which may indicate your body is fighting an infection or inflammation."
            )
        if mchc_low:
            explanation_lines.append(
                "One index called MCHC is low, which may suggest early iron deficiency or mild hypochromic anemia."
            )

        if not explanation_lines:
            explanation_lines.append(
                "The report has some findings that should be reviewed with your clinician for personalized interpretation."
            )

        return " ".join(explanation_lines)

    def _possible_causes(self, flags: list, lower_text: str) -> list:
        """Suggest likely causes from detected patterns."""
        names = {f["name"].lower(): f for f in flags}
        causes = []

        hb_low = any("hemoglobin" in n and v["direction"] == "low" for n, v in names.items())
        rbc_low = any("rbc" in n and v["direction"] == "low" for n, v in names.items())
        wbc_high = any("wbc" in n and v["direction"] == "high" for n, v in names.items())
        esr_high = any("esr" in n and v["direction"] == "high" for n, v in names.items())
        mchc_low = any("mchc" in n and v["direction"] == "low" for n, v in names.items())

        if hb_low or rbc_low:
            causes.append("Iron deficiency anemia")
        if mchc_low:
            causes.append("Early-stage anemia")
        if wbc_high or "infection" in lower_text:
            causes.append("Recent or ongoing infection")
        if esr_high or "inflammatory" in lower_text:
            causes.append("Inflammatory condition")

        return list(dict.fromkeys(causes))

    def _suggested_next_tests(self, flags: list, lower_text: str) -> list:
        """Recommend practical follow-up tests."""
        names = {f["name"].lower(): f for f in flags}
        tests = []

        hb_low = any("hemoglobin" in n and v["direction"] == "low" for n, v in names.items())
        rbc_low = any("rbc" in n and v["direction"] == "low" for n, v in names.items())
        wbc_high = any("wbc" in n and v["direction"] == "high" for n, v in names.items())
        esr_high = any("esr" in n and v["direction"] == "high" for n, v in names.items())
        mchc_low = any("mchc" in n and v["direction"] == "low" for n, v in names.items())

        if hb_low or rbc_low:
            tests.append("Iron studies (Serum Ferritin)")
            tests.append("Peripheral smear")
        if mchc_low:
            tests.append("Serum iron")
            tests.append("Ferritin test")
        if wbc_high or esr_high or "infection" in lower_text or "inflammatory" in lower_text:
            tests.append("CRP / ESR (inflammation markers)")
        if wbc_high:
            tests.append("Repeat CBC with differential")

        return list(dict.fromkeys(tests))

    def _local_summarize(self, report_text: str, report_type: str) -> Dict[str, Any]:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", report_text.strip()) if s.strip()]
        if not sentences:
            return {
                "status": "success",
                "summary": "No report text provided.",
                "key_findings": [],
                "abnormalities": [],
                "recommendations": ["Provide report text for analysis."],
                "report_type": report_type,
            }

        lower_text = report_text.lower()
        lab_values = self._extract_lab_measurements(report_text)
        cbc_flags = [v for v in lab_values if v.get("direction") in {"low", "high"}]
        cbc_impressions = self._cbc_impressions(cbc_flags, lower_text)

        words = re.findall(r"\b[a-zA-Z]{3,}\b", report_text.lower())
        stopwords = {
            "the", "and", "for", "with", "that", "this", "from", "were", "are", "was", "has", "have",
            "had", "not", "but", "patient", "report", "normal", "within", "into", "than", "then", "also"
        }
        freq = {}
        for w in words:
            if w not in stopwords:
                freq[w] = freq.get(w, 0) + 1

        scored = []
        for s in sentences:
            tokens = re.findall(r"\b[a-zA-Z]{3,}\b", s.lower())
            score = sum(freq.get(t, 0) for t in tokens)
            scored.append((score, s))
        top_summary = [s for _, s in sorted(scored, key=lambda x: x[0], reverse=True)[:3]]
        impression_match = re.search(r"impression\s*:\s*(.+)", report_text, flags=re.IGNORECASE)
        impression_text = impression_match.group(1).strip() if impression_match else ""
        summary_sentences = []
        if cbc_impressions:
            summary_sentences.append("Detected " + "; ".join(cbc_impressions) + ".")
        elif cbc_flags:
            summary_sentences.append("Blood report shows limited abnormalities without critical danger signs.")
        else:
            summary_sentences.append("Blood report is largely normal with no major abnormalities detected.")

        if impression_text:
            summary_sentences.append("Report impression: " + impression_text)
        summary = " ".join(summary_sentences)[:900]

        key_findings = []
        display_order = ["hemoglobin", "wbc", "platelets", "rbc", "mchc", "mch", "mcv", "esr"]
        by_canonical = {v["canonical"]: v for v in lab_values}
        for key in display_order:
            v = by_canonical.get(key)
            if not v:
                continue
            if v["direction"] == "normal":
                key_findings.append(f"{v['name']}: {v['value']} (normal)")
            elif v["direction"] in {"low", "high"}:
                key_findings.append(f"{v['name']}: {v['value']} ({v['direction']} vs normal {v['low']}-{v['high']})")
            if len(key_findings) >= 6:
                break
        if not key_findings:
            if report_type.lower() in {"laboratory", "lab", "cbc"}:
                key_findings = [
                    "Could not confidently extract structured lab values from OCR text. Please review extracted text and correct key lines (Hb, WBC, Platelets, MCHC)."
                ]
            else:
                key_findings = top_summary[:3]

        abnormalities = []
        abnormalities.extend(cbc_impressions)
        abnormalities = list(dict.fromkeys(abnormalities))
        severity = self._severity_level(cbc_flags, lower_text)
        patient_friendly_explanation = self._patient_friendly_explanation(cbc_flags, lower_text)
        possible_causes = self._possible_causes(cbc_flags, lower_text)
        suggested_next_tests = self._suggested_next_tests(cbc_flags, lower_text)

        if abnormalities:
            recommendations = [
                "Follow up with a licensed clinician for confirmatory interpretation.",
                "Correlate findings with patient symptoms and prior reports.",
            ]
            if any("infection" in x.lower() or "leukocyt" in x.lower() or "esr" in x.lower() for x in cbc_impressions):
                recommendations.append("Consider repeat CBC and targeted infection workup as clinically indicated.")
            if any("mchc" in x.lower() or "anemia" in x.lower() for x in cbc_impressions):
                recommendations.append("Maintain iron-rich diet and discuss iron profile testing with your clinician.")
        else:
            recommendations = [
                "No clear abnormal flags detected by local heuristic mode.",
                "Use clinician review for final diagnosis.",
            ]

        return {
            "status": "success",
            "summary": summary,
            "key_findings": key_findings,
            "abnormalities": abnormalities,
            "recommendations": recommendations,
            "patient_friendly_explanation": patient_friendly_explanation,
            "severity_level": severity,
            "possible_causes": possible_causes,
            "suggested_next_tests": suggested_next_tests,
            "sections": {
                "summary": summary,
                "key_issues": abnormalities,
                "abnormal_values": key_findings,
                "recommendations": recommendations,
            },
            "report_type": report_type,
        }
        
    def summarize_report(self, report_text: str, report_type: str = "general") -> Dict[str, Any]:
        """
        Summarize a medical report
        
        Args:
            report_text: Full medical report text
            report_type: Type of report (pathology, radiology, lab, etc.)
            
        Returns:
            Dictionary with summary, key findings, and analysis
        """
        if self.provider == "gemini":
            return self._gemini_summarize(report_text, report_type)

        return self._local_summarize(report_text, report_type)

    def batch_summarize(self, reports: list) -> list:
        """
        Summarize multiple reports
        
        Args:
            reports: List of report dictionaries with 'text' and 'type' keys
            
        Returns:
            List of summarized results
        """
        results = []
        for report in reports:
            result = self.summarize_report(
                report.get("text", ""),
                report.get("type", "general")
            )
            results.append(result)
        return results
