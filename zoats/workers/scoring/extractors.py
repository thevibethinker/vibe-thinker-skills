#!/usr/bin/env python3
"""
Resume Signal Extractors

Extract structured signals from resume text:
- Business impact (revenue, cost savings, growth %)
- Elite signals (acceptance rates, awards, top-tier institutions)
- Capability proxies (tech skills → analytical depth)
"""
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict


@dataclass
class BusinessImpact:
    """Quantified business outcome"""
    value: float
    type: str  # revenue, cost_savings, growth, scale
    context: str  # surrounding text
    confidence: float
    

@dataclass
class EliteSignal:
    """Marker of exceptional selection/achievement"""
    type: str  # acceptance_rate, award, top_tier_institution, elite_program
    detail: str
    confidence: float
    boost_factor: float  # multiplier for scoring


def extract_business_impact(text: str) -> List[BusinessImpact]:
    """
    Extract all quantified business outcomes.
    
    Examples:
    - "$90M in sales" → BusinessImpact(90, 'revenue', ...)
    - "Reduced costs by $2.5M" → BusinessImpact(2.5, 'cost_savings', ...)
    - "Grew revenue 45%" → BusinessImpact(45, 'growth', ...)
    """
    impacts = []
    text_lower = text.lower()
    
    # Revenue patterns
    revenue_patterns = [
        r'\$(\d+(?:\.\d+)?)\s*([MBK])\s*(?:in\s+)?(?:revenue|sales|ARR|bookings)',
        r'(?:revenue|sales|ARR|bookings).*?\$(\d+(?:\.\d+)?)\s*([MBK])',
        r'generated\s+\$(\d+(?:\.\d+)?)\s*([MBK])',
        r'achieved\s+\$(\d+(?:\.\d+)?)\s*([MBK])',
    ]
    
    for pattern in revenue_patterns:
        for match in re.finditer(pattern, text, re.I):
            value = float(match.group(1))
            unit = match.group(2).upper()
            multiplier = {'K': 0.001, 'M': 1, 'B': 1000}[unit]
            
            # Extract context (50 chars before/after)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            
            impacts.append(BusinessImpact(
                value=value * multiplier,
                type='revenue',
                context=context,
                confidence=0.9 if 'generated' in context.lower() or 'achieved' in context.lower() else 0.7
            ))
    
    # Cost savings patterns
    savings_patterns = [
        r'(?:saved|reduced costs?|cut costs?).*?\$(\d+(?:\.\d+)?)\s*([MBK])',
        r'\$(\d+(?:\.\d+)?)\s*([MBK])\s*(?:in\s+)?(?:savings|cost reduction)',
    ]
    
    for pattern in savings_patterns:
        for match in re.finditer(pattern, text, re.I):
            value = float(match.group(1))
            unit = match.group(2).upper()
            multiplier = {'K': 0.001, 'M': 1, 'B': 1000}[unit]
            
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            
            impacts.append(BusinessImpact(
                value=value * multiplier,
                type='cost_savings',
                context=context,
                confidence=0.85
            ))
    
    # Growth patterns (%)
    growth_patterns = [
        r'(?:grew|increased|improved).*?(\d+)%',
        r'(\d+)%\s+(?:growth|increase|improvement)',
    ]
    
    for pattern in growth_patterns:
        for match in re.finditer(pattern, text, re.I):
            value = float(match.group(1))
            
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            
            impacts.append(BusinessImpact(
                value=value,
                type='growth',
                context=context,
                confidence=0.75
            ))
    
    # Deduplicate overlapping matches
    impacts = _deduplicate_impacts(impacts)
    
    return impacts


def extract_elite_signals(text: str) -> List[EliteSignal]:
    """
    Extract markers of exceptional selection or achievement.
    
    Examples:
    - "4% acceptance rate" → boost analytical/problem-solving
    - "McKinsey" → boost all consulting criteria
    - "Rhodes Scholar" → boost everything
    """
    signals = []
    text_lower = text.lower()
    
    # Top-tier institutions
    top_tier = {
        'harvard': 1.3, 'stanford': 1.3, 'wharton': 1.3, 'mit': 1.3,
        'yale': 1.25, 'princeton': 1.25, 'oxford': 1.25, 'cambridge': 1.25,
        'cornell': 1.15, 'columbia': 1.15, 'chicago': 1.15,
    }
    
    for school, boost in top_tier.items():
        if school in text_lower:
            # Extract degree context
            for match in re.finditer(rf'\b{school}\b.*?(?:mba|phd|master|ms|ma|bs|ba)', text, re.I):
                signals.append(EliteSignal(
                    type='top_tier_institution',
                    detail=f"{school.title()} degree",
                    confidence=0.95,
                    boost_factor=boost
                ))
                break  # Only count once per school
    
    # Elite companies (MBB, FAANG)
    elite_companies = {
        'mckinsey': 1.4, 'bain': 1.35, 'bcg': 1.35,
        'google': 1.15, 'apple': 1.10, 'facebook': 1.10, 'meta': 1.10,
        'amazon': 1.10, 'microsoft': 1.10, 'netflix': 1.05,
        'deloitte consulting': 1.20, 'oliver wyman': 1.15
    }
    
    for company, boost in elite_companies.items():
        # Avoid false positives (e.g., "Microsoft Word")
        # Must have employment context
        if company in text_lower:
            # Check for employment indicators
            context_patterns = [
                rf'(?:at|for|with)\s+{re.escape(company)}',
                rf'{re.escape(company)}\s*[-–—]\s*\w+',  # "Microsoft - Engineer"
                rf'(?:worked|work|employee)\s+(?:at|for)\s+{re.escape(company)}'
            ]
            
            has_employment_context = any(
                re.search(pattern, text_lower, re.IGNORECASE) 
                for pattern in context_patterns
            )
            
            # Also check it's not just a skill mention
            skill_context_patterns = [
                rf'{re.escape(company)}\s+(?:word|excel|office|powerpoint|windows)',
                rf'(?:word|excel|office|powerpoint|windows)\s+{re.escape(company)}'
            ]
            
            is_skill_mention = any(
                re.search(pattern, text_lower, re.IGNORECASE)
                for pattern in skill_context_patterns
            )
            
            if has_employment_context and not is_skill_mention:
                signals.append(EliteSignal(
                    type='elite_company',
                    detail=f"Worked at {company.title()}",
                    confidence=0.9,
                    boost_factor=boost
                ))
    
    # Acceptance rates / selectivity
    acceptance_patterns = [
        r'(\d+(?:\.\d+)?)\%?\s*acceptance',
        r'selected.*?(\d+(?:\.\d+)?)\%',
        r'top\s+(\d+)\%',
    ]
    
    for pattern in acceptance_patterns:
        for match in re.finditer(pattern, text, re.I):
            rate = float(match.group(1))
            if rate <= 10:  # Only flag highly selective
                boost = 1.3 if rate <= 5 else 1.2
                signals.append(EliteSignal(
                    type='acceptance_rate',
                    detail=f"Selected from {rate}% pool",
                    confidence=0.85,
                    boost_factor=boost
                ))
    
    # Awards & honors
    award_keywords = [
        r'(?:fulbright|rhodes|marshall|truman)\s+scholar',
        r'summa cum laude',
        r'magna cum laude',
        r'phi beta kappa',
        r'national merit',
    ]
    
    for pattern in award_keywords:
        if re.search(pattern, text, re.I):
            signals.append(EliteSignal(
                type='award',
                detail=pattern.replace(r'(?:', '').replace(r')', '').replace('\\s+', ' '),
                confidence=0.95,
                boost_factor=1.25
            ))
    
    # Military elite units
    if re.search(r'elite.*?unit|special forces|navy seal|ranger|idf.*?elite', text, re.I):
        signals.append(EliteSignal(
            type='elite_program',
            detail='Elite military selection',
            confidence=0.8,
            boost_factor=1.2
        ))
    
    return signals


def extract_capability_proxies(text: str) -> Dict[str, float]:
    """
    Map technical/specialized skills to consulting capabilities.
    
    Returns: {capability: confidence_score}
    """
    proxies = {}
    text_lower = text.lower()
    
    # Data science → Analytical depth
    data_keywords = ['python', 'r ', 'sql', 'tableau', 'powerbi', 'data analysis', 
                     'statistical', 'machine learning', 'a/b test']
    data_score = sum(1 for kw in data_keywords if kw in text_lower) / len(data_keywords)
    if data_score > 0.15:  # At least 15% match
        proxies['analytical_depth'] = min(0.9, 0.5 + data_score)
    
    # Product management → Strategic thinking
    pm_keywords = ['roadmap', 'product strategy', 'stakeholder', 'prioritization',
                   'product market fit', 'mvp', 'user research']
    pm_score = sum(1 for kw in pm_keywords if kw in text_lower) / len(pm_keywords)
    if pm_score > 0.15:
        proxies['strategic_thinking'] = min(0.85, 0.5 + pm_score)
    
    # Operations/Supply chain → Process optimization
    ops_keywords = ['supply chain', 'logistics', 'inventory', 'lean', 'six sigma',
                    'process improvement', 'operations']
    ops_score = sum(1 for kw in ops_keywords if kw in text_lower) / len(ops_keywords)
    if ops_score > 0.15:
        proxies['process_optimization'] = min(0.8, 0.4 + ops_score)
    
    # Consulting → Direct experience (stricter - must have actual consulting keywords, not volunteer)
    consulting_core = ['consulting', 'consultant', 'mckinsey', 'bain', 'bcg', 'deloitte consulting', 'strategy consulting']
    # Exclude volunteer/student/junior consulting
    exclude_patterns = ['volunteer', 'junior achievement', 'student consulting', 'pro bono']
    
    has_consulting = False
    for kw in consulting_core:
        if kw in text_lower:
            # Check if it's in a volunteering context
            import re
            matches = [m for m in re.finditer(re.escape(kw), text_lower)]
            for match in matches:
                context = text_lower[max(0, match.start()-50):min(len(text_lower), match.end()+50)]
                if not any(excl in context for excl in exclude_patterns):
                    has_consulting = True
                    break
            if has_consulting:
                break
    
    if has_consulting:
        # Strong consulting background
        consulting_keywords = ['client', 'engagement', 'strategy', 'analysis', 'recommendations',
                              'stakeholder management', 'project']
        consulting_score = sum(1 for kw in consulting_keywords if kw in text_lower) / len(consulting_keywords)
        proxies['consulting_skills'] = min(0.95, 0.7 + consulting_score * 0.25)
    else:
        # No direct consulting - lower bar
        proxies['consulting_skills'] = 0.0
    
    return proxies


def _deduplicate_impacts(impacts: List[BusinessImpact]) -> List[BusinessImpact]:
    """Remove overlapping/duplicate impact statements"""
    if not impacts:
        return []
    
    # Sort by value descending
    sorted_impacts = sorted(impacts, key=lambda x: x.value, reverse=True)
    
    unique = []
    seen_contexts = set()
    
    for impact in sorted_impacts:
        # Check if context overlaps with existing
        overlap = False
        for seen in seen_contexts:
            if _context_overlap(impact.context, seen) > 0.7:
                overlap = True
                break
        
        if not overlap:
            unique.append(impact)
            seen_contexts.add(impact.context)
    
    return unique


def _context_overlap(ctx1: str, ctx2: str) -> float:
    """Calculate overlap ratio between two context strings"""
    words1 = set(ctx1.lower().split())
    words2 = set(ctx2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union)


if __name__ == "__main__":
    # Test extraction
    test_resume = """
    Led eBay team that generated $90M in sales and reduced costs by $2.5M.
    Selected from 4% acceptance pool to Cornell MBA program.
    Used Python, SQL, Tableau for statistical analysis.
    Worked at McKinsey for 3 years.
    """
    
    print("=== Business Impact ===")
    for impact in extract_business_impact(test_resume):
        print(f"  {impact.type}: ${impact.value}M (conf: {impact.confidence})")
    
    print("\n=== Elite Signals ===")
    for signal in extract_elite_signals(test_resume):
        print(f"  {signal.type}: {signal.detail} (boost: {signal.boost_factor}x)")
    
    print("\n=== Capability Proxies ===")
    for cap, score in extract_capability_proxies(test_resume).items():
        print(f"  {cap}: {score:.2f}")
