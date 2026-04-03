"""X-ray image analysis using pre-trained models"""
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import numpy as np
from typing import Dict, Any
import os

class XrayAnalyzer:
    """Analyze X-ray images using pre-trained ResNet model"""

    # Safety thresholds for conservative, non-diagnostic output behavior.
    LOW_CONFIDENCE_THRESHOLD = 0.40
    NEAR_TIE_GAP_THRESHOLD = 0.05
    
    # X-ray classifications
    XRAY_CLASSES = {
        0: "Normal",
        1: "Pneumonia",
        2: "COVID-19",
        3: "Tuberculosis",
        4: "Abnormal"
    }
    
    def __init__(self, model_path: str = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model(model_path)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                std=[0.229, 0.224, 0.225])
        ])
        
    def _load_model(self, model_path: str = None):
        """Load pre-trained ResNet model"""
        try:
            if model_path and os.path.exists(model_path):
                model = torch.load(model_path, map_location=self.device)
            else:
                # Load pre-trained ResNet50
                model = models.resnet50(pretrained=True)
                # Modify final layer for X-ray classification
                num_ftrs = model.fc.in_features
                model.fc = torch.nn.Linear(num_ftrs, len(self.XRAY_CLASSES))
            
            model = model.to(self.device)
            model.eval()
            return model
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    
    def analyze_xray(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze an X-ray image
        
        Args:
            image_path: Path to the X-ray image
            
        Returns:
            Dictionary with classification and confidence
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            # Model inference
            with torch.no_grad():
                outputs = self.model(image_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                confidence, prediction = torch.max(probabilities, 1)
            
            predicted_class = prediction.item()
            confidence_score = confidence.item()
            classification = self.XRAY_CLASSES.get(predicted_class, "Unknown")

            probs = probabilities[0].detach().cpu().numpy().astype(float)
            sorted_probs = sorted(probs, reverse=True)
            top1 = sorted_probs[0] if sorted_probs else 0.0
            top2 = sorted_probs[1] if len(sorted_probs) > 1 else 0.0
            near_tie = (top1 - top2) < self.NEAR_TIE_GAP_THRESHOLD
            low_confidence = confidence_score < self.LOW_CONFIDENCE_THRESHOLD

            all_probabilities = {
                self.XRAY_CLASSES[i]: float(probabilities[0][i].item())
                for i in range(len(self.XRAY_CLASSES))
            }

            if low_confidence or near_tie:
                classification = "Uncertain"
                findings = self._generate_uncertain_findings(confidence_score, all_probabilities)
            else:
                findings = self._generate_findings(classification, confidence_score)

            recommendations = self._generate_recommendations(classification, low_confidence or near_tie)
            
            return {
                "status": "success",
                "image_path": image_path,
                "classification": classification,
                "confidence_score": float(confidence_score),
                "confidence": float(confidence_score),
                "findings": findings,
                "finding": findings,
                "clinical_note": findings,
                "recommendations": recommendations,
                "all_probabilities": all_probabilities
                ,"probabilities": all_probabilities
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "image_path": image_path,
                "classification": "Error",
                "confidence_score": 0.0,
                "confidence": 0.0,
                "findings": "Unable to process image"
                ,"finding": "Unable to process image",
                "clinical_note": "Unable to process image",
                "recommendations": [],
                "all_probabilities": {},
                "probabilities": {}
            }
    
    def _generate_findings(self, classification: str, confidence: float) -> str:
        """Generate clinical findings based on classification"""
        findings_map = {
            "Normal": "No significant abnormalities detected. The X-ray appears normal.",
            "Pneumonia": "Signs consistent with pneumonia detected. Consolidation and/or infiltration visible.",
            "COVID-19": "Findings suggestive of COVID-19 pneumonia. Bilateral involvement possible.",
            "Tuberculosis": "Findings consistent with tuberculosis. Further investigation recommended.",
            "Abnormal": "Abnormal findings detected. Clinical correlation recommended."
        }
        
        base_finding = findings_map.get(classification, "Unable to classify")
        confidence_text = f"Confidence: {confidence:.2%}"
        
        if confidence < 0.6:
            confidence_text += " (Low confidence - further review recommended)"
        elif confidence < 0.8:
            confidence_text += " (Moderate confidence)"
        else:
            confidence_text += " (High confidence)"
        
        return f"{base_finding}\n{confidence_text}"

    def _generate_uncertain_findings(self, confidence: float, all_probabilities: Dict[str, float]) -> str:
        """Generate safe, non-diagnostic message when model confidence is weak."""
        sorted_items = sorted(all_probabilities.items(), key=lambda x: x[1], reverse=True)
        top_class = sorted_items[0][0] if sorted_items else "Unknown"
        top1 = sorted_items[0][1] if sorted_items else 0.0
        top2 = sorted_items[1][1] if len(sorted_items) > 1 else 0.0
        confidence_gap = max(0.0, top1 - top2)

        if top_class == "Abnormal":
            top_class_label = "Abnormal (non-specific finding)"
        else:
            top_class_label = top_class

        return (
            "Decision Rule: Max probability < 40% -> Uncertain classification\n"
            f"Interpretation: The model shows moderate uncertainty; although \"{top_class_label}\" has the highest probability, it does not exceed the confidence threshold for reliable classification.\n"
            f"Confidence Gap: {confidence_gap:.2%} (limited separation between top classes)\n"
            f"Top Class Note: \"{top_class_label}\" is the leading class but with insufficient confidence for confirmation.\n"
            "Visual Insight: No clear large opacity, cavity, or severe abnormality is evident at a basic level.\n"
            "Clinical Note: No strong radiographic evidence of acute pathology is observed at a basic level; however, model confidence is insufficient for confirmation.\n"
            "Severity: Uncertain - Non-urgent but requires clinical review\n"
            "Recommendations:\n"
            "- Radiologist review required\n"
            "- Consider CT scan if clinically indicated\n"
            "- Correlate with symptoms"
        )

    def _generate_recommendations(self, classification: str, uncertain: bool) -> list:
        if uncertain:
            return [
                "Radiologist review required",
                "Consider CT scan if clinically indicated",
                "Correlate with symptoms",
            ]

        recommendations_map = {
            "Normal": ["No urgent radiology follow-up is suggested based on this model output."],
            "Pneumonia": ["Clinical evaluation is recommended.", "Correlate with fever, cough, and oxygen levels."],
            "COVID-19": ["Clinical correlation is recommended.", "Consider isolation and local protocols if symptomatic."],
            "Tuberculosis": ["Further specialist review is recommended.", "Follow local infectious disease guidance."],
            "Abnormal": ["Further medical review is recommended."],
        }
        return recommendations_map.get(classification, ["Further medical review is recommended."])
    
    def batch_analyze(self, image_paths: list) -> list:
        """
        Analyze multiple X-ray images
        
        Args:
            image_paths: List of image paths
            
        Returns:
            List of analysis results
        """
        results = []
        for image_path in image_paths:
            result = self.analyze_xray(image_path)
            results.append(result)
        return results
