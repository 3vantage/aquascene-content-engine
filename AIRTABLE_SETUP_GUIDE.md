# AquaScene Content Engine - Airtable Schema Analysis Setup Guide

## Overview

This guide helps you set up and run a comprehensive schema analysis of your AquaScene Content Engine Airtable base. The analysis will examine all tables, fields, relationships, and data patterns to generate complete metadata documentation.

## Prerequisites

✅ **Environment Setup Complete**
- Python 3.13+ installed
- Virtual environment created (`/venv/`)
- Required packages installed:
  - pyairtable==3.1.1
  - python-dotenv==1.1.1
  - pandas==2.3.1

## Configuration Steps

### 1. Get Your Airtable API Key

1. Visit [Airtable Personal Access Tokens](https://airtable.com/create/tokens)
2. Create a new personal access token
3. Grant the following permissions:
   - `data.records:read` - Read records
   - `schema.bases:read` - Read base schema
4. Add your base to the token's scope
5. Copy the generated token (starts with `pat...`)

### 2. Find Your Base ID

1. Open your AquaScene Content Engine base in Airtable
2. Go to Help → API Documentation
3. Your Base ID will be displayed at the top (starts with `app...`)

### 3. Update Environment Variables

Edit the `.env` file and replace the placeholder values:

```bash
# ===================
# AIRTABLE SETTINGS
# ===================
AIRTABLE_API_KEY=pat_your_actual_api_key_here
AIRTABLE_BASE_ID=app_your_actual_base_id_here
```

## Running the Analysis

### Step 1: Test Connection

```bash
# Activate virtual environment
source venv/bin/activate

# Test connection
python3 test_airtable_connection.py
```

Expected output when configured correctly:
```
AquaScene Content Engine - Airtable Connection Test
=====================================================
🔍 Testing Environment Configuration
----------------------------------------
AIRTABLE_API_KEY: ✅ Set
AIRTABLE_BASE_ID: ✅ Set
API Key (preview): pat_1234...
Base ID: app_abcdef123456

🔍 Testing pyairtable Import
------------------------------
✅ pyairtable imported successfully

🔍 Testing Airtable Connection
--------------------------------
✅ Connected successfully!
📋 Found X tables in base
📄 Tables:
   1. Content_Items
   2. Content_Types
   3. Publishing_Schedule
   ... and X more

✅ All tests passed! Ready to run schema analysis.
```

### Step 2: Run Full Schema Analysis

```bash
# Run comprehensive analysis
python3 airtable_schema_analysis.py
```

## Analysis Output

The analysis will generate two files:

### 1. JSON Report (`airtable_schema_analysis_YYYYMMDD_HHMMSS.json`)

Detailed machine-readable analysis including:
- Complete field metadata for every table
- Relationship mappings between tables
- Data quality assessment
- Sample values and validation rules
- Business logic insights

### 2. Summary Report (`airtable_schema_summary_YYYYMMDD_HHMMSS.txt`)

Human-readable summary including:
- Tables overview with record counts
- Relationships map
- Data quality metrics
- Key recommendations

## Expected Analysis Coverage

The analysis will examine:

### Table Structure
- ✅ Field names and data types
- ✅ Primary keys and computed fields
- ✅ Validation rules and constraints
- ✅ Field completion rates

### Relationships
- ✅ Linked record relationships
- ✅ Lookup fields
- ✅ Rollup fields
- ✅ Cross-table dependencies

### Data Quality
- ✅ Record counts per table
- ✅ Field completion rates
- ✅ Data type consistency
- ✅ Potential duplicates
- ✅ Common value patterns

### Business Logic
- ✅ Workflow fields (status, categories)
- ✅ Computed field dependencies
- ✅ Required vs optional fields
- ✅ Data validation patterns

## Typical AquaScene Tables Expected

Based on content engine requirements, the analysis might find tables like:

- **Content_Items** - Main content repository
- **Content_Types** - Blog posts, social media, newsletters
- **Publishing_Schedule** - When and where to publish
- **Authors** - Content creators and contributors
- **Tags** - Content categorization
- **Campaigns** - Marketing campaign tracking
- **Analytics** - Performance metrics
- **Templates** - Content templates and formats

## Troubleshooting

### Common Issues

**Connection Failed - Invalid API Key**
```
💡 Tips for API Key:
   - Get your API key from: https://airtable.com/create/tokens
   - Make sure the token has access to your base
   - API keys should start with 'pat' (Personal Access Token)
```

**Connection Failed - Base Not Found**
```
💡 Tips for Base ID:
   - Find your base ID in the Airtable API docs for your base
   - Base IDs typically start with 'app'
   - Make sure the base exists and you have access to it
```

**Import Errors**
```bash
# Reinstall dependencies
source venv/bin/activate
pip install --upgrade pyairtable python-dotenv pandas
```

## Using Analysis Results

### For Metadata Table Creation
The JSON output provides all field definitions needed to create a comprehensive metadata table documenting:
- Table purposes and business context
- Field definitions and validation rules
- Relationship mappings
- Data quality standards

### For System Documentation
The analysis results can be used to:
- Generate API documentation
- Create data dictionaries
- Plan data migrations
- Identify optimization opportunities
- Implement data governance policies

## Next Steps

After running the analysis:

1. **Review the generated reports**
2. **Create metadata table** using the field definitions
3. **Implement data quality improvements** based on recommendations
4. **Document business rules** found in the analysis
5. **Set up regular monitoring** for data quality metrics

## Security Notes

- Never commit actual API keys to version control
- Use environment variables for sensitive configuration
- Restrict API token permissions to minimum required
- Regularly rotate API keys for security

---

**Ready to analyze your AquaScene Content Engine Airtable base!** 

Run the test script first, then proceed with the full analysis once connection is confirmed.