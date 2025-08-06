#!/usr/bin/env python3
"""
AquaScene Content Engine - Metadata Table Creator
=================================================

This script helps create a comprehensive metadata table in Airtable based on the 
schema analysis results. It can either create the table structure or provide
instructions for manual creation.

Usage:
    python create_metadata_table.py [analysis_file.json]

Author: Claude Code
Date: 2025-08-06
"""

import json
import sys
import os
from typing import Dict, List, Any
from dotenv import load_dotenv
from pyairtable import Api

load_dotenv()

class MetadataTableCreator:
    """Creates metadata table structure from analysis results"""
    
    def __init__(self, analysis_file: str, api_key: str = None, base_id: str = None):
        self.analysis_file = analysis_file
        self.api_key = api_key or os.getenv('AIRTABLE_API_KEY')
        self.base_id = base_id or os.getenv('AIRTABLE_BASE_ID')
        self.analysis_data = None
        
    def load_analysis(self) -> bool:
        """Load schema analysis results"""
        try:
            with open(self.analysis_file, 'r') as f:
                self.analysis_data = json.load(f)
            print(f"✅ Loaded analysis from {self.analysis_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to load analysis file: {e}")
            return False
    
    def generate_metadata_structure(self) -> Dict[str, Any]:
        """Generate the structure for the metadata table"""
        
        # Define the metadata table structure
        metadata_fields = [
            {
                "name": "Table_Name",
                "type": "singleLineText",
                "description": "Name of the Airtable table",
                "options": {}
            },
            {
                "name": "Field_Name", 
                "type": "singleLineText",
                "description": "Name of the field within the table",
                "options": {}
            },
            {
                "name": "Field_Type",
                "type": "singleSelect",
                "description": "Airtable field type (singleLineText, number, etc.)",
                "options": {
                    "choices": [
                        {"name": "singleLineText"},
                        {"name": "multilineText"},
                        {"name": "singleSelect"},
                        {"name": "multipleSelects"},
                        {"name": "number"},
                        {"name": "currency"},
                        {"name": "percent"},
                        {"name": "date"},
                        {"name": "dateTime"},
                        {"name": "createdTime"},
                        {"name": "lastModifiedTime"},
                        {"name": "autoNumber"},
                        {"name": "formula"},
                        {"name": "rollup"},
                        {"name": "count"},
                        {"name": "lookup"},
                        {"name": "multipleRecordLinks"},
                        {"name": "email"},
                        {"name": "url"},
                        {"name": "phoneNumber"},
                        {"name": "checkbox"},
                        {"name": "multipleAttachments"},
                        {"name": "rating"},
                        {"name": "richText"}
                    ]
                }
            },
            {
                "name": "Description",
                "type": "multilineText",
                "description": "Business description of what this field contains",
                "options": {}
            },
            {
                "name": "Is_Primary",
                "type": "checkbox",
                "description": "Whether this is the primary field for the table",
                "options": {}
            },
            {
                "name": "Is_Required",
                "type": "checkbox", 
                "description": "Whether this field is required/mandatory",
                "options": {}
            },
            {
                "name": "Is_Computed",
                "type": "checkbox",
                "description": "Whether this field is computed (formula, rollup, etc.)",
                "options": {}
            },
            {
                "name": "Validation_Rules",
                "type": "multilineText",
                "description": "Validation rules and constraints for this field",
                "options": {}
            },
            {
                "name": "Sample_Values",
                "type": "multilineText",
                "description": "Example values found in this field",
                "options": {}
            },
            {
                "name": "Related_Tables",
                "type": "multilineText",
                "description": "Tables this field links to or depends on",
                "options": {}
            },
            {
                "name": "Business_Purpose",
                "type": "multilineText", 
                "description": "Why this field exists and how it's used",
                "options": {}
            },
            {
                "name": "Data_Quality_Score",
                "type": "singleSelect",
                "description": "Assessment of data quality for this field",
                "options": {
                    "choices": [
                        {"name": "Excellent", "color": "green"},
                        {"name": "Good", "color": "blue"},
                        {"name": "Fair", "color": "yellow"},
                        {"name": "Poor", "color": "orange"},
                        {"name": "Critical", "color": "red"}
                    ]
                }
            },
            {
                "name": "Completion_Rate",
                "type": "number",
                "description": "Percentage of records with data in this field",
                "options": {
                    "precision": 2
                }
            },
            {
                "name": "Last_Updated",
                "type": "lastModifiedTime",
                "description": "When this metadata record was last updated",
                "options": {}
            },
            {
                "name": "Notes",
                "type": "multilineText",
                "description": "Additional notes and observations",
                "options": {}
            }
        ]
        
        return {
            "name": "Table_Metadata",
            "description": "Comprehensive documentation of all tables and fields in the AquaScene Content Engine",
            "fields": metadata_fields
        }
    
    def generate_metadata_records(self) -> List[Dict[str, Any]]:
        """Generate records for the metadata table from analysis results"""
        if not self.analysis_data:
            return []
        
        records = []
        
        for table in self.analysis_data.get('tables', []):
            table_name = table.get('name', '')
            
            for field in table.get('fields', []):
                # Determine data quality score based on completion rate
                completion_rate = 0.0
                if table.get('data_patterns', {}).get('field_completion_rates'):
                    completion_rate = table['data_patterns']['field_completion_rates'].get(field.get('name', ''), 0.0)
                
                quality_score = "Excellent"
                if completion_rate < 0.5:
                    quality_score = "Critical"
                elif completion_rate < 0.7:
                    quality_score = "Poor" 
                elif completion_rate < 0.85:
                    quality_score = "Fair"
                elif completion_rate < 0.95:
                    quality_score = "Good"
                
                # Determine if field is required (heuristic)
                is_required = field.get('is_primary', False) or completion_rate >= 0.95
                
                # Build business purpose from field analysis
                business_purpose = []
                if field.get('is_primary'):
                    business_purpose.append("Primary identifier for records in this table")
                if field.get('is_computed'):
                    business_purpose.append("Automatically calculated value")
                if field.get('field_type') == 'multipleRecordLinks':
                    business_purpose.append("Links to records in related tables")
                
                # Format sample values
                sample_values_text = ""
                if field.get('sample_values'):
                    sample_values_text = str(field['sample_values'][:5])  # First 5 samples
                
                # Format validation rules
                validation_text = "\n".join(field.get('validation_rules', []))
                
                # Determine related tables
                related_tables = []
                for rel in table.get('relationships', []):
                    if rel.get('field_name') == field.get('name'):
                        # This is approximate - would need table ID to name mapping
                        related_tables.append(f"Linked table ID: {rel.get('linked_table_id', 'Unknown')}")
                
                record = {
                    "fields": {
                        "Table_Name": table_name,
                        "Field_Name": field.get('name', ''),
                        "Field_Type": field.get('field_type', ''),
                        "Description": field.get('description', ''),
                        "Is_Primary": field.get('is_primary', False),
                        "Is_Required": is_required,
                        "Is_Computed": field.get('is_computed', False),
                        "Validation_Rules": validation_text,
                        "Sample_Values": sample_values_text,
                        "Related_Tables": "\n".join(related_tables),
                        "Business_Purpose": "\n".join(business_purpose),
                        "Data_Quality_Score": quality_score,
                        "Completion_Rate": completion_rate * 100,  # Convert to percentage
                        "Notes": f"Analyzed on {self.analysis_data.get('analysis_date', 'Unknown')}"
                    }
                }
                
                records.append(record)
        
        return records
    
    def create_table_instructions(self) -> str:
        """Generate instructions for manually creating the metadata table"""
        structure = self.generate_metadata_structure()
        
        instructions = f"""
# Creating AquaScene Metadata Table: Step-by-Step Instructions

## Table Setup
1. **Create New Table**: In your AquaScene Airtable base, create a new table
2. **Name**: `{structure['name']}`  
3. **Description**: {structure['description']}

## Field Configuration
Add the following fields to your metadata table:

"""
        
        for i, field in enumerate(structure['fields'], 1):
            instructions += f"### {i}. {field['name']}\n"
            instructions += f"- **Type**: {field['type']}\n"
            instructions += f"- **Description**: {field['description']}\n"
            
            if field.get('options', {}).get('choices'):
                instructions += "- **Choices**:\n"
                for choice in field['options']['choices']:
                    instructions += f"  - {choice['name']}\n"
            
            if field.get('options', {}).get('precision') is not None:
                instructions += f"- **Precision**: {field['options']['precision']} decimal places\n"
            
            instructions += "\n"
        
        instructions += """
## Data Population

After creating the table structure, you can populate it with data from your analysis results:

1. **Manual Entry**: Use the analysis results to manually enter metadata for each field
2. **Import**: Use the generated CSV/JSON files to bulk import the metadata records
3. **API**: Use the Airtable API to programmatically create the metadata records

## Usage Tips

- Use the metadata table to document business rules and field purposes
- Update completion rates regularly by re-running the analysis
- Add custom views to filter by table, field type, or data quality score
- Link to actual field usage in workflows and documentation

## Maintenance

- Re-run schema analysis monthly to update completion rates
- Review and update business purposes as requirements change
- Monitor data quality scores and address issues
- Keep notes updated with changes and decisions
"""
        
        return instructions
    
    def export_creation_files(self):
        """Export files needed to create the metadata table"""
        if not self.analysis_data:
            print("❌ No analysis data loaded")
            return
        
        # Generate structure and records
        structure = self.generate_metadata_structure()
        records = self.generate_metadata_records()
        
        timestamp = self.analysis_data.get('analysis_date', '').replace(':', '').replace('-', '').replace('T', '_')[:15]
        
        # Export instructions
        instructions_file = f"metadata_table_instructions_{timestamp}.md"
        with open(instructions_file, 'w') as f:
            f.write(self.create_table_instructions())
        
        # Export structure as JSON
        structure_file = f"metadata_table_structure_{timestamp}.json"
        with open(structure_file, 'w') as f:
            json.dump(structure, f, indent=2)
        
        # Export records as JSON
        records_file = f"metadata_table_records_{timestamp}.json"
        with open(records_file, 'w') as f:
            json.dump(records, f, indent=2)
        
        print(f"✅ Created metadata table files:")
        print(f"   📋 {instructions_file} - Step-by-step setup guide")
        print(f"   🏗️  {structure_file} - Table structure definition")  
        print(f"   📊 {records_file} - Records to populate ({len(records)} entries)")
        
        # Summary
        tables_analyzed = len(set(r['fields']['Table_Name'] for r in records))
        fields_analyzed = len(records)
        
        print(f"\n📊 Metadata Summary:")
        print(f"   Tables: {tables_analyzed}")
        print(f"   Fields: {fields_analyzed}")
        print(f"   Quality Issues: {len([r for r in records if r['fields']['Data_Quality_Score'] in ['Poor', 'Critical']])}")
        
        return instructions_file, structure_file, records_file


def main():
    """Main execution function"""
    print("AquaScene Content Engine - Metadata Table Creator")
    print("=" * 52)
    
    # Get analysis file from command line or find latest
    analysis_file = None
    if len(sys.argv) > 1:
        analysis_file = sys.argv[1]
    else:
        # Find the most recent analysis file
        import glob
        json_files = glob.glob("*airtable_analysis_*.json") + glob.glob("demo_airtable_analysis_*.json")
        if json_files:
            analysis_file = max(json_files, key=os.path.getctime)
            print(f"🔍 Using most recent analysis file: {analysis_file}")
        else:
            print("❌ No analysis file found. Please run the schema analysis first.")
            print("Usage: python create_metadata_table.py [analysis_file.json]")
            return 1
    
    if not os.path.exists(analysis_file):
        print(f"❌ Analysis file not found: {analysis_file}")
        return 1
    
    # Create metadata table helper
    creator = MetadataTableCreator(analysis_file)
    
    # Load analysis results
    if not creator.load_analysis():
        return 1
    
    # Export creation files
    try:
        creator.export_creation_files()
        print("\n✅ Metadata table creation files generated successfully!")
        print("\n📋 Next Steps:")
        print("1. Follow the instructions file to create the table in Airtable")
        print("2. Import the records using the JSON file")
        print("3. Customize field descriptions based on your business needs")
        print("4. Set up views and filters for easy navigation")
        
    except Exception as e:
        print(f"❌ Failed to create metadata files: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())