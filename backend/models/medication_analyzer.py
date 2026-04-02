"""Medication review analyzer using OpenAI"""
import os
import json
import re
from typing import Dict, List, Any

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

class MedicationAnalyzer:
    """Analyze medication reviews for sentiment and side effects"""
    
    def __init__(self, api_key: str = None):
        self.provider = os.getenv("AI_PROVIDER", "local").lower()
        self.backup_provider = os.getenv("BACKUP_PROVIDER", "").lower()
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
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

    def _infer_actual_use(self, medication_name: str, review_text: str) -> str:
        name = (medication_name or "").lower()
        text = (review_text or "").lower()

        known_uses = {
            "amlodipine": "Treats high blood pressure (hypertension).",
            "metformin": "Helps control blood sugar in type 2 diabetes.",
            "atorvastatin": "Lowers cholesterol and cardiovascular risk.",
            "losartan": "Treats high blood pressure and helps protect kidneys.",
            "paracetamol": "Relieves pain and reduces fever.",
            "acetaminophen": "Relieves pain and reduces fever.",
            "ibuprofen": "Relieves pain, inflammation, and fever.",
            "azithromycin": "Antibiotic used for bacterial infections.",
            "amoxicillin": "Antibiotic used for bacterial infections.",
            "omeprazole": "Reduces stomach acid for reflux or ulcers.",
            "pantoprazole": "Reduces stomach acid for reflux or ulcers.",
            "cetirizine": "Relieves allergy symptoms.",
            "levocetirizine": "Relieves allergy symptoms.",
        }

        for med, use in known_uses.items():
            if med in name:
                return use

        keyword_uses = [
            ("blood pressure|hypertension|bp", "Likely used for high blood pressure."),
            ("sugar|diabetes|glucose", "Likely used for blood sugar control."),
            ("cholesterol|lipid|statin", "Likely used for cholesterol management."),
            ("pain|headache|fever|body ache", "Likely used for pain or fever relief."),
            ("infection|antibiotic|bacterial", "Likely used to treat a bacterial infection."),
            ("acidity|reflux|heartburn|gastric", "Likely used for acidity or reflux symptoms."),
            ("allergy|sneezing|itching|hives", "Likely used for allergy symptoms."),
        ]

        for pattern, use in keyword_uses:
            if re.search(pattern, text):
                return use

        return "General therapeutic use; confirm with prescription guidance."

    def _groq_analyze(self, review_text: str, medication_name: str) -> Dict[str, Any]:
        if not Groq or not self._has_valid_groq_key() or not self.groq_client:
            return {
                "status": "error",
                "message": "Groq backup is not configured.",
                "medication_name": medication_name,
                "actual_use": "",
                "sentiment_score": 0,
                "side_effects": [],
                "effectiveness_rating": 0,
                "impression": "",
                "recommendation": "",
            }

        prompt = f"""Analyze this medication review and extract:
1. Sentiment score (-1 to 1, where -1 is very negative, 0 is neutral, 1 is very positive)
2. Reported side effects (list)
3. Effectiveness rating (0-5)
4. Overall impression (brief)
5. Recommendation (continue, monitor, discontinue)
6. Actual use (what this medicine is typically used for)

Medication: {medication_name}
Review: {review_text}

Respond ONLY in JSON format with keys: sentiment_score, side_effects, effectiveness_rating, impression, recommendation, actual_use"""

        try:
            completion = self.groq_client.chat.completions.create(
                model=self.groq_model,
                response_format={"type": "json_object"},
                temperature=0.4,
                max_tokens=500,
                messages=[
                    {"role": "system", "content": "You return strict JSON only."},
                    {"role": "user", "content": prompt},
                ],
            )
            text = completion.choices[0].message.content or "{}"
            result = _extract_json(text)

            return {
                "status": "success",
                "medication_name": medication_name,
                "actual_use": result.get("actual_use", self._infer_actual_use(medication_name, review_text)),
                "sentiment_score": float(result.get("sentiment_score", 0)),
                "side_effects": result.get("side_effects", []),
                "effectiveness_rating": float(result.get("effectiveness_rating", 0)),
                "impression": result.get("impression", ""),
                "recommendation": result.get("recommendation", ""),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "medication_name": medication_name,
                "actual_use": "",
                "sentiment_score": 0,
                "side_effects": [],
                "effectiveness_rating": 0,
                "impression": "",
                "recommendation": "",
            }

    def _gemini_analyze(self, review_text: str, medication_name: str) -> Dict[str, Any]:
        if not genai:
            return {
                "status": "error",
                "message": "Gemini SDK is not installed. Install google-generativeai.",
                "medication_name": medication_name,
                "actual_use": "",
                "sentiment_score": 0,
                "side_effects": [],
                "effectiveness_rating": 0,
                "impression": "",
                "recommendation": ""
            }

        if not self._has_valid_gemini_key():
            return {
                "status": "error",
                "message": "AI_PROVIDER is gemini but GEMINI_API_KEY is missing/invalid.",
                "medication_name": medication_name,
                "actual_use": "",
                "sentiment_score": 0,
                "side_effects": [],
                "effectiveness_rating": 0,
                "impression": "",
                "recommendation": ""
            }

        prompt = f"""Analyze this medication review and extract:
1. Sentiment score (-1 to 1, where -1 is very negative, 0 is neutral, 1 is very positive)
2. Reported side effects (list)
3. Effectiveness rating (0-5)
4. Overall impression (brief)
5. Recommendation (continue, monitor, discontinue)
6. Actual use (what this medicine is typically used for)

Medication: {medication_name}
Review: {review_text}

Respond ONLY in JSON format with keys: sentiment_score, side_effects, effectiveness_rating, impression, recommendation, actual_use"""

        try:
            response = self._generate_with_gemini_fallback(
                prompt,
                generation_config={"temperature": 0.4, "max_output_tokens": 500},
            )
            result = _extract_json((response.text or "{}"))
            return {
                "status": "success",
                "medication_name": medication_name,
                "actual_use": result.get("actual_use", self._infer_actual_use(medication_name, review_text)),
                "sentiment_score": float(result.get("sentiment_score", 0)),
                "side_effects": result.get("side_effects", []),
                "effectiveness_rating": float(result.get("effectiveness_rating", 0)),
                "impression": result.get("impression", ""),
                "recommendation": result.get("recommendation", ""),
            }
        except Exception as e:
            if self._should_use_groq_backup():
                groq_result = self._groq_analyze(review_text, medication_name)
                if groq_result.get("status") == "success":
                    return groq_result
            return {
                "status": "error",
                "message": str(e),
                "medication_name": medication_name,
                "actual_use": "",
                "sentiment_score": 0,
                "side_effects": [],
                "effectiveness_rating": 0,
                "impression": "",
                "recommendation": ""
            }

    def _local_analyze(self, review_text: str, medication_name: str) -> Dict[str, Any]:
        text = review_text.lower()
        positive_terms = {
            "helped", "effective", "improved", "better", "recommend", "good", "great", "excellent", "works", "relief"
        }
        negative_terms = {
            "worse", "bad", "severe", "pain", "nausea", "dizziness", "vomit", "headache", "rash", "stop", "discontinue"
        }

        tokens = re.findall(r"\b[a-zA-Z']+\b", text)
        pos = sum(1 for t in tokens if t in positive_terms)
        neg = sum(1 for t in tokens if t in negative_terms)
        sentiment_score = (pos - neg) / max(pos + neg, 1)
        sentiment_score = max(-1.0, min(1.0, sentiment_score))

        known_side_effects = [
            "nausea", "vomiting", "dizziness", "headache", "rash", "cough", "fatigue", "diarrhea",
            "constipation", "insomnia", "dry mouth", "stomach pain", "cramping", "angioedema"
        ]
        side_effects = [se for se in known_side_effects if se in text]

        effectiveness_rating = round(max(0.0, min(5.0, 2.5 + sentiment_score * 2.5)), 1)

        if sentiment_score > 0.3:
            recommendation = "continue"
            impression = "Overall positive patient sentiment in local heuristic mode."
        elif sentiment_score < -0.3:
            recommendation = "monitor"
            impression = "Overall negative patient sentiment in local heuristic mode."
        else:
            recommendation = "monitor"
            impression = "Mixed or neutral patient sentiment in local heuristic mode."

        if "angioedema" in side_effects:
            recommendation = "discontinue"

        return {
            "status": "success",
            "medication_name": medication_name,
            "actual_use": self._infer_actual_use(medication_name, review_text),
            "sentiment_score": float(sentiment_score),
            "side_effects": side_effects,
            "effectiveness_rating": float(effectiveness_rating),
            "impression": impression,
            "recommendation": recommendation,
        }
        
    def analyze_review(self, review_text: str, medication_name: str) -> Dict[str, Any]:
        """
        Analyze a medication review
        
        Args:
            review_text: Patient review of medication
            medication_name: Name of the medication
            
        Returns:
            Dictionary with sentiment, side effects, effectiveness
        """
        if self.provider == "gemini":
            return self._gemini_analyze(review_text, medication_name)

        return self._local_analyze(review_text, medication_name)

    def aggregate_reviews(self, reviews: List[Dict]) -> Dict[str, Any]:
        """
        Aggregate analysis of multiple reviews for a medication
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            Aggregated statistics and insights
        """
        analyses = []
        all_side_effects = {}
        sentiment_scores = []
        effectiveness_ratings = []
        
        for review in reviews:
            analysis = self.analyze_review(
                review.get("text", review.get("review_text", "")),
                review.get("medication_name", "")
            )
            analyses.append(analysis)
            
            if analysis["status"] == "success":
                sentiment_scores.append(analysis["sentiment_score"])
                effectiveness_ratings.append(analysis["effectiveness_rating"])
                
                # Aggregate side effects
                for se in analysis["side_effects"]:
                    all_side_effects[se] = all_side_effects.get(se, 0) + 1
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        avg_effectiveness = sum(effectiveness_ratings) / len(effectiveness_ratings) if effectiveness_ratings else 0
        
        # Sort side effects by frequency
        sorted_side_effects = sorted(all_side_effects.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_reviews_analyzed": len(reviews),
            "average_sentiment": avg_sentiment,
            "average_effectiveness": avg_effectiveness,
            "most_common_side_effects": sorted_side_effects[:5],
            "sentiment_distribution": {
                "positive": len([s for s in sentiment_scores if s > 0.3]),
                "neutral": len([s for s in sentiment_scores if -0.3 <= s <= 0.3]),
                "negative": len([s for s in sentiment_scores if s < -0.3])
            },
            "detailed_analyses": analyses
        }
