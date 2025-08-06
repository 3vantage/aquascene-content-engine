#!/usr/bin/env python3
"""
AquaScene Content Engine - Airtable Schema Analysis
===================================================

This script performs a comprehensive analysis of the AquaScene Content Engine Airtable base,
examining all tables, fields, relationships, and data patterns to generate complete metadata.

Usage:
    python airtable_schema_analysis.py

Requirements:
    - AIRTABLE_API_KEY: Your Airtable API key
    - AIRTABLE_BASE_ID: The base ID for AquaScene Content Engine

Author: Claude Code
Date: 2025-08-06
"""

import os
import json
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from pyairtable import Api
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class FieldMetadata:
    """Metadata for an Airtable field"""
    name: str
    field_type: str
    options: Dict[str, Any]
    description: Optional[str] = None
    is_primary: bool = False
    is_computed: bool = False
    validation_rules: List[str] = None
    sample_values: List[Any] = None
    
    def __post_init__(self):
        if self.validation_rules is None:
            self.validation_rules = []
        if self.sample_values is None:
            self.sample_values = []

@dataclass
class TableMetadata:
    """Metadata for an Airtable table"""
    id: str
    name: str
    description: Optional[str]
    fields: List[FieldMetadata]
    record_count: int
    primary_field: str
    relationships: List[Dict[str, Any]]
    data_patterns: Dict[str, Any]
    business_logic: List[str]
    
    def __post_init__(self):
        if self.relationships is None:
            self.relationships = []
        if self.data_patterns is None:
            self.data_patterns = {}
        if self.business_logic is None:
            self.business_logic = []

@dataclass
class BaseMetadata:
    """Complete metadata for the Airtable base"""
    base_id: str
    base_name: str
    analysis_date: str
    tables: List[TableMetadata]
    relationships_map: Dict[str, List[str]]
    data_quality_assessment: Dict[str, Any]
    recommendations: List[str]


class AirtableSchemaAnalyzer:
    """Comprehensive Airtable schema analysis tool"""
    
    def __init__(self, api_key: str, base_id: str):
        """Initialize the analyzer with Airtable credentials"""
        self.api_key = api_key
        self.base_id = base_id
        self.api = Api(api_key)
        self.base = None
        self.tables_cache = {}
        
    def connect_to_base(self) -> bool:
        """Connect to the Airtable base and validate access"""
        try:
            # Get base information
            self.base = self.api.base(self.base_id)
            print(f"✅ Successfully connected to Airtable base: {self.base_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Airtable base: {str(e)}")
            return False
    
    def discover_tables(self) -> List[str]:
        """Discover all tables in the base"""
        try:
            # Get all tables using the API
            tables = self.base.schema().tables
            table_names = [table.name for table in tables]
            print(f"📋 Found {len(table_names)} tables:")
            for i, name in enumerate(table_names, 1):
                print(f"   {i}. {name}")
            return table_names
        except Exception as e:
            print(f"❌ Failed to discover tables: {str(e)}")
            return []
    
    def analyze_field(self, field: Dict, table_name: str, records_sample: List[Dict]) -> FieldMetadata:
        """Analyze a single field and extract metadata"""
        field_metadata = FieldMetadata(
            name=field.get('name', ''),
            field_type=field.get('type', ''),
            options=field.get('options', {})
        )
        
        # Check if this is the primary field
        field_metadata.is_primary = field.get('name') == "Name" or field.get('type') == "autoNumber"
        
        # Check if field is computed/formula
        field_metadata.is_computed = field.get('type') in ['formula', 'rollup', 'count', 'lookup']
        
        # Extract validation rules based on field type
        if field.get('type') == 'singleSelect':
            choices = field.get('options', {}).get('choices', [])
            field_metadata.validation_rules.append(f"Must be one of: {[c.get('name') for c in choices]}")
        elif field.get('type') == 'multipleSelects':
            choices = field.get('options', {}).get('choices', [])
            field_metadata.validation_rules.append(f"Can include: {[c.get('name') for c in choices]}")
        elif field.get('type') == 'number':
            precision = field.get('options', {}).get('precision')
            if precision is not None:
                field_metadata.validation_rules.append(f"Precision: {precision} decimal places")
        elif field.get('type') == 'currency':
            symbol = field.get('options', {}).get('symbol', '$')
            precision = field.get('options', {}).get('precision', 2)
            field_metadata.validation_rules.append(f"Currency format: {symbol} with {precision} decimal places")
        elif field.get('type') == 'date':
            date_format = field.get('options', {}).get('dateFormat', {}).get('format', 'M/D/YYYY')
            field_metadata.validation_rules.append(f"Date format: {date_format}")
        elif field.get('type') == 'email':
            field_metadata.validation_rules.append("Must be valid email format")
        elif field.get('type') == 'url':
            field_metadata.validation_rules.append("Must be valid URL format")
        elif field.get('type') == 'phoneNumber':
            field_metadata.validation_rules.append("Must be valid phone number format")
        
        # Extract sample values from records
        sample_values = []
        for record in records_sample[:10]:  # Get up to 10 sample values
            if field.get('name') in record['fields']:
                value = record['fields'][field.get('name')]
                if value not in sample_values and value is not None:
                    sample_values.append(value)
        field_metadata.sample_values = sample_values
        
        return field_metadata
    
    def analyze_table_relationships(self, table_name: str, fields: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze relationships between tables"""
        relationships = []
        
        for field in fields:
            if field.get('type') == 'multipleRecordLinks':
                linked_table = field.get('options', {}).get('linkedTableId')
                relationships.append({
                    'type': 'many_to_many',
                    'field_name': field.get('name'),
                    'linked_table_id': linked_table,
                    'inverse_field_id': field.get('options', {}).get('inverseLinkFieldId')
                })
            elif field.get('type') == 'lookup':
                relationships.append({
                    'type': 'lookup',
                    'field_name': field.get('name'),
                    'record_link_field_id': field.get('options', {}).get('recordLinkFieldId'),
                    'field_id_in_linked_table': field.get('options', {}).get('fieldIdInLinkedTable')
                })
            elif field.get('type') == 'rollup':
                relationships.append({
                    'type': 'rollup',
                    'field_name': field.get('name'),
                    'record_link_field_id': field.get('options', {}).get('recordLinkFieldId'),
                    'field_id_in_linked_table': field.get('options', {}).get('fieldIdInLinkedTable'),
                    'rollup_function': field.get('options', {}).get('rollupFunction')
                })
        
        return relationships
    
    def analyze_data_patterns(self, table_name: str, records: List[Dict]) -> Dict[str, Any]:
        """Analyze data patterns and quality in the table"""
        if not records:
            return {
                'record_count': 0,
                'field_completion_rates': {},
                'data_types_found': {},
                'common_patterns': {},
                'data_quality_issues': []
            }
        
        # Calculate field completion rates
        field_completion = {}
        all_field_names = set()
        for record in records:
            all_field_names.update(record.get('fields', {}).keys())
        
        for field_name in all_field_names:
            completed = sum(1 for record in records if field_name in record.get('fields', {}))
            field_completion[field_name] = completed / len(records)
        
        # Analyze data types found in each field
        data_types_found = {}
        for field_name in all_field_names:
            types = set()
            for record in records:
                if field_name in record.get('fields', {}):
                    value = record['fields'][field_name]
                    types.add(type(value).__name__)
            data_types_found[field_name] = list(types)
        
        # Identify common patterns
        common_patterns = {}
        for field_name in all_field_names:
            values = [record['fields'].get(field_name) for record in records if field_name in record.get('fields', {})]
            if values:
                # Most common values (for categorical data)
                if len(set(values)) < len(values) * 0.8:  # If less than 80% unique, show common values
                    value_counts = pd.Series(values).value_counts()
                    common_patterns[field_name] = {
                        'most_common': value_counts.head(5).to_dict(),
                        'unique_count': len(set(values)),
                        'total_count': len(values)
                    }
        
        # Identify data quality issues
        data_quality_issues = []
        
        # Check for fields with low completion rates
        low_completion_fields = [field for field, rate in field_completion.items() if rate < 0.5]
        if low_completion_fields:
            data_quality_issues.append(f"Fields with low completion rates (<50%): {low_completion_fields}")
        
        # Check for potential duplicate records (based on primary field)
        if records and 'Name' in all_field_names:
            names = [record['fields'].get('Name') for record in records if 'Name' in record.get('fields', {})]
            if len(names) != len(set(names)):
                data_quality_issues.append("Potential duplicate records found based on Name field")
        
        return {
            'record_count': len(records),
            'field_completion_rates': field_completion,
            'data_types_found': data_types_found,
            'common_patterns': common_patterns,
            'data_quality_issues': data_quality_issues
        }
    
    def analyze_table(self, table_name: str) -> TableMetadata:
        """Perform comprehensive analysis of a single table"""
        print(f"\n🔍 Analyzing table: {table_name}")
        
        try:
            # Get table schema
            table = self.base.table(table_name)
            schema = self.base.schema()
            
            # Find the table in schema
            table_schema = None
            for t in schema.tables:
                if t.name == table_name:
                    table_schema = t
                    break
            
            if not table_schema:
                raise Exception(f"Table {table_name} not found in schema")
            
            # Get records for analysis (sample)
            try:
                records = table.all(max_records=100)  # Sample for analysis
                print(f"   📊 Retrieved {len(records)} records for analysis")
            except Exception as e:
                print(f"   ⚠️ Could not retrieve records: {str(e)}")
                records = []
            
            # Analyze fields
            fields_metadata = []
            for field in table_schema.get('fields', []):
                field_meta = self.analyze_field(field, table_name, records)
                fields_metadata.append(field_meta)
                print(f"   📄 Analyzed field: {field.get('name')} ({field.get('type')})")
            
            # Analyze relationships
            relationships = self.analyze_table_relationships(table_name, table_schema.get('fields', []))
            print(f"   🔗 Found {len(relationships)} relationships")
            
            # Analyze data patterns
            data_patterns = self.analyze_data_patterns(table_name, records)
            print(f"   📈 Completion rate analysis: {len(data_patterns['field_completion_rates'])} fields")
            
            # Determine primary field
            primary_field = table_schema.get('primaryFieldId')
            primary_field_name = "Name"  # Default
            for field in table_schema.get('fields', []):
                if field.get('id') == primary_field:
                    primary_field_name = field.get('name')
                    break
            
            # Generate business logic insights
            business_logic = []
            if relationships:
                business_logic.append(f"Table has {len(relationships)} relationships with other tables")
            
            # Check for workflow fields
            workflow_fields = [f.get('name') for f in table_schema.get('fields', []) if f.get('type') in ['singleSelect', 'multipleSelects']]
            if workflow_fields:
                business_logic.append(f"Workflow/status fields: {workflow_fields}")
            
            # Check for computed fields
            computed_fields = [f.get('name') for f in table_schema.get('fields', []) if f.get('type') in ['formula', 'rollup', 'count', 'lookup']]
            if computed_fields:
                business_logic.append(f"Computed fields: {computed_fields}")
            
            return TableMetadata(
                id=table_schema.get('id'),
                name=table_name,
                description=table_schema.get('description'),
                fields=fields_metadata,
                record_count=len(records) if records else 0,
                primary_field=primary_field_name,
                relationships=relationships,
                data_patterns=data_patterns,
                business_logic=business_logic
            )
            
        except Exception as e:
            print(f"   ❌ Error analyzing table {table_name}: {str(e)}")
            return None
    
    def build_relationships_map(self, tables_metadata: List[TableMetadata]) -> Dict[str, List[str]]:
        """Build a comprehensive relationships map between tables"""
        relationships_map = {}
        
        for table in tables_metadata:
            related_tables = []
            for rel in table.relationships:
                if rel['type'] in ['many_to_many', 'lookup', 'rollup']:
                    # Find the related table name by ID
                    related_table_id = rel.get('linked_table_id') or rel.get('record_link_field_id')
                    if related_table_id:
                        for other_table in tables_metadata:
                            if other_table.id == related_table_id:
                                related_tables.append(other_table.name)
                                break
            
            relationships_map[table.name] = related_tables
        
        return relationships_map
    
    def assess_data_quality(self, tables_metadata: List[TableMetadata]) -> Dict[str, Any]:
        """Assess overall data quality across all tables"""
        assessment = {
            'total_tables': len(tables_metadata),
            'total_records': sum(t.record_count for t in tables_metadata),
            'tables_with_relationships': len([t for t in tables_metadata if t.relationships]),
            'tables_with_quality_issues': [],
            'field_type_distribution': {},
            'completion_rate_summary': {}
        }
        
        # Analyze field types across all tables
        field_type_counts = {}
        for table in tables_metadata:
            for field in table.fields:
                field_type_counts[field.field_type] = field_type_counts.get(field.field_type, 0) + 1
        assessment['field_type_distribution'] = field_type_counts
        
        # Analyze completion rates
        all_completion_rates = []
        for table in tables_metadata:
            if table.data_patterns and 'field_completion_rates' in table.data_patterns:
                all_completion_rates.extend(table.data_patterns['field_completion_rates'].values())
        
        if all_completion_rates:
            assessment['completion_rate_summary'] = {
                'average_completion': sum(all_completion_rates) / len(all_completion_rates),
                'min_completion': min(all_completion_rates),
                'max_completion': max(all_completion_rates)
            }
        
        # Identify tables with quality issues
        for table in tables_metadata:
            if table.data_patterns and table.data_patterns.get('data_quality_issues'):
                assessment['tables_with_quality_issues'].append({
                    'table_name': table.name,
                    'issues': table.data_patterns['data_quality_issues']
                })
        
        return assessment
    
    def generate_recommendations(self, base_metadata: BaseMetadata) -> List[str]:
        """Generate recommendations for improving the Airtable structure"""
        recommendations = []
        
        # Check for tables without relationships
        isolated_tables = [name for name, relations in base_metadata.relationships_map.items() if not relations]
        if isolated_tables:
            recommendations.append(f"Consider adding relationships for isolated tables: {isolated_tables}")
        
        # Check for low completion rates
        if base_metadata.data_quality_assessment.get('completion_rate_summary', {}).get('average_completion', 1) < 0.8:
            recommendations.append("Review fields with low completion rates - consider making required or removing unused fields")
        
        # Check for tables with many fields (potential normalization)
        large_tables = [t.name for t in base_metadata.tables if len(t.fields) > 20]
        if large_tables:
            recommendations.append(f"Consider normalizing large tables with many fields: {large_tables}")
        
        # Check for computed field usage
        tables_with_formulas = [t.name for t in base_metadata.tables if any(f.is_computed for f in t.fields)]
        if tables_with_formulas:
            recommendations.append(f"Tables using computed fields (good for automation): {tables_with_formulas}")
        
        # Data quality recommendations
        if base_metadata.data_quality_assessment.get('tables_with_quality_issues'):
            recommendations.append("Address data quality issues identified in the analysis")
        
        # Metadata table recommendation
        recommendations.append("Create a metadata table to document table purposes, field definitions, and business rules")
        recommendations.append("Implement regular data quality monitoring and validation processes")
        recommendations.append("Consider adding description fields to tables for better documentation")
        
        return recommendations
    
    def perform_full_analysis(self) -> BaseMetadata:
        """Perform complete schema analysis of the Airtable base"""
        print("🚀 Starting comprehensive Airtable schema analysis...")
        print("=" * 60)
        
        # Connect to base
        if not self.connect_to_base():
            return None
        
        # Discover all tables
        table_names = self.discover_tables()
        if not table_names:
            print("❌ No tables found or unable to access tables")
            return None
        
        # Analyze each table
        tables_metadata = []
        for table_name in table_names:
            table_meta = self.analyze_table(table_name)
            if table_meta:
                tables_metadata.append(table_meta)
        
        if not tables_metadata:
            print("❌ No tables could be analyzed")
            return None
        
        print("\n📊 Building relationships map...")
        relationships_map = self.build_relationships_map(tables_metadata)
        
        print("🔍 Assessing data quality...")
        data_quality_assessment = self.assess_data_quality(tables_metadata)
        
        # Create comprehensive metadata
        base_metadata = BaseMetadata(
            base_id=self.base_id,
            base_name=f"AquaScene Content Engine Base ({self.base_id})",
            analysis_date=datetime.now().isoformat(),
            tables=tables_metadata,
            relationships_map=relationships_map,
            data_quality_assessment=data_quality_assessment,
            recommendations=[]
        )
        
        print("💡 Generating recommendations...")
        base_metadata.recommendations = self.generate_recommendations(base_metadata)
        
        print("\n✅ Analysis completed successfully!")
        return base_metadata
    
    def export_results(self, base_metadata: BaseMetadata, output_format: str = 'json'):
        """Export analysis results to various formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_format == 'json':
            filename = f"airtable_schema_analysis_{timestamp}.json"
            with open(filename, 'w') as f:
                # Convert dataclass to dict for JSON serialization
                json.dump(asdict(base_metadata), f, indent=2, default=str)
            print(f"📄 Results exported to: {filename}")
        
        elif output_format == 'summary':
            filename = f"airtable_schema_summary_{timestamp}.txt"
            with open(filename, 'w') as f:
                f.write("AquaScene Content Engine - Airtable Schema Analysis Summary\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Analysis Date: {base_metadata.analysis_date}\n")
                f.write(f"Base ID: {base_metadata.base_id}\n")
                f.write(f"Total Tables: {len(base_metadata.tables)}\n\n")
                
                f.write("TABLES OVERVIEW:\n")
                f.write("-" * 20 + "\n")
                for table in base_metadata.tables:
                    f.write(f"• {table.name}\n")
                    f.write(f"  - Fields: {len(table.fields)}\n")
                    f.write(f"  - Records: {table.record_count}\n")
                    f.write(f"  - Relationships: {len(table.relationships)}\n")
                    f.write(f"  - Primary Field: {table.primary_field}\n\n")
                
                f.write("RELATIONSHIPS MAP:\n")
                f.write("-" * 20 + "\n")
                for table_name, related_tables in base_metadata.relationships_map.items():
                    f.write(f"• {table_name} → {related_tables}\n")
                
                f.write("\nDATA QUALITY ASSESSMENT:\n")
                f.write("-" * 25 + "\n")
                for key, value in base_metadata.data_quality_assessment.items():
                    f.write(f"• {key}: {value}\n")
                
                f.write("\nRECOMMENDATIONS:\n")
                f.write("-" * 15 + "\n")
                for i, rec in enumerate(base_metadata.recommendations, 1):
                    f.write(f"{i}. {rec}\n")
            
            print(f"📄 Summary exported to: {filename}")
        
        return filename


def main():
    """Main execution function"""
    print("AquaScene Content Engine - Airtable Schema Analyzer")
    print("=" * 55)
    
    # Get credentials from environment
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    
    if not api_key or api_key == 'your-airtable-api-key-here':
        print("\n❌ AIRTABLE_API_KEY not set or using placeholder value")
        print("Please set your actual Airtable API key in the .env file")
        print("Get your API key from: https://airtable.com/create/tokens")
        return 1
    
    if not base_id or base_id == 'your-airtable-base-id-here':
        print("\n❌ AIRTABLE_BASE_ID not set or using placeholder value")
        print("Please set your actual Airtable base ID in the .env file")
        print("Find your base ID in the Airtable API documentation for your base")
        return 1
    
    print(f"\n🔧 Configuration:")
    print(f"   API Key: {api_key[:8]}..." if api_key else "   API Key: Not set")
    print(f"   Base ID: {base_id}")
    
    # Initialize analyzer
    analyzer = AirtableSchemaAnalyzer(api_key, base_id)
    
    # Perform analysis
    base_metadata = analyzer.perform_full_analysis()
    
    if not base_metadata:
        print("\n❌ Analysis failed. Check your credentials and base access.")
        return 1
    
    # Export results
    print("\n📤 Exporting results...")
    json_file = analyzer.export_results(base_metadata, 'json')
    summary_file = analyzer.export_results(base_metadata, 'summary')
    
    print("\n" + "=" * 60)
    print("🎉 ANALYSIS COMPLETE!")
    print("=" * 60)
    print(f"📊 Analyzed {len(base_metadata.tables)} tables")
    print(f"📋 Total fields: {sum(len(t.fields) for t in base_metadata.tables)}")
    print(f"📈 Total records: {sum(t.record_count for t in base_metadata.tables)}")
    print(f"🔗 Tables with relationships: {base_metadata.data_quality_assessment.get('tables_with_relationships', 0)}")
    print(f"\n📄 Files created:")
    print(f"   • {json_file} (detailed JSON)")
    print(f"   • {summary_file} (human-readable summary)")
    
    print(f"\n💡 Key Recommendations:")
    for i, rec in enumerate(base_metadata.recommendations[:3], 1):
        print(f"   {i}. {rec}")
    
    if len(base_metadata.recommendations) > 3:
        print(f"   ... and {len(base_metadata.recommendations) - 3} more (see files for details)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())