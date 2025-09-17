#!/usr/bin/env python3
"""
Method 2: LangChain Custom LLM Wrapper
Compatible with LangChain 0.3.27
"""

import requests
import json
from typing import Any, List, Mapping, Optional

# Updated imports for LangChain 0.3.27
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class CustomOpenAICompatibleLLM(LLM):
    """
    Custom LangChain LLM wrapper for OpenAI-compatible API
    Compatible with LangChain 0.3.27
    """
    
    base_url: str
    model_name: str
    max_tokens: int = 150
    temperature: float = 0.7
    timeout: int = 30
    
    def __init__(self, base_url: str, model_name: str, **kwargs):
        """
        Initialize the custom LLM
        
        Args:
            base_url (str): Base URL of the LLM server
            model_name (str): Name of the model
            **kwargs: Additional parameters
        """
        super().__init__(**kwargs)
        self.base_url = base_url.rstrip('/')  # Remove trailing slash
        self.model_name = model_name
        self.max_tokens = kwargs.get('max_tokens', 150)
        self.temperature = kwargs.get('temperature', 0.7)
        self.timeout = kwargs.get('timeout', 30)
    
    @property
    def _llm_type(self) -> str:
        """Return the LLM type identifier"""
        return "custom_openai_compatible"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Call the LLM with the given prompt
        
        Args:
            prompt (str): The prompt to send
            stop (List[str], optional): Stop sequences
            run_manager: Callback manager (not used)
            **kwargs: Additional parameters
            
        Returns:
            str: Generated response
            
        Raises:
            Exception: If the API call fails
        """
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Build the request data
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
        
        # Add stop sequences if provided
        if stop:
            data["stop"] = stop
            
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the content from the response
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                return content.strip()
            else:
                raise Exception(f"Unexpected response format: {result}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"HTTP request failed: {e}")
        except KeyError as e:
            raise Exception(f"Invalid response format - missing key: {e}")
        except Exception as e:
            raise Exception(f"LLM call failed: {e}")
    
    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters for this LLM instance"""
        return {
            "base_url": self.base_url,
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout
        }

class LangChainLLMManager:
    """Manager class for LangChain operations"""
    
    def __init__(self, base_url: str, model_name: str, **kwargs):
        """
        Initialize the LangChain LLM Manager
        
        Args:
            base_url (str): Base URL of the LLM server
            model_name (str): Name of the model
        """
        self.llm = CustomOpenAICompatibleLLM(
            base_url=base_url,
            model_name=model_name,
            **kwargs
        )
    
    def simple_invoke(self, prompt: str, **kwargs) -> str:
        """
        Simple invocation of the LLM
        
        Args:
            prompt (str): The prompt to send
            **kwargs: Additional parameters
            
        Returns:
            str: Generated response
        """
        try:
            response = self.llm.invoke(prompt, **kwargs)
            return response
        except Exception as e:
            return f"Error: {str(e)}"
    
    def create_chain(self, template: str, input_variables: List[str]):
        """
        Create a LangChain chain with a prompt template
        
        Args:
            template (str): Prompt template string
            input_variables (List[str]): List of input variable names
            
        Returns:
            LLMChain: Configured LangChain chain
        """
        prompt_template = PromptTemplate(
            input_variables=input_variables,
            template=template
        )
        
        chain = LLMChain(
            llm=self.llm,
            prompt=prompt_template,
            verbose=True  # Set to False to reduce output
        )
        
        return chain
    
    def run_chain(self, chain, **kwargs):
        """
        Run a LangChain chain with given parameters
        
        Args:
            chain: The LangChain chain to run
            **kwargs: Parameters for the chain
            
        Returns:
            str: Chain output
        """
        try:
            return chain.run(**kwargs)
        except Exception as e:
            return f"Chain execution error: {str(e)}"

def main():
    """Main function to demonstrate the LangChain wrapper"""
    
    print("=== LangChain Custom LLM Wrapper Demo ===\n")
    
    # Initialize the manager
    llm_manager = LangChainLLMManager(
        base_url="http://nip01gpu87.sdi.corp.com:8000",
        model_name="model_lllm",
        max_tokens=200,
        temperature=0.7
    )
    
    # Test 1: Simple invocation
    print("Test 1: Simple LLM Invocation")
    print("-" * 40)
    
    simple_questions = [
        "What is the capital of France?",
        "Explain machine learning briefly.",
        "What are the benefits of solar energy?"
    ]
    
    for question in simple_questions:
        print(f"Q: {question}")
        response = llm_manager.simple_invoke(question)
        print(f"A: {response}\n")
    
    print("="*70 + "\n")
    
    # Test 2: Using LangChain Chain with Prompt Template
    print("Test 2: LangChain Chain with Prompt Template")
    print("-" * 45)
    
    # Create a chain for Q&A
    qa_template = """
    You are a knowledgeable assistant. Please provide a clear and concise answer to the following question:
    
    Question: {question}
    
    Answer:"""
    
    qa_chain = llm_manager.create_chain(
        template=qa_template,
        input_variables=["question"]
    )
    
    chain_questions = [
        "What is artificial intelligence?",
        "How do solar panels work?",
        "What are the main programming languages?"
    ]
    
    for question in chain_questions:
        print(f"Q: {question}")
        response = llm_manager.run_chain(qa_chain, question=question)
        print(f"A: {response}\n")
    
    print("="*70 + "\n")
    
    # Test 3: More complex chain with multiple variables
    print("Test 3: Complex Chain with Multiple Variables")
    print("-" * 45)
    
    story_template = """
    Write a short {genre} story about {topic} in approximately {length} words.
    The story should be suitable for {audience}.
    
    Story:"""
    
    story_chain = llm_manager.create_chain(
        template=story_template,
        input_variables=["genre", "topic", "length", "audience"]
    )
    
    story_params = {
        "genre": "science fiction",
        "topic": "robots helping humans",
        "length": "100",
        "audience": "children"
    }
    
    print(f"Parameters: {story_params}")
    response = llm_manager.run_chain(story_chain, **story_params)
    print(f"Story: {response}\n")
    
    print("="*70 + "\n")
    
    # Test 4: Direct LLM properties
    print("Test 4: LLM Properties and Information")
    print("-" * 40)
    
    print(f"LLM Type: {llm_manager.llm._llm_type}")
    print(f"Identifying Params: {llm_manager.llm._identifying_params}")

if __name__ == "__main__":
    main()
