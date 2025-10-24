prompt = """You are a JSON-only response system. Analyze the following text and respond ONLY with valid JSON.

Rules:
- Output ONLY valid JSON, no other text
- No explanations before or after the JSON
- Use double quotes for all strings
- Ensure all brackets are properly closed

Required JSON format:
{
  "misconduct_flag": boolean,
  "scoring": number (0-100),
  "misconduct_type": "string description"
}

Text to analyze: [YOUR_TEXT_HERE]

JSON output:"""
