
# Creating AquaScene Metadata Table: Step-by-Step Instructions

## Table Setup
1. **Create New Table**: In your AquaScene Airtable base, create a new table
2. **Name**: `Table_Metadata`  
3. **Description**: Comprehensive documentation of all tables and fields in the AquaScene Content Engine

## Field Configuration
Add the following fields to your metadata table:

### 1. Table_Name
- **Type**: singleLineText
- **Description**: Name of the Airtable table

### 2. Field_Name
- **Type**: singleLineText
- **Description**: Name of the field within the table

### 3. Field_Type
- **Type**: singleSelect
- **Description**: Airtable field type (singleLineText, number, etc.)
- **Choices**:
  - singleLineText
  - multilineText
  - singleSelect
  - multipleSelects
  - number
  - currency
  - percent
  - date
  - dateTime
  - createdTime
  - lastModifiedTime
  - autoNumber
  - formula
  - rollup
  - count
  - lookup
  - multipleRecordLinks
  - email
  - url
  - phoneNumber
  - checkbox
  - multipleAttachments
  - rating
  - richText

### 4. Description
- **Type**: multilineText
- **Description**: Business description of what this field contains

### 5. Is_Primary
- **Type**: checkbox
- **Description**: Whether this is the primary field for the table

### 6. Is_Required
- **Type**: checkbox
- **Description**: Whether this field is required/mandatory

### 7. Is_Computed
- **Type**: checkbox
- **Description**: Whether this field is computed (formula, rollup, etc.)

### 8. Validation_Rules
- **Type**: multilineText
- **Description**: Validation rules and constraints for this field

### 9. Sample_Values
- **Type**: multilineText
- **Description**: Example values found in this field

### 10. Related_Tables
- **Type**: multilineText
- **Description**: Tables this field links to or depends on

### 11. Business_Purpose
- **Type**: multilineText
- **Description**: Why this field exists and how it's used

### 12. Data_Quality_Score
- **Type**: singleSelect
- **Description**: Assessment of data quality for this field
- **Choices**:
  - Excellent
  - Good
  - Fair
  - Poor
  - Critical

### 13. Completion_Rate
- **Type**: number
- **Description**: Percentage of records with data in this field
- **Precision**: 2 decimal places

### 14. Last_Updated
- **Type**: lastModifiedTime
- **Description**: When this metadata record was last updated

### 15. Notes
- **Type**: multilineText
- **Description**: Additional notes and observations


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
