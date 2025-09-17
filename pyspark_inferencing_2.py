#!/usr/bin/env python3
"""
PySpark Batch Processing for LLM Inference
Uses Method 2 (LangChain Custom LLM Wrapper) for batch processing CSV data
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, current_timestamp, lit
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, IntegerType
import requests
import json
from typing import Any, List, Mapping, Optional
from datetime import datetime

# Import LangChain components (compatible with 0.3.27)
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun

class CustomOpenAICompatibleLLM(LLM):
    """
    Custom LangChain LLM wrapper for OpenAI-compatible API
    Updated with the fix you mentioned
    """
    
    base_url: str
    model_name: str
    max_tokens: int = 150
    temperature: float = 0.7
    timeout: int = 60  # Increased timeout for batch processing
    
    def __init__(self, base_url: str, model_name: str, **kwargs):
        """Initialize the custom LLM with the fix"""
        # Add the fix you mentioned
        kwargs["base_url"] = base_url
        kwargs["model_name"] = model_name
        
        super().__init__(**kwargs)
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.max_tokens = kwargs.get('max_tokens', 150)
        self.temperature = kwargs.get('temperature', 0.7)
        self.timeout = kwargs.get('timeout', 60)
    
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
        """Call the LLM with the given prompt"""
        
        headers = {"Content-Type": "application/json"}
        
        data = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature)
        }
        
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
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                return content.strip()
            else:
                raise Exception(f"Unexpected response format: {result}")
                
        except Exception as e:
            # Return error message instead of raising exception for batch processing
            return f"ERROR: {str(e)}"
    
    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {
            "base_url": self.base_url,
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

class SparkLLMProcessor:
    """PySpark processor for batch LLM inference"""
    
    def __init__(self, base_url: str, model_name: str, app_name: str = "LLM_Batch_Processing"):
        """
        Initialize the Spark LLM Processor
        
        Args:
            base_url (str): LLM server base URL
            model_name (str): Model name
            app_name (str): Spark application name
        """
        self.base_url = base_url
        self.model_name = model_name
        self.app_name = app_name
        
        # Initialize Spark Session
        self.spark = SparkSession.builder \
            .appName(app_name) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        # Set log level to reduce noise
        self.spark.sparkContext.setLogLevel("WARN")
        
        print(f"Initialized Spark Session: {app_name}")
        print(f"Spark Version: {self.spark.version}")
    
    def create_llm_udf(self, max_tokens: int = 200, temperature: float = 0.7):
        """
        Create a User Defined Function (UDF) for LLM inference
        
        Args:
            max_tokens (int): Maximum tokens for generation
            temperature (float): Temperature for randomness
            
        Returns:
            UDF function for Spark
        """
        
        def llm_inference(query: str) -> str:
            """
            Inner function for LLM inference
            This function will be executed on Spark workers
            """
            if not query or query.strip() == "":
                return "ERROR: Empty query"
            
            try:
                # Create LLM instance (will be created on each worker)
                llm = CustomOpenAICompatibleLLM(
                    base_url=self.base_url,
                    model_name=self.model_name,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Get response
                response = llm.invoke(query.strip())
                return response
                
            except Exception as e:
                return f"ERROR: {str(e)}"
        
        # Register UDF with Spark
        return udf(llm_inference, StringType())
    
    def process_csv_batch(self, 
                         input_csv_path: str, 
                         output_path: str,
                         max_tokens: int = 200,
                         temperature: float = 0.7,
                         batch_size: int = 100):
        """
        Process CSV file in batches
        
        Args:
            input_csv_path (str): Path to input CSV file
            output_path (str): Path to save output
            max_tokens (int): Maximum tokens for generation
            temperature (float): Temperature for randomness
            batch_size (int): Number of records to process in each batch
        """
        
        print(f"Starting batch processing of: {input_csv_path}")
        print(f"Output will be saved to: {output_path}")
        print(f"Parameters: max_tokens={max_tokens}, temperature={temperature}")
        
        try:
            # Read CSV file
            df = self.spark.read \
                .option("header", "true") \
                .option("inferSchema", "true") \
                .csv(input_csv_path)
            
            print(f"Loaded {df.count()} records from CSV")
            print("Schema:")
            df.printSchema()
            
            # Show sample data
            print("Sample data:")
            df.show(5, truncate=False)
            
            # Create LLM UDF
            llm_udf = self.create_llm_udf(max_tokens=max_tokens, temperature=temperature)
            
            # Add processing metadata
            df_with_metadata = df \
                .withColumn("processing_timestamp", current_timestamp()) \
                .withColumn("max_tokens", lit(max_tokens)) \
                .withColumn("temperature", lit(temperature))
            
            # Apply LLM inference
            print("Applying LLM inference...")
            df_with_responses = df_with_metadata \
                .withColumn("llm_response", llm_udf(col("query"))) \
                .withColumn("completion_timestamp", current_timestamp())
            
            # Cache the result for multiple operations
            df_with_responses.cache()
            
            # Show results
            print("Processing completed. Sample results:")
            df_with_responses.select("request_id", "query", "llm_response").show(5, truncate=False)
            
            # Save results
            print(f"Saving results to: {output_path}")
            df_with_responses \
                .coalesce(1) \
                .write \
                .mode("overwrite") \
                .option("header", "true") \
                .csv(output_path)
            
            # Show summary statistics
            total_records = df_with_responses.count()
            error_records = df_with_responses.filter(col("llm_response").startswith("ERROR:")).count()
            success_records = total_records - error_records
            
            print(f"\n=== Processing Summary ===")
            print(f"Total records processed: {total_records}")
            print(f"Successful responses: {success_records}")
            print(f"Error responses: {error_records}")
            print(f"Success rate: {(success_records/total_records)*100:.2f}%")
            
            return df_with_responses
            
        except Exception as e:
            print(f"Error during batch processing: {e}")
            raise e
    
    def process_dataframe_batch(self, 
                               df, 
                               output_path: str = None,
                               max_tokens: int = 200,
                               temperature: float = 0.7):
        """
        Process an existing Spark DataFrame
        
        Args:
            df: Spark DataFrame with 'request_id' and 'query' columns
            output_path (str): Optional output path
            max_tokens (int): Maximum tokens for generation
            temperature (float): Temperature for randomness
            
        Returns:
            Processed DataFrame with LLM responses
        """
        
        print("Processing existing DataFrame...")
        
        # Create LLM UDF
        llm_udf = self.create_llm_udf(max_tokens=max_tokens, temperature=temperature)
        
        # Add processing metadata and apply LLM inference
        df_processed = df \
            .withColumn("processing_timestamp", current_timestamp()) \
            .withColumn("llm_response", llm_udf(col("query"))) \
            .withColumn("completion_timestamp", current_timestamp())
        
        # Cache results
        df_processed.cache()
        
        # Save if output path provided
        if output_path:
            print(f"Saving results to: {output_path}")
            df_processed \
                .coalesce(1) \
                .write \
                .mode("overwrite") \
                .option("header", "true") \
                .csv(output_path)
        
        return df_processed
    
    def create_sample_data(self, output_path: str, num_records: int = 10):
        """
        Create sample CSV data for testing
        
        Args:
            output_path (str): Path to save sample CSV
            num_records (int): Number of sample records to create
        """
        
        sample_queries = [
            "What is artificial intelligence?",
            "Explain machine learning in simple terms.",
            "What are the benefits of renewable energy?",
            "How do solar panels work?",
            "What is the difference between AI and ML?",
            "Explain quantum computing briefly.",
            "What are the main programming languages?",
            "How does blockchain technology work?",
            "What is cloud computing?",
            "Explain the concept of big data."
        ]
        
        # Create sample data
        data = []
        for i in range(num_records):
            query_idx = i % len(sample_queries)
            data.append((f"req_{i+1:03d}", sample_queries[query_idx]))
        
        # Create DataFrame
        schema = StructType([
            StructField("request_id", StringType(), True),
            StructField("query", StringType(), True)
        ])
        
        sample_df = self.spark.createDataFrame(data, schema)
        
        # Save to CSV
        sample_df \
            .coalesce(1) \
            .write \
            .mode("overwrite") \
            .option("header", "true") \
            .csv(output_path)
        
        print(f"Created sample data with {num_records} records at: {output_path}")
        return sample_df
    
    def stop_spark(self):
        """Stop the Spark session"""
        if self.spark:
            self.spark.stop()
            print("Spark session stopped")

def main():
    """Main function demonstrating batch processing"""
    
    # Configuration
    BASE_URL = "http://nip01gpu87.sdi.corp.com:8000"
    MODEL_NAME = "model_lllm"
    
    # Initialize processor
    processor = SparkLLMProcessor(
        base_url=BASE_URL,
        model_name=MODEL_NAME,
        app_name="LLM_Batch_Processing_Demo"
    )
    
    try:
        # Create sample data for testing
        print("=== Creating Sample Data ===")
        sample_df = processor.create_sample_data("sample_input_data", num_records=5)
        sample_df.show(truncate=False)
        
        print("\n=== Processing Sample Data ===")
        # Process the sample data
        result_df = processor.process_dataframe_batch(
            df=sample_df,
            output_path="batch_results",
            max_tokens=150,
            temperature=0.7
        )
        
        print("\n=== Final Results ===")
        result_df.select("request_id", "query", "llm_response").show(truncate=False)
        
        # Uncomment below to process an actual CSV file
        # print("\n=== Processing CSV File ===")
        # processor.process_csv_batch(
        #     input_csv_path="your_input_file.csv",
        #     output_path="your_output_directory",
        #     max_tokens=200,
        #     temperature=0.7
        # )
        
    except Exception as e:
        print(f"Error in main: {e}")
    
    finally:
        # Clean up
        processor.stop_spark()

if __name__ == "__main__":
    main()
