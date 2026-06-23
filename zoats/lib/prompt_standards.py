#!/usr/bin/env python3
"""
ZoATS Prompt Standards
Centralized prompt guidance to ensure consistent, compliant LLM outputs.
"""

# Gender-Neutral Language Standard
GENDER_NEUTRAL_INSTRUCTION = """
CRITICAL: Use gender-neutral language at all times when referring to the candidate.

- Use "they/them/their" pronouns (NOT "he/him/his" or "she/her/hers")
- Use "the candidate", "the applicant", or the candidate's name
- Never assume gender from names, roles, or other characteristics
- Examples:
  ✓ "The candidate has demonstrated their analytical skills..."
  ✓ "They bring relevant experience in..."
  ✓ "[Name] shows strong potential for this role..."
  ✗ "He has 5 years of experience..." (gendered)
  ✗ "She demonstrated leadership..." (gendered)
"""

# Anti-Bias Standards
ANTI_BIAS_INSTRUCTION = """
CRITICAL: Evaluate ONLY job-relevant qualifications.

NEVER consider or mention:
- Age, generation, or "years since graduation"
- Gender, gender expression, or pronouns (except they/them)
- Race, ethnicity, national origin, or cultural background
- Disability, medical conditions, or health
- Marital/family status, pregnancy, or caregiving
- Religion, political beliefs, or personal values
- Physical appearance, voice, or mannerisms
- "Culture fit" or personality assessments
- Geographic location or accent (unless role-specific requirement)

Focus exclusively on:
- Skills, knowledge, and demonstrated capabilities
- Relevant experience and measurable outcomes
- Professional trajectory and growth
- Analytical/technical abilities as evidenced by work
"""

# Combined Standard (use this for most prompts)
FULL_PROMPT_STANDARD = f"""{GENDER_NEUTRAL_INSTRUCTION}

{ANTI_BIAS_INSTRUCTION}
"""


def add_standards_to_prompt(base_prompt: str, standards_type: str = "full") -> str:
    """
    Prepend standards to any LLM prompt.
    
    Args:
        base_prompt: The core prompt text
        standards_type: "gender_neutral", "anti_bias", or "full" (default)
    
    Returns:
        Enhanced prompt with standards prepended
    """
    if standards_type == "gender_neutral":
        prefix = GENDER_NEUTRAL_INSTRUCTION
    elif standards_type == "anti_bias":
        prefix = ANTI_BIAS_INSTRUCTION
    else:  # "full"
        prefix = FULL_PROMPT_STANDARD
    
    return f"{prefix}\n\n---\n\n{base_prompt}"


# Convenience function for common use case
def wrap_candidate_prompt(prompt: str) -> str:
    """Wrap a candidate evaluation prompt with full standards."""
    return add_standards_to_prompt(prompt, "full")
