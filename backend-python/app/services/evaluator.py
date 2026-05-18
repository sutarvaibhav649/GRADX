# evaluator.py - COMPLETE FIXED VERSION

import math
import json
import nltk
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from nltk.tokenize import sent_tokenize, word_tokenize
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

# Download required NLTK data
for _pkg, _path in [('punkt', 'tokenizers/punkt'), ('punkt_tab', 'tokenizers/punkt_tab'), ('stopwords', 'corpora/stopwords')]:
    try:
        nltk.data.find(_path)
    except LookupError:
        nltk.download(_pkg, quiet=True)

# Load the embedding model
SEMANTIC_MODEL = SentenceTransformer("all-mpnet-base-v2")

def convert_to_serializable(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_to_serializable(item) for item in obj)
    return obj

class AdvancedEvaluator:
    def __init__(self):
        self.current_config = {}
        self.evaluation_history = []
        try:
            self.stop_words = set(nltk.corpus.stopwords.words('english'))
        except LookupError:
            self.stop_words = set()
    
    def auto_configure_from_model(self, model_answer: Dict, question_type: str = "conceptual",
                                   cheating_threshold: float = 0.4):
        """Automatically configure evaluator from model answer"""
        topic = model_answer.get("topic", "Extracted Model Answer")

        key_concepts = {}
        required_terms = set()

        answer_dict = model_answer.get("Answer", {})
        for section, text in answer_dict.items():
            if text and isinstance(text, str):
                words = text.lower().split()
                # len > 2 catches short but important technical terms: CPU, RAM, API, SQL, AI, ML
                important = [w for w in words if len(w) > 2 and w not in self.stop_words]
                key_concepts[section] = list(dict.fromkeys(important))[:15]
                for w in important[:8]:
                    required_terms.add(w)

        self.configure(
            topic=topic,
            key_concepts=key_concepts,
            required_terms=list(required_terms)[:20],
            question_type=question_type,
            cheating_threshold=cheating_threshold
        )
        return self.current_config
    
    def configure(self, topic: str, key_concepts: Dict, required_terms: List[str], 
                  question_type: str = "conceptual", cheating_threshold: float = 0.4):
        self.current_config = {
            'topic': topic,
            'key_concepts': key_concepts,
            'required_terms': required_terms,
            'question_type': question_type,
            'cheating_threshold': cheating_threshold
        }
        print(f"[OK] Evaluator configured for: {topic}")
    
    def semantic_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        v1 = SEMANTIC_MODEL.encode(text1, convert_to_tensor=True)
        v2 = SEMANTIC_MODEL.encode(text2, convert_to_tensor=True)
        result = cosine_similarity(v1.cpu().numpy().reshape(1, -1), v2.cpu().numpy().reshape(1, -1))[0][0]
        return float(result)
    
    def coherence_score(self, text: str) -> float:
        if not text:
            return 0.0
        sentences = sent_tokenize(text)
        if not sentences:
            return 0.0
        
        avg_len = np.mean([len(s.split()) for s in sentences])
        if avg_len < 4:
            return 0.5
        elif avg_len < 7:
            return 0.8
        return 1.0
    
    def concept_coverage(self, section: str, text: str) -> float:
        if section not in self.current_config.get('key_concepts', {}):
            return 0.5
        
        keywords = self.current_config['key_concepts'][section]
        if not keywords:
            return 1.0
        
        text_lower = text.lower()
        found = sum(1 for kw in keywords if kw.lower() in text_lower)
        result = min(1.0, found / len(keywords)) if keywords else 0.0
        return float(result)
    
    def detect_keyword_stuffing(self, text: str, section: str) -> Dict:
        if not text:
            return {'is_suspicious': False, 'keyword_density': 0.0}
        
        text_lower = text.lower()
        words = word_tokenize(text_lower)
        content_words = [w for w in words if w not in self.stop_words and w.isalpha()]
        
        keywords = self.current_config.get('key_concepts', {}).get(section, [])
        if not keywords:
            keywords = self.current_config.get('required_terms', [])
        
        keyword_count = sum(text_lower.count(kw.lower()) for kw in keywords)
        keyword_density = keyword_count / len(content_words) if content_words else 0.0
        
        is_suspicious = keyword_density > 0.4
        
        return {
            'is_suspicious': bool(is_suspicious),
            'keyword_density': float(round(keyword_density, 3)),
            'short_sentence_ratio': 0.0,
            'repetition_score': 0.0
        }
    
    def calculate_semantic_depth(self, student_text: str, model_text: str) -> Dict:
        if not student_text or not model_text:
            return {'depth_score': 0.0, 'coverage_score': 0.0, 'explanation_quality': 0.0}
        
        student_sentences = sent_tokenize(student_text)
        model_sentences = sent_tokenize(model_text)
        
        if not student_sentences:
            return {'depth_score': 0.0, 'coverage_score': 0.0, 'explanation_quality': 0.0}
        
        student_embeddings = SEMANTIC_MODEL.encode(student_sentences)
        model_embeddings = SEMANTIC_MODEL.encode(model_sentences)
        
        coverage_scores = []
        for model_emb in model_embeddings:
            similarities = [cosine_similarity(model_emb.reshape(1, -1), stud_emb.reshape(1, -1))[0][0] 
                          for stud_emb in student_embeddings]
            coverage_scores.append(max(similarities) if similarities else 0.0)
        coverage_score = float(np.mean(coverage_scores)) if coverage_scores else 0.0
        
        # A student who writes 60% of the model answer length scores full length_ratio.
        # This stops penalising concise-but-correct answers vs verbose model answers.
        length_ratio = min(1.0, len(student_text) / max(1, len(model_text) * 0.6))
        depth_score = (coverage_score * 0.7) + (length_ratio * 0.3)
        
        return {
            'depth_score': float(round(depth_score, 3)),
            'coverage_score': float(round(coverage_score, 3)),
            'explanation_quality': float(round(length_ratio, 3))
        }
    
    def evaluate_section(self, section: str, student_text: str, model_text: str,
                         max_marks: float, strictness: str = "moderate",
                         subject: str = "") -> Dict:
        safe_max = float(max_marks) if max_marks and max_marks > 0 else 1.0

        # Guard: blank answer — skip all expensive calls
        if not student_text or not student_text.strip():
            return {
                'marks_awarded': 0.0, 'max_marks': round(safe_max, 1), 'percentage': 0.0,
                'scores': {'semantic_similarity': 0.0, 'coherence': 0.0,
                           'concept_coverage': 0.0, 'depth_score': 0.0,
                           'llm_marks': None, 'local_marks': 0.0},
                'llm_evaluation': None,
                'cheating_detection': {'is_suspicious': False, 'keyword_density': 0.0,
                                       'short_sentence_ratio': 0.0, 'repetition_score': 0.0},
                'student_text': student_text, 'model_text': model_text
            }

        # ── Local scoring (fast, no API cost) ────────────────────────────────
        semantic_sim = self.semantic_similarity(student_text, model_text)
        coherence    = self.coherence_score(student_text)
        coverage     = self.concept_coverage(section, student_text)
        depth        = self.calculate_semantic_depth(student_text, model_text)
        cheating     = self.detect_keyword_stuffing(student_text, section)

        local_raw = (semantic_sim * 0.5) + (coverage * 0.25) + (depth['depth_score'] * 0.25)
        local_raw *= coherence
        if cheating['keyword_density'] > 0.75:
            local_raw *= 0.8
        local_marks = round(min(local_raw * safe_max, safe_max), 1)

        # ── LLM scoring (primary accuracy layer) ─────────────────────────────
        # Skip LLM only for answers that are clearly irrelevant (semantic < 0.08)
        # or extremely short (< 15 chars), to save API cost.
        llm_result = None
        llm_marks  = None
        try:
            from app.services.ocr_gemini import evaluate_section_with_llm
            if len(student_text.strip()) >= 15 and semantic_sim >= 0.08:
                llm_result = evaluate_section_with_llm(
                    section, student_text, model_text, safe_max, strictness, subject
                )
                if llm_result and llm_result.get('marks_awarded', -1) >= 0:
                    llm_marks = float(llm_result['marks_awarded'])
        except Exception as e:
            print(f"LLM evaluation skipped for section '{section}': {e}")

        # ── Blend: LLM 70 % + local 30 % (fall back to 100 % local on LLM error) ──
        if llm_marks is not None:
            final_marks = round((llm_marks * 0.7) + (local_marks * 0.3), 1)
        else:
            final_marks = local_marks
        final_marks = max(0.0, min(final_marks, safe_max))

        return {
            'marks_awarded': round(final_marks, 1),
            'max_marks': round(safe_max, 1),
            'percentage': float(round((final_marks / safe_max) * 100, 1)),
            'scores': {
                'semantic_similarity': float(round(semantic_sim, 3)),
                'coherence':           float(round(coherence, 3)),
                'concept_coverage':    float(round(coverage, 3)),
                'depth_score':         float(depth['depth_score']),
                'llm_marks':           float(llm_marks) if llm_marks is not None else None,
                'local_marks':         float(local_marks),
            },
            'llm_evaluation': llm_result,
            'cheating_detection': cheating,
            'student_text': student_text,
            'model_text': model_text
        }
    
    def evaluate(self, student_answer: Dict, model_answer: Dict,
                 marks_per_section: Dict = None,
                 strictness: str = "moderate", subject: str = "") -> Dict:
        if marks_per_section is None:
            marks_per_section = {"Definition": 2, "Body": 4, "Conclusion": 2}

        if not self.current_config:
            self.auto_configure_from_model({"Answer": model_answer, "topic": "Deep Learning"})

        results = {}
        total_marks = 0
        max_total = 0

        for section, raw_max in marks_per_section.items():
            max_marks = float(raw_max) if raw_max and float(raw_max) > 0 else 0.0
            if max_marks <= 0:
                continue
            result = self.evaluate_section(
                section,
                student_answer.get(section, ""),
                model_answer.get(section, ""),
                max_marks,
                strictness=strictness,
                subject=subject,
            )
            results[section] = result
            total_marks += result['marks_awarded']
            max_total += max_marks
        
        overall_percentage = round((total_marks / max_total) * 100, 1) if max_total > 0 else 0.0
        
        evaluation_result = {
            'total_marks': round(total_marks, 1),
            'max_marks': round(max_total, 1),
            'percentage': float(overall_percentage),
            'section_scores': results,
            'feedback': self._generate_feedback(results),
            'config_used': str(self.current_config.get('topic', 'Deep Learning'))
        }
        
        # CRITICAL: Convert numpy types to Python native types
        evaluation_result = convert_to_serializable(evaluation_result)
        
        self.evaluation_history.append(evaluation_result)
        return evaluation_result
    
    def _generate_feedback(self, results: Dict) -> Dict:
        feedback = {'strengths': [], 'improvements': [], 'warnings': []}

        for section, data in results.items():
            max_m = data.get('max_marks') or 1
            marks_pct = (data['marks_awarded'] / max_m) * 100

            llm_eval          = data.get('llm_evaluation') or {}
            reasoning         = llm_eval.get('reasoning', '')
            concepts_covered  = llm_eval.get('concepts_covered', [])
            concepts_missing  = llm_eval.get('concepts_missing', [])

            if marks_pct >= 75:
                msg = f"{section}: Excellent understanding"
                if concepts_covered:
                    msg += f" ({', '.join(concepts_covered[:2])})"
                feedback['strengths'].append(f"✅ {msg}")
            elif marks_pct >= 50:
                msg = f"{section}: Good understanding"
                if reasoning:
                    msg += f" — {reasoning}"
                feedback['strengths'].append(f"👍 {msg}")
            else:
                msg = f"{section}: Needs improvement"
                if reasoning:
                    msg += f" — {reasoning}"
                feedback['improvements'].append(f"📚 {msg}")

            # Use LLM-identified missing concepts if available, else fall back to local coverage
            if concepts_missing:
                feedback['improvements'].append(
                    f"🔑 {section}: Missing — {', '.join(concepts_missing[:3])}"
                )
            elif data['scores']['concept_coverage'] < 0.3 and not llm_eval:
                feedback['improvements'].append(f"🔑 {section}: Missing key concepts")

            if data['cheating_detection']['is_suspicious']:
                feedback['warnings'].append(f"⚠️ {section}: High keyword density detected")

        return feedback
    
    def save_to_json_file(self, student_answer: Dict, model_answer: Dict, evaluation_result: Dict, filename: str = None):
        if filename is None:
            filename = f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Ensure evaluation_result is serializable
        evaluation_result = convert_to_serializable(evaluation_result)
        
        json_data = {
            "evaluation_result": evaluation_result,
            "student_answer": convert_to_serializable(student_answer),
            "model_answer": convert_to_serializable(model_answer),
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(json_data, f, indent=2)
        print(f"✅ Evaluation saved to {filename}")
        return filename

advanced_evaluator = AdvancedEvaluator()