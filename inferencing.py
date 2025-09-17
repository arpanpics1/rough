#pip install requests langchain langchain-community langchain-openai


# Method 1: Direct HTTP request using requests library
import requests
import json

def inference_direct(prompt, max_tokens=150, temperature=0.7):
    """
    Direct inference using requests library
    """
    url = "http://nip01gpu87.sdi.corp.com:8000/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "model_lllm",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except KeyError as e:
        print(f"Unexpected response format: {e}")
        return None

# Method 2: Using LangChain framework
from langchain_community.llms import OpenAI
from langchain.schema import BaseLanguageModel
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from typing import Any, List, Mapping, Optional
import requests

class CustomOpenAICompatibleLLM(LLM):
    """
    Custom LangChain LLM wrapper for OpenAI-compatible API
    """
    
    base_url: str
    model_name: str
    max_tokens: int = 150
    temperature: float = 0.7
    
    def __init__(self, base_url: str, model_name: str, **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.model_name = model_name
    
    @property
    def _llm_type(self) -> str:
        return "custom_openai_compatible"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the LLM with the given prompt."""
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature)
        }
        
        if stop:
            data["stop"] = stop
            
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            raise Exception(f"LLM call failed: {e}")
    
    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {
            "base_url": self.base_url,
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

# Method 3: Using LangChain with OpenAI class (if your server is fully OpenAI compatible)
from langchain_openai import ChatOpenAI

def setup_langchain_openai():
    """
    Setup LangChain with OpenAI class for OpenAI-compatible servers
    """
    # Note: You might need to set a dummy API key even though it won't be used
    import os
    os.environ["OPENAI_API_KEY"] = "dummy-key"
    
    llm = ChatOpenAI(
        base_url="http://nip01gpu87.sdi.corp.com:8000/v1",
        model="model_lllm",
        max_tokens=150,
        temperature=0.7
    )
    
    return llm

# Usage examples
if __name__ == "__main__":
    # Example 1: Direct method
    print("=== Direct Method ===")
    response = inference_direct("What is the capital of France?")
    if response:
        print(f"Response: {response}")
    
    # Example 2: Custom LangChain wrapper
    print("\n=== Custom LangChain Method ===")
    custom_llm = CustomOpenAICompatibleLLM(
        base_url="http://nip01gpu87.sdi.corp.com:8000",
        model_name="model_lllm",
        max_tokens=150,
        temperature=0.7
    )
    
    try:
        response = custom_llm.invoke("What is the capital of France?")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: LangChain with ChatOpenAI (if server is fully compatible)
    print("\n=== LangChain ChatOpenAI Method ===")
    try:
        llm = setup_langchain_openai()
        response = llm.invoke("What is the capital of France?")
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Error: {e}")

# Advanced usage with LangChain chains
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

def create_langchain_chain():
    """
    Create a more sophisticated LangChain chain
    """
    # Initialize the custom LLM
    llm = CustomOpenAICompatibleLLM(
        base_url="http://nip01gpu87.sdi.corp.com:8000",
        model_name="model_lllm"
    )
    
    # Create a prompt template
    prompt_template = PromptTemplate(
        input_variables=["question"],
        template="Please answer the following question clearly and concisely: {question}"
    )
    
    # Create the chain
    chain = LLMChain(llm=llm, prompt=prompt_template)
    
    return chain

# Example usage of the chain
def use_langchain_chain():
    """
    Example of using LangChain chain
    """
    chain = create_langchain_chain()
    
    questions = [
        "What is the capital of France?",
        "Explain quantum computing in simple terms.",
        "What are the benefits of renewable energy?"
    ]
    
    for question in questions:
        try:
            response = chain.run(question=question)
            print(f"Q: {question}")
            print(f"A: {response}\n")
        except Exception as e:
            print(f"Error processing question '{question}': {e}\n")
