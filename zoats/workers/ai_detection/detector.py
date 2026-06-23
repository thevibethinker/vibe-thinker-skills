#!/usr/bin/env python3
"""
AI-Written Resume Detector

Flags generic, AI-generated resumes with low burstiness/perplexity.

Indicators:
- Low burstiness: Uniform sentence length (no variation)
- Low perplexity: Generic corporate speak, clichés
- Buzzword stuffing: High keyword density, low specificity
- Lack of authenticity: No quirks, personal voice, or specific details

Returns:
- ai_generated_likelihood: "high" | "medium" | "low"
- confidence: float (0-1)
- flags: List[str] (reasons)
"""
import re
import statistics
from typing import Dict, List, Tuple
from collections import Counter


def calculate_burstiness(text: str) -> float:
    """
    Measure sentence length variance.
    Low variance = AI-generated (uniform structure)
    High variance = Human (natural rhythm variation)
    
    Returns: coefficient of variation (0-1+, higher = more bursty)
    """
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    if len(sentences) < 5:
        return 0.5  # Not enough data
    
    # Count words per sentence
    lengths = [len(s.split()) for s in sentences]
    
    if statistics.mean(lengths) == 0:
        return 0
    
    # Coefficient of variation: std_dev / mean
    cv = statistics.stdev(lengths) / statistics.mean(lengths)
    
    # Normalize: CV < 0.3 = low burstiness (AI), CV > 0.6 = high (human)
    return cv


def detect_generic_phrases(text: str) -> Tuple[int, List[str]]:
    """
    Count generic AI clichés and buzzwords.
    
    Returns: (count, matched_phrases)
    """
    generic_patterns = [
        r"\bresults?[- ]driven\b",
        r"\bsynerg(?:y|ies|istic)\b",
        r"\bthink outside the box\b",
        r"\bgo[- ]getter\b",
        r"\bteam player\b",
        r"\bhard[- ]working\b",
        r"\bdetail[- ]oriented\b",
        r"\bproven track record\b",
        r"\bdynamic (?:professional|individual)\b",
        r"\bpassionate about\b",
        r"\bleverag(?:e|ed|ing) (?:my |their )?(?:skills|experience|expertise)\b",
        r"\bstakeholder engagement\b",
        r"\bcross[- ]functional collaboration\b",
        r"\bstrategic thinking\b",
        r"\bproblem[- ]solving skills\b",
        r"\bexcellent communication\b",
        r"\bfast[- ]paced environment\b",
        r"\bwearing many hats\b",
        r"\bhit the ground running\b",
    ]
    
    text_lower = text.lower()
    matches = []
    
    for pattern in generic_patterns:
        found = re.findall(pattern, text_lower, re.I)
        matches.extend(found)
    
    return len(matches), matches[:5]  # Return top 5


def measure_specificity(text: str) -> float:
    """
    Measure ratio of specific details (numbers, names, tools) to generic terms.
    
    High specificity = authentic (lots of concrete details)
    Low specificity = AI-generated (vague, generic)
    
    Returns: ratio (0-1, higher = more specific)
    """
    # Count specific markers
    numbers = len(re.findall(r'\$?\d+[KMB%]?|\d+[.,]\d+', text))
    proper_nouns = len(re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', text))
    technical_terms = len(re.findall(r'\b(?:Python|SQL|AWS|Excel|Tableau|React|TensorFlow|Docker)\b', text, re.I))
    
    specific_count = numbers + proper_nouns + technical_terms
    
    # Count generic corporate terms
    generic_terms = len(re.findall(
        r'\b(?:leverage|synergy|optimize|streamline|enhance|facilitate|utilize|implement)\b',
        text, re.I
    ))
    
    total = specific_count + generic_terms
    if total == 0:
        return 0
    
    return specific_count / total


def detect_ai_resume(resume_text: str) -> Dict:
    """
    Main detection function.
    
    Returns:
    {
        "likelihood": "high" | "medium" | "low",
        "confidence": 0.0-1.0,
        "flags": ["reason1", "reason2", ...],
        "scores": {
            "burstiness": 0.45,
            "generic_phrase_count": 8,
            "specificity": 0.23
        }
    }
    """
    flags = []
    scores = {}
    
    # 1. Burstiness
    burstiness = calculate_burstiness(resume_text)
    scores['burstiness'] = round(burstiness, 2)
    
    if burstiness < 0.3:
        flags.append("Very uniform sentence structure (low burstiness)")
    elif burstiness < 0.45:
        flags.append("Somewhat uniform structure")
    
    # 2. Generic phrases
    generic_count, generic_examples = detect_generic_phrases(resume_text)
    scores['generic_phrase_count'] = generic_count
    
    if generic_count > 5:
        flags.append(f"Heavy use of generic buzzwords ({generic_count} instances)")
        scores['generic_examples'] = generic_examples
    elif generic_count > 3:
        flags.append(f"Moderate generic language ({generic_count} instances)")
    
    # 3. Specificity
    specificity = measure_specificity(resume_text)
    scores['specificity'] = round(specificity, 2)
    
    if specificity < 0.3:
        flags.append("Low specificity (few concrete details, numbers, or names)")
    elif specificity < 0.5:
        flags.append("Moderate specificity")
    
    # 4. Combined score
    # Weight: burstiness 30%, generics 40%, specificity 30%
    ai_score = (
        (1 - min(burstiness / 0.6, 1.0)) * 0.3 +  # Low burstiness = AI
        (min(generic_count / 6, 1.0)) * 0.4 +      # High generics = AI
        (1 - specificity) * 0.3                     # Low specificity = AI
    )
    
    # Determine likelihood
    if ai_score > 0.65:
        likelihood = "high"
        confidence = min(ai_score, 0.95)
    elif ai_score > 0.45:
        likelihood = "medium"
        confidence = 0.6 + (ai_score - 0.45) * 0.5
    else:
        likelihood = "low"
        confidence = 0.3 + ai_score * 0.5
    
    return {
        "likelihood": likelihood,
        "confidence": round(confidence, 2),
        "flags": flags,
        "scores": scores
    }


if __name__ == "__main__":
    # Test
    test_ai = """
    I am a results-driven professional with a proven track record of success.
    I leverage my skills to optimize processes and enhance team collaboration.
    I am passionate about problem-solving and thrive in fast-paced environments.
    I am a detail-oriented team player who thinks outside the box.
    I have excellent communication skills and enjoy wearing many hats.
    """
    
    test_human = """
    Built automated ETL pipeline processing 5M records/day, cutting runtime from 4hrs to 12min.
    Led pricing strategy for Q3 launch—analyzed competitor data across 50 markets using Python/pandas.
    Shipped feature to 152M users. Increased retention 18% (A/B test, p<0.01).
    Cornell MBA. Former IDF. Love dogs.
    """
    
    print("AI-written test:")
    print(detect_ai_resume(test_ai))
    print("\nHuman-written test:")
    print(detect_ai_resume(test_human))
