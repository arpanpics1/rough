#!/usr/bin/env python3
"""
Schema Difference Analyzer

This script analyzes the differences between captured JSON schemas,
comparing each schema against the first (baseline) schema.
"""

import json
import os
import sys
from typing import Dict, List, Set, Any, Tuple
import argparse
from datetime import datetime


class SchemaDiffAnalyzer:
    def __init__(self, schema_file_path: str, output_dir: str = None):
        self.schema_file_path = schema_file_path
        self.output_dir = output_dir or os.path.dirname(schema_file_path)
        self.schemas = {}
        self.baseline_schema = None
        self.baseline_schema_id = None
        self.differences = {}
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def load_schemas(self):
        """Load schemas from the input file."""
        print(f"Loading schemas from: {self.schema_file_path}")
        
        if not os.path.exists(self.schema_file_path):
            raise FileNotFoundError(f"Schema file not found: {self.schema_file_path}")
        
        with open(self.schema_file_path, 'r', encoding='utf-8') as f:
            self.schemas = json.load(f)
        
        if not self.schemas:
            raise ValueError("No schemas found in the input file")
        
        # Set the first schema as baseline
        self.baseline_schema_id = list(self.schemas.keys())[0]
        self.baseline_schema = self.schemas[self.baseline_schema_id]['schema']
        
        print(f"Loaded {len(self.schemas)} schemas")
        print(f"Using '{self.baseline_schema_id}' as baseline schema")
    
    def get_all_paths(self, schema: Dict, parent_path: str = "") -> Set[str]:
        """Extract all field paths from a schema."""
        paths = set()
        
        if isinstance(schema, dict):
            if schema.get('type') == 'object' and 'properties' in schema:
                for prop_name, prop_schema in schema['properties'].items():
                    current_path = f"{parent_path}.{prop_name}" if parent_path else prop_name
                    paths.add(current_path)
                    paths.update(self.get_all_paths(prop_schema, current_path))
            elif schema.get('type') == 'array' and 'items' in schema:
                paths.update(self.get_all_paths(schema['items'], f"{parent_path}[]"))
        
        return paths
    
    def get_field_info(self, schema: Dict, target_path: str, current_path: str = "") -> Dict:
        """Get detailed information about a specific field path."""
        if isinstance(schema, dict):
            if schema.get('type') == 'object' and 'properties' in schema:
                for prop_name, prop_schema in schema['properties'].items():
                    field_path = f"{current_path}.{prop_name}" if current_path else prop_name
                    
                    if field_path == target_path:
                        return {
                            'type': prop_schema.get('type', 'unknown'),
                            'required': prop_name in schema.get('required', []),
                            'path': field_path
                        }
                    
                    if target_path.startswith(field_path + "."):
                        return self.get_field_info(prop_schema, target_path, field_path)
            
            elif schema.get('type') == 'array' and 'items' in schema:
                array_path = f"{current_path}[]"
                if target_path.startswith(array_path):
                    remaining_path = target_path[len(array_path)+1:]
                    if remaining_path:
                        return self.get_field_info(schema['items'], remaining_path, array_path)
        
        return None
    
    def compare_schemas(self, schema1: Dict, schema2: Dict) -> Dict:
        """Compare two schemas and return the differences."""
        baseline_paths = self.get_all_paths(schema1)
        comparison_paths = self.get_all_paths(schema2)
        
        # Find differences
        missing_in_comparison = baseline_paths - comparison_paths
        added_in_comparison = comparison_paths - baseline_paths
        common_paths = baseline_paths & comparison_paths
        
        # Check for type differences in common paths
        type_differences = []
        for path in common_paths:
            baseline_info = self.get_field_info(schema1, path)
            comparison_info = self.get_field_info(schema2, path)
            
            if baseline_info and comparison_info:
                if baseline_info['type'] != comparison_info['type']:
                    type_differences.append({
                        'path': path,
                        'baseline_type': baseline_info['type'],
                        'comparison_type': comparison_info['type']
                    })
                elif baseline_info['required'] != comparison_info['required']:
                    type_differences.append({
                        'path': path,
                        'baseline_required': baseline_info['required'],
                        'comparison_required': comparison_info['required'],
                        'difference_type': 'required_status'
                    })
        
        return {
            'missing_fields': sorted(list(missing_in_comparison)),
            'additional_fields': sorted(list(added_in_comparison)),
            'type_differences': type_differences,
            'total_baseline_fields': len(baseline_paths),
            'total_comparison_fields': len(comparison_paths),
            'common_fields': len(common_paths)
        }
    
    def analyze_all_schemas(self):
        """Analyze differences between all schemas and the baseline."""
        print("\nAnalyzing schema differences...")
        print("-" * 50)
        
        for schema_id, schema_info in self.schemas.items():
            if schema_id == self.baseline_schema_id:
                # Skip the baseline schema
                self.differences[schema_id] = {
                    'is_baseline': True,
                    'schema_info': schema_info
                }
                continue
            
            print(f"Comparing {schema_id} with baseline...")
            
            comparison_result = self.compare_schemas(
                self.baseline_schema,
                schema_info['schema']
            )
            
            self.differences[schema_id] = {
                'is_baseline': False,
                'schema_info': schema_info,
                'differences': comparison_result
            }
    
    def print_summary(self):
        """Print a summary of all differences."""
        print("\n" + "=" * 80)
        print("SCHEMA COMPARISON SUMMARY")
        print("=" * 80)
        
        print(f"Baseline Schema: {self.baseline_schema_id}")
        print(f"Baseline Schema Count: {self.schemas[self.baseline_schema_id]['count']} records")
        print()
        
        for schema_id, diff_info in self.differences.items():
            if diff_info['is_baseline']:
                continue
            
            print(f"Schema: {schema_id}")
            print(f"Record Count: {diff_info['schema_info']['count']}")
            print(f"Sample Lines: {diff_info['schema_info']['sample_lines'][:5]}")
            
            diff = diff_info['differences']
            print(f"Fields in baseline: {diff['total_baseline_fields']}")
            print(f"Fields in this schema: {diff['total_comparison_fields']}")
            print(f"Common fields: {diff['common_fields']}")
            
            if diff['missing_fields']:
                print(f"✗ Missing fields ({len(diff['missing_fields'])}): {', '.join(diff['missing_fields'][:10])}")
                if len(diff['missing_fields']) > 10:
                    print(f"    ... and {len(diff['missing_fields']) - 10} more")
            
            if diff['additional_fields']:
                print(f"✓ Additional fields ({len(diff['additional_fields'])}): {', '.join(diff['additional_fields'][:10])}")
                if len(diff['additional_fields']) > 10:
                    print(f"    ... and {len(diff['additional_fields']) - 10} more")
            
            if diff['type_differences']:
                print(f"⚠ Type differences ({len(diff['type_differences'])}):")
                for type_diff in diff['type_differences'][:5]:
                    if 'difference_type' in type_diff and type_diff['difference_type'] == 'required_status':
                        print(f"    - {type_diff['path']}: required status changed")
                    else:
                        print(f"    - {type_diff['path']}: {type_diff['baseline_type']} → {type_diff['comparison_type']}")
                if len(diff['type_differences']) > 5:
                    print(f"    ... and {len(diff['type_differences']) - 5} more")
            
            if not any([diff['missing_fields'], diff['additional_fields'], diff['type_differences']]):
                print("✓ No differences found (identical to baseline)")
            
            print("-" * 80)
    
    def generate_detailed_report(self) -> str:
        """Generate a detailed report file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.output_dir, f"schema_differences_report_{timestamp}.txt")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("DETAILED SCHEMA COMPARISON REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Input file: {self.schema_file_path}\n")
            f.write(f"Baseline schema: {self.baseline_schema_id}\n\n")
            
            # Baseline schema details
            f.write("BASELINE SCHEMA DETAILS:\n")
            f.write("-" * 40 + "\n")
            baseline_paths = self.get_all_paths(self.baseline_schema)
            f.write(f"Total fields: {len(baseline_paths)}\n")
            f.write(f"Record count: {self.schemas[self.baseline_schema_id]['count']}\n")
            f.write(f"Sample lines: {self.schemas[self.baseline_schema_id]['sample_lines']}\n\n")
            
            f.write("Baseline schema fields:\n")
            for path in sorted(baseline_paths):
                field_info = self.get_field_info(self.baseline_schema, path)
                if field_info:
                    required_status = "required" if field_info['required'] else "optional"
                    f.write(f"  - {path} ({field_info['type']}, {required_status})\n")
            f.write("\n")
            
            # Detailed comparison for each schema
            for schema_id, diff_info in self.differences.items():
                if diff_info['is_baseline']:
                    continue
                
                f.write(f"SCHEMA COMPARISON: {schema_id}\n")
                f.write("=" * 80 + "\n")
                f.write(f"Record count: {diff_info['schema_info']['count']}\n")
                f.write(f"First seen at line: {diff_info['schema_info']['first_seen']}\n")
                f.write(f"Sample lines: {diff_info['schema_info']['sample_lines']}\n\n")
                
                diff = diff_info['differences']
                
                if diff['missing_fields']:
                    f.write(f"MISSING FIELDS ({len(diff['missing_fields'])}):\n")
                    f.write("Fields present in baseline but missing in this schema:\n")
                    for field in diff['missing_fields']:
                        field_info = self.get_field_info(self.baseline_schema, field)
                        if field_info:
                            required_status = "required" if field_info['required'] else "optional"
                            f.write(f"  ✗ {field} ({field_info['type']}, {required_status})\n")
                    f.write("\n")
                
                if diff['additional_fields']:
                    f.write(f"ADDITIONAL FIELDS ({len(diff['additional_fields'])}):\n")
                    f.write("Fields present in this schema but not in baseline:\n")
                    for field in diff['additional_fields']:
                        field_info = self.get_field_info(diff_info['schema_info']['schema'], field)
                        if field_info:
                            required_status = "required" if field_info['required'] else "optional"
                            f.write(f"  ✓ {field} ({field_info['type']}, {required_status})\n")
                    f.write("\n")
                
                if diff['type_differences']:
                    f.write(f"TYPE DIFFERENCES ({len(diff['type_differences'])}):\n")
                    f.write("Fields with different types or requirements:\n")
                    for type_diff in diff['type_differences']:
                        if 'difference_type' in type_diff and type_diff['difference_type'] == 'required_status':
                            baseline_req = "required" if type_diff['baseline_required'] else "optional"
                            comparison_req = "required" if type_diff['comparison_required'] else "optional"
                            f.write(f"  ⚠ {type_diff['path']}: {baseline_req} → {comparison_req}\n")
                        else:
                            f.write(f"  ⚠ {type_diff['path']}: {type_diff['baseline_type']} → {type_diff['comparison_type']}\n")
                    f.write("\n")
                
                if not any([diff['missing_fields'], diff['additional_fields'], diff['type_differences']]):
                    f.write("✓ IDENTICAL TO BASELINE\n")
                    f.write("This schema has no differences compared to the baseline schema.\n\n")
                
                f.write("-" * 80 + "\n\n")
        
        return report_file
    
    def generate_json_report(self) -> str:
        """Generate a JSON report with all differences."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = os.path.join(self.output_dir, f"schema_differences_{timestamp}.json")
        
        report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'input_file': self.schema_file_path,
                'baseline_schema_id': self.baseline_schema_id,
                'total_schemas': len(self.schemas)
            },
            'baseline_schema': {
                'schema_id': self.baseline_schema_id,
                'record_count': self.schemas[self.baseline_schema_id]['count'],
                'sample_lines': self.schemas[self.baseline_schema_id]['sample_lines'],
                'total_fields': len(self.get_all_paths(self.baseline_schema))
            },
            'schema_comparisons': {}
        }
        
        for schema_id, diff_info in self.differences.items():
            if diff_info['is_baseline']:
                continue
            
            report_data['schema_comparisons'][schema_id] = {
                'record_count': diff_info['schema_info']['count'],
                'first_seen_line': diff_info['schema_info']['first_seen'],
                'sample_lines': diff_info['schema_info']['sample_lines'],
                'differences': diff_info['differences']
            }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        return json_file


def main():
    parser = argparse.ArgumentParser(
        description="Analyze differences between captured JSON schemas"
    )
    parser.add_argument(
        "schema_file",
        help="Path to the schema file generated by the schema extractor"
    )
    parser.add_argument(
        "-o", "--output-dir",
        help="Output directory for reports (default: same as input file directory)"
    )
    
    args = parser.parse_args()
    
    try:
        # Create analyzer
        analyzer = SchemaDiffAnalyzer(args.schema_file, args.output_dir)
        
        # Load schemas
        analyzer.load_schemas()
        
        # Analyze differences
        analyzer.analyze_all_schemas()
        
        # Print summary
        analyzer.print_summary()
        
        # Generate detailed reports
        txt_report = analyzer.generate_detailed_report()
        json_report = analyzer.generate_json_report()
        
        print(f"\nReports generated:")
        print(f"- Detailed text report: {txt_report}")
        print(f"- JSON report: {json_report}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
