#pip install requests langchain langchain-community langchain-openai


#!/usr/bin/env python3
"""
Method 1: Direct HTTP Request to LLM Server
Simple and straightforward approach using requests library
"""

import requests
import json

class DirectLLMClient:
    def __init__(self, base_url, model_name):
        """
        Initialize the direct LLM client
        
        Args:
            base_url (str): Base URL of the LLM server
            model_name (str): Name of the model to use
        """
        self.base_url = base_url
        self.model_name = model_name
    
    def inference(self, prompt, max_tokens=150, temperature=0.7, system_message=None):
        """
        Send inference request to the LLM server
        
        Args:
            prompt (str): User prompt/question
            max_tokens (int): Maximum tokens to generate
            temperature (float): Temperature for randomness (0.0 to 1.0)
            system_message (str, optional): System message for context
            
        Returns:
            str or None: Generated response or None if error
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Build messages array
        messages = []
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            print(f"Sending request to: {url}")
            print(f"Request data: {json.dumps(data, indent=2)}")
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()  # Raise exception for bad status codes
            
            result = response.json()
            
            # Extract the response content
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                return content.strip()
            else:
                print("Unexpected response format:")
                print(json.dumps(result, indent=2))
                return None
                
        except requests.exceptions.ConnectionError:
            print(f"Error: Could not connect to {url}")
            print("Please check if the server is running and the URL is correct.")
            return None
        except requests.exceptions.Timeout:
            print("Error: Request timed out")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error {response.status_code}: {e}")
            if response.text:
                print(f"Response: {response.text}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
        except KeyError as e:
            print(f"Unexpected response format - missing key: {e}")
            return None
        except json.JSONDecodeError:
            print("Error: Invalid JSON response")
            print(f"Response text: {response.text}")
            return None

def main():
    """Main function to demonstrate the direct LLM client"""
    
    # Initialize the client
    client = DirectLLMClient(
        base_url="http://nip01gpu87.sdi.corp.com:8000",
        model_name="model_lllm"
    )
    
    # Test questions
    questions = [
        "What is the capital of France?",
        "Explain artificial intelligence in simple terms.",
        "What are the main benefits of renewable energy?",
        "Write a short poem about technology."
    ]
    
    print("=== Direct LLM Client Demo ===\n")
    
    for i, question in enumerate(questions, 1):
        print(f"Question {i}: {question}")
        print("-" * 50)
        
        # Send the request
        response = client.inference(
            prompt=question,
            max_tokens=200,
            temperature=0.7
        )
        
        if response:
            print(f"Response: {response}")
        else:
            print("Failed to get response")
        
        print("\n" + "="*70 + "\n")
    
    # Example with system message
    print("=== Example with System Message ===\n")
    
    system_msg = "You are a helpful assistant that explains things clearly and concisely."
    question = "What is machine learning?"
    
    print(f"System: {system_msg}")
    print(f"Question: {question}")
    print("-" * 50)
    
    response = client.inference(
        prompt=question,
        max_tokens=150,
        temperature=0.5,
        system_message=system_msg
    )
    
    if response:
        print(f"Response: {response}")
    else:
        print("Failed to get response")

if __name__ == "__main__":
    main()
