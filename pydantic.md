import json
import re

def extract_and_fix_json(response_text):
    """Extract and repair JSON from LLM response"""
    
    # Method 1: Try direct parsing
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Method 2: Extract JSON between curly braces
    try:
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            potential_json = json_match.group(0)
            return json.loads(potential_json)
    except (json.JSONDecodeError, AttributeError):
        pass
    
    # Method 3: Clean common issues
    try:
        # Remove markdown code blocks
        cleaned = re.sub(r'```json\s*|\s*```', '', response_text)
        # Remove leading/trailing text
        cleaned = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if cleaned:
            return json.loads(cleaned.group(0))
    except (json.JSONDecodeError, AttributeError):
        pass
    
    # Method 4: Return default structure
    return {
        "misconduct_flag": False,
        "scoring": 0,
        "misconduct_type": "Parse error - unable to extract valid JSON",
        "_raw_response": response_text
    }

# Usage
llm_output = model.generate(prompt)
structured_output = extract_and_fix_json(llm_output)
