from typing import Dict, List

def generate_match_explanation(query: str, result: Dict) -> str:
    """Generate a human-readable explanation of why this profile matched"""
    explanation = f"This profile matches your search '{query}' based on "
    reasons = []
    
    if result['role']:
        reasons.append(f"their role as {result['role']}")
    if result['education']:
        reasons.append(f"their education background in {result['education']}")
    if result['bio']:
        reasons.append("their professional experience")
    if result.get('interests'):
        reasons.append(f"their interests in {', '.join(result['interests'][:3])}")
    
    if reasons:
        explanation += ", ".join(reasons[:-1])
        if len(reasons) > 1:
            explanation += f" and {reasons[-1]}"
        elif len(reasons) == 1:
            explanation += reasons[0]
    
    return explanation

def generate_company_explanation(query: str, result: Dict) -> str:
    """Generate a human-readable explanation of why this company matched"""
    explanation = f"This company matches your search '{query}' based on "
    reasons = []
    
    if result['industry']:
        reasons.append(f"its industry focus in {result['industry']}")
    if result['description']:
        reasons.append("its business description")
    if result['location']:
        reasons.append(f"its location in {result['location']}")
    if result.get('founded_year'):
        reasons.append(f"being founded in {result['founded_year']}")
    
    if reasons:
        explanation += ", ".join(reasons[:-1])
        if len(reasons) > 1:
            explanation += f" and {reasons[-1]}"
        elif len(reasons) == 1:
            explanation += reasons[0]
    
    return explanation

def generate_cofounder_explanation(interests: List[str], role: str, interest_similarity: float) -> str:
    """Generate a human-readable explanation for co-founder matching"""
    explanation = f"This potential co-founder could be a great match! "
    
    # Add role-based explanation
    explanation += f"They are a {role}. "
    
    # Add interests-based explanation
    if interests:
        if interest_similarity > 0.8:
            explanation += f"You share many common interests, including {', '.join(interests[:3])}. "
        elif interest_similarity > 0.5:
            explanation += f"You have some interests in common, such as {', '.join(interests[:2])}. "
        else:
            explanation += f"They bring diverse interests including {', '.join(interests[:2])}. "
    
    # Add compatibility score explanation
    if interest_similarity > 0.8:
        explanation += "Your interests align very strongly!"
    elif interest_similarity > 0.6:
        explanation += "You have good interest alignment."
    else:
        explanation += "Your different interests could bring diverse perspectives."
    
    return explanation 