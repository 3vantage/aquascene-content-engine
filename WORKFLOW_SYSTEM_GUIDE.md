# AquaScene Agentic Workflow System - User Guide

## Overview

The AquaScene Content Engine now includes a comprehensive agentic workflow system that automates the analysis of your Airtable base and creates detailed metadata documentation. This system provides a user-friendly web interface to execute complex Python scripts, track progress in real-time, and manage results.

## Features

### 🔧 Core Capabilities
- **Airtable Connection Testing** - Validate API credentials and discover tables
- **Schema Analysis** - Comprehensive analysis of table structures, relationships, and data patterns
- **Metadata Table Creation** - Generate documentation tables with field definitions and business rules
- **Real-time Progress Tracking** - Live updates via WebSocket connections
- **Result Management** - Download analysis results in multiple formats
- **Error Handling** - Comprehensive logging and error reporting

### 🎯 Automated Analysis
- Table and field discovery
- Relationship mapping
- Data quality assessment
- Field completion rate analysis
- Validation rule extraction
- Business logic identification
- Recommendation generation

## Getting Started

### 1. Access the Workflow System

Navigate to the Admin Dashboard at: `http://localhost:3001`

Click on **"Airtable Workflow"** in the sidebar menu.

### 2. Connect to Airtable

**Required Information:**
- **Airtable API Key**: Get from [Airtable Tokens](https://airtable.com/create/tokens)
  - Format: `patXXXXXXXXXXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`
- **Base ID**: Find in your Airtable base URL or API documentation
  - Format: `appXXXXXXXXXXXXXX`

**Steps:**
1. Enter your API credentials
2. Click "Test Connection"
3. Review discovered tables
4. Proceed to analysis

### 3. Run Schema Analysis

**What it analyzes:**
- All tables and their structures
- Field types and validation rules
- Inter-table relationships
- Data patterns and quality metrics
- Computed fields and formulas
- Business logic patterns

**Process:**
1. Click "Start Analysis"
2. Monitor real-time progress
3. View logs in the sidebar
4. Wait for completion

### 4. Review Results

**Available Outputs:**
- **JSON Results**: Complete analysis data
- **Summary Report**: Human-readable overview
- **Metadata Table**: Structured documentation

**Actions:**
- Download result files
- View analysis summary
- Create metadata table

### 5. Generate Metadata Table

**Purpose:**
Create a comprehensive documentation table in your Airtable base with:
- Field definitions and purposes
- Validation rules and constraints
- Data quality scores
- Business context
- Completion rates

**Process:**
1. Click "Create Metadata Table"
2. Monitor creation progress
3. Download setup instructions
4. Import metadata records

## API Reference

### Base URL
```
http://localhost:8000/api/v1/workflows
```

### Endpoints

#### Test Connection
```http
POST /airtable/test-connection
Content-Type: application/json

{
  "airtable_api_key": "your-api-key",
  "airtable_base_id": "your-base-id",
  "workflow_type": "connection_test"
}
```

#### Start Schema Analysis
```http
POST /airtable/schema-analysis
Content-Type: application/json

{
  "airtable_api_key": "your-api-key",
  "airtable_base_id": "your-base-id",
  "workflow_type": "schema_analysis"
}
```

#### Check Workflow Status
```http
GET /status/{workflow_id}
```

#### Create Metadata Table
```http
POST /airtable/create-metadata-table?workflow_id={workflow_id}
```

#### Download Results
```http
GET /download/{workflow_id}/{file_type}
```

#### WebSocket Updates
```
ws://localhost:8000/api/v1/workflows/ws
```

## File Outputs

### Analysis Results
- **`airtable_schema_analysis_TIMESTAMP.json`**: Complete analysis data
- **`airtable_schema_summary_TIMESTAMP.txt`**: Human-readable summary

### Metadata Table Files
- **`metadata_table_instructions_TIMESTAMP.md`**: Setup guide
- **`metadata_table_structure_TIMESTAMP.json`**: Table field definitions
- **`metadata_table_records_TIMESTAMP.json`**: Data records to import

## Workflow Monitoring

### Status Types
- **pending**: Workflow queued but not started
- **running**: Active execution with progress updates
- **completed**: Successfully finished with results
- **failed**: Error occurred during execution

### Progress Tracking
- Real-time percentage completion
- Live log streaming
- Error reporting
- Result availability

## Troubleshooting

### Common Issues

#### Connection Failed
- Verify API key format and permissions
- Check base ID accuracy
- Ensure base is accessible
- Test API key in Airtable web interface

#### Analysis Timeout
- Large bases may take longer
- Check service logs: `docker logs content-engine-api`
- Verify system resources
- Monitor for Python script errors

#### WebSocket Issues
- Check browser console for connection errors
- Verify port accessibility
- Restart services if needed

#### Missing Dependencies
- Ensure all Python packages installed
- Rebuild Docker images if needed
- Check requirements.txt for missing packages

### Log Analysis

#### Service Logs
```bash
# Content Manager API
docker logs content-engine-api

# Admin Dashboard
docker logs content-engine-admin

# All services
docker-compose logs
```

#### Workflow Logs
- Available in real-time via UI
- Stored in workflow status
- Accessible via API endpoints

## Advanced Usage

### Environment Variables

```bash
# Set for automated testing
export AIRTABLE_API_KEY="your-api-key"
export AIRTABLE_BASE_ID="your-base-id"

# Run test script
python3 test_workflow_system.py
```

### Programmatic Access

```python
import requests

# Test connection
response = requests.post(
    "http://localhost:8000/api/v1/workflows/airtable/test-connection",
    json={
        "airtable_api_key": "your-key",
        "airtable_base_id": "your-base",
        "workflow_type": "connection_test"
    }
)

# Start analysis
analysis = requests.post(
    "http://localhost:8000/api/v1/workflows/airtable/schema-analysis",
    json={
        "airtable_api_key": "your-key",
        "airtable_base_id": "your-base",
        "workflow_type": "schema_analysis"
    }
)

workflow_id = analysis.json()["workflow_id"]

# Monitor progress
status = requests.get(
    f"http://localhost:8000/api/v1/workflows/status/{workflow_id}"
)
```

### Custom Workflows

The system is designed to be extensible. You can add new workflow types by:

1. **Adding API endpoints** in `workflow_routes.py`
2. **Creating execution functions** for background processing  
3. **Adding UI components** in the React dashboard
4. **Defining workflow configurations** and status tracking

## Security Considerations

### API Key Protection
- Never commit API keys to version control
- Use environment variables for credentials
- Rotate keys regularly
- Limit base permissions to minimum required

### Access Control
- Admin dashboard requires local network access
- API endpoints should be protected in production
- Consider authentication for multi-user environments
- Monitor API usage and logs

## Performance

### Optimization Tips
- **Large Bases**: Analysis time scales with data volume
- **Network**: Ensure stable Airtable API connection
- **Resources**: Adequate memory for data processing
- **Concurrent Workflows**: Limit parallel executions

### Monitoring
- Track workflow execution times
- Monitor system resource usage
- Review error rates and patterns
- Optimize for common use cases

## Support

### Resources
- **Documentation**: This guide and inline code comments
- **Examples**: Test scripts and sample configurations
- **Logs**: Comprehensive logging for debugging
- **Community**: Share improvements and extensions

### Best Practices
1. **Test with small bases first** before analyzing large datasets
2. **Regular backups** of analysis results and metadata
3. **Version control** for workflow configurations
4. **Monitor performance** and optimize as needed
5. **Keep credentials secure** and rotate regularly

---

## Quick Start Checklist

- [ ] Services running (`docker-compose up`)
- [ ] Admin dashboard accessible (`http://localhost:3001`)
- [ ] Airtable API key obtained
- [ ] Base ID identified
- [ ] Connection test successful
- [ ] Schema analysis completed
- [ ] Results downloaded
- [ ] Metadata table created (optional)

**Ready to analyze your Airtable base! 🚀**