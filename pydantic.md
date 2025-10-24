# Example with vLLM or similar frameworks
from pydantic import BaseModel

class MisconductOutput(BaseModel):
    misconduct_flag: bool
    scoring: int
    misconduct_type: str

# Use guided generation (if supported)
output = model.generate(
    prompt,
    guided_json=MisconductOutput.schema()
)
