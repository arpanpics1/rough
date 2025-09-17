Yes, you can definitely access a Llama 3 endpoint using both Postman and curl commands. Since no API key is required, it should be straightforward. Here are both approaches:

## Using curl command

The basic structure would be:

```bash
curl -X POST "YOUR_ENDPOINT_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Your question or text here",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

**Example:**
```bash
curl -X POST "http://your-company-server:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is artificial intelligence?",
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

## Using Postman

1. **Method**: Select `POST`
2. **URL**: Enter your endpoint URL
3. **Headers**: Add `Content-Type: application/json`
4. **Body**: Select `raw` and `JSON`, then add:
```json
{
  "prompt": "Your question here",
  "max_tokens": 100,
  "temperature": 0.7
}
```

## Common Parameters

Most Llama 3 endpoints accept these parameters:
- `prompt` or `input`: Your text input
- `max_tokens`: Maximum response length (e.g., 100-500)
- `temperature`: Creativity level (0.0-1.0)
- `top_p`: Nucleus sampling (0.0-1.0)
- `stream`: Boolean for streaming responses

## To find the exact format:

1. **Check with your team** - Ask for documentation or examples
2. **Test with simple requests** - Start with basic JSON structure
3. **Look for common patterns**:
   - `/generate`, `/chat`, `/completions`, `/v1/completions`
   - OpenAI-compatible format vs custom format

## Example variations to try:

**OpenAI-style format:**
```json
{
  "model": "llama3",
  "messages": [{"role": "user", "content": "Hello!"}],
  "max_tokens": 100
}
```

**Simple format:**
```json
{
  "text": "Hello, how are you?",
  "max_length": 100
}
```

Would you like me to help you troubleshoot once you try these approaches? Just share your endpoint URL format and any error messages you encounter.


#!/bin/bash

# Basic inference request
curl -X POST "http://nip01gpu87.sdi.corp.com:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "model_lllm",
    "messages": [
      {
        "role": "user",
        "content": "What is the capital of France?"
      }
    ],
    "max_tokens": 150,
    "temperature": 0.7
  }'

# More advanced example with system message and conversation
curl -X POST "http://nip01gpu87.sdi.corp.com:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "model_lllm",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant that provides concise and accurate answers."
      },
      {
        "role": "user",
        "content": "Explain quantum computing in simple terms."
      }
    ],
    "max_tokens": 200,
    "temperature": 0.7,
    "top_p": 0.9,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
  }'

# Example with streaming response
curl -X POST "http://nip01gpu87.sdi.corp.com:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "model_lllm",
    "messages": [
      {
        "role": "user",
        "content": "Write a short poem about artificial intelligence."
      }
    ],
    "max_tokens": 100,
    "temperature": 0.8,
    "stream": true
  }'

# Example with authentication (if required)
curl -X POST "http://nip01gpu87.sdi.corp.com:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \
  -d '{
    "model": "model_lllm",
    "messages": [
      {
        "role": "user",
        "content": "Hello, how are you today?"
      }
    ],
    "max_tokens": 50,
    "temperature": 0.5
  }'
