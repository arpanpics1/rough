#!/usr/bin/env python3
"""
APISIX Log Schema Extractor

This script processes APISIX log files, extracts unique JSON schemas,
handles malformed records, and provides detailed processing statistics.
"""

import json
import os
import sys
from typing import Dict, List, Set, Any, Tuple
from collections import defaultdict
import argparse
from datetime import datetime


class SchemaExtractor:
    def __init__(self, log_file_path: str, output_dir: str = None):
        self.log_file_path = log_file_path
        self.output_dir = output_dir or os.path.dirname(log_file_path)
        self.processed_count = 0
        self.failed_count = 0
        self.schemas = {}
        self.failed_records = []
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_json_schema(self, obj: Any, path: str = "root") -> Dict:
        """
        Recursively extract schema from a JSON object.
        Returns a schema dictionary with type information and structure.
        """
        if obj is None:
            return {"type": "null", "path": path}
        elif isinstance(obj, bool):
            return {"type": "boolean", "path": path}
        elif isinstance(obj, int):
            return {"type": "integer", "path": path}
        elif isinstance(obj, float):
            return {"type": "number", "path": path}
        elif isinstance(obj, str):
            return {"type": "string", "path": path}
        elif isinstance(obj, list):
            if not obj:
                return {"type": "array", "items": {"type": "unknown"}, "path": path}
            
            # Get schema of first item and check if all items have same schema
            item_schemas = []
            for i, item in enumerate(obj[:5]):  # Check first 5 items for performance
                item_schema = self.get_json_schema(item, f"{path}[{i}]")
                item_schemas.append(item_schema)
            
            # For simplicity, use the first item's schema as the array item schema
            return {
                "type": "array",
                "items": item_schemas[0] if item_schemas else {"type": "unknown"},
                "path": path
            }
        elif isinstance(obj, dict):
            properties = {}
            for key, value in obj.items():
                properties[key] = self.get_json_schema(value, f"{path}.{key}")
            
            return {
                "type": "object",
                "properties": properties,
                "required": list(obj.keys()),
                "path": path
            }
        else:
            return {"type": "unknown", "value_type": str(type(obj)), "path": path}
    
    def normalize_schema_for_comparison(self, schema: Dict) -> Dict:
        """
        Normalize schema for comparison by removing paths and sorting required fields.
        This ensures that schemas with fields in different orders are treated as identical.
        """
        if isinstance(schema, dict):
            normalized = {}
            for k, v in schema.items():
                if k == 'path':
                    continue  # Skip path field
                elif k == 'required' and isinstance(v, list):
                    # Sort required fields to ignore order
                    normalized[k] = sorted(v)
                elif k == 'properties' and isinstance(v, dict):
                    # Sort properties by key to ignore order
                    normalized[k] = {key: self.normalize_schema_for_comparison(value) 
                                   for key, value in sorted(v.items())}
                else:
                    normalized[k] = self.normalize_schema_for_comparison(v)
            return normalized
        elif isinstance(schema, list):
            return [self.normalize_schema_for_comparison(item) for item in schema]
        else:
            return schema
    
    def schemas_equal(self, schema1: Dict, schema2: Dict) -> bool:
        """
        Compare two schemas to check if they are equivalent.
        Ignores field ordering and path information.
        """
        normalized1 = self.normalize_schema_for_comparison(schema1)
        normalized2 = self.normalize_schema_for_comparison(schema2)
        return normalized1 == normalized2
    
    def add_schema(self, schema: Dict, record_line: int):
        """
        Add a schema to the collection, checking for uniqueness.
        """
        schema_id = None
        
        # Check if this schema already exists
        for existing_id, existing_schema in self.schemas.items():
            if self.schemas_equal(schema, existing_schema['schema']):
                existing_schema['count'] += 1
                existing_schema['sample_lines'].append(record_line)
                return existing_id
        
        # New unique schema
        schema_id = f"schema_{len(self.schemas) + 1}"
        self.schemas[schema_id] = {
            'schema': schema,
            'count': 1,
            'sample_lines': [record_line],
            'first_seen': record_line
        }
        return schema_id
    
    def process_log_file(self):
        """
        Process the APISIX log file and extract schemas.
        """
        print(f"Processing log file: {self.log_file_path}")
        print(f"Output directory: {self.output_dir}")
        print("-" * 60)
        
        if not os.path.exists(self.log_file_path):
            raise FileNotFoundError(f"Log file not found: {self.log_file_path}")
        
        line_number = 0
        
        with open(self.log_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line_number += 1
                line = line.strip()
                
                if not line:  # Skip empty lines
                    continue
                
                try:
                    # Parse JSON record
                    record = json.loads(line)
                    
                    # Extract schema
                    schema = self.get_json_schema(record)
                    
                    # Add to unique schemas
                    self.add_schema(schema, line_number)
                    
                    self.processed_count += 1
                    
                    # Progress indicator
                    if self.processed_count % 1000 == 0:
                        print(f"Processed {self.processed_count} records...")
                
                except json.JSONDecodeError as e:
                    self.failed_count += 1
                    self.failed_records.append({
                        'line_number': line_number,
                        'content': line,
                        'error': str(e)
                    })
                    print(f"Warning: Failed to parse JSON at line {line_number}: {str(e)}")
                
                except Exception as e:
                    self.failed_count += 1
                    self.failed_records.append({
                        'line_number': line_number,
                        'content': line,
                        'error': f"Unexpected error: {str(e)}"
                    })
                    print(f"Warning: Unexpected error at line {line_number}: {str(e)}")
    
    def save_results(self):
        """
        Save the extracted schemas and failed records to files.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save unique schemas
        schema_file = os.path.join(self.output_dir, f"unique_schemas_{timestamp}.json")
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(self.schemas, f, indent=2, ensure_ascii=False)
        
        # Save failed records if any
        if self.failed_records:
            failed_file = os.path.join(self.output_dir, f"failed_records_{timestamp}.json")
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(self.failed_records, f, indent=2, ensure_ascii=False)
        
        # Save summary report
        self.save_summary_report(timestamp)
        
        return schema_file, failed_file if self.failed_records else None
    
    def save_summary_report(self, timestamp: str):
        """
        Save a human-readable summary report.
        """
        report_file = os.path.join(self.output_dir, f"processing_report_{timestamp}.txt")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("APISIX Log Processing Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Input file: {self.log_file_path}\n")
            f.write(f"Processing time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("PROCESSING STATISTICS:\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total records processed successfully: {self.processed_count}\n")
            f.write(f"Total records failed to process: {self.failed_count}\n")
            f.write(f"Total unique schemas found: {len(self.schemas)}\n\n")
            
            if self.schemas:
                f.write("SCHEMA SUMMARY:\n")
                f.write("-" * 30 + "\n")
                for schema_id, schema_info in self.schemas.items():
                    f.write(f"{schema_id}:\n")
                    f.write(f"  - Occurrences: {schema_info['count']}\n")
                    f.write(f"  - First seen at line: {schema_info['first_seen']}\n")
                    f.write(f"  - Sample lines: {schema_info['sample_lines'][:5]}\n")
                    f.write("\n")
            
            if self.failed_records:
                f.write("FAILED RECORDS SUMMARY:\n")
                f.write("-" * 30 + "\n")
                for i, failed in enumerate(self.failed_records[:10], 1):
                    f.write(f"{i}. Line {failed['line_number']}: {failed['error']}\n")
                if len(self.failed_records) > 10:
                    f.write(f"... and {len(self.failed_records) - 10} more failed records\n")
    
    def print_summary(self):
        """
        Print processing summary to console.
        """
        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Successfully processed: {self.processed_count} records")
        print(f"Failed to process: {self.failed_count} records")
        print(f"Unique schemas found: {len(self.schemas)}")
        
        if self.schemas:
            print("\nSCHEMA BREAKDOWN:")
            print("-" * 30)
            for schema_id, schema_info in self.schemas.items():
                print(f"{schema_id}: {schema_info['count']} occurrences")
        
        success_rate = (self.processed_count / (self.processed_count + self.failed_count)) * 100
        print(f"\nSuccess rate: {success_rate:.2f}%")


def main():
    parser = argparse.ArgumentParser(
        description="Extract unique JSON schemas from APISIX log files"
    )
    parser.add_argument(
        "log_file",
        help="Path to the APISIX log file to process"
    )
    parser.add_argument(
        "-o", "--output-dir",
        help="Output directory for results (default: same as input file directory)"
    )
    
    args = parser.parse_args()
    
    try:
        # Create schema extractor
        extractor = SchemaExtractor(args.log_file, args.output_dir)
        
        # Process the log file
        extractor.process_log_file()
        
        # Save results
        schema_file, failed_file = extractor.save_results()
        
        # Print summary
        extractor.print_summary()
        
        print(f"\nOutput files:")
        print(f"- Unique schemas: {schema_file}")
        if failed_file:
            print(f"- Failed records: {failed_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
