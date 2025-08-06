# AquaScene Content Manager

The **Content Manager** is the central hub for content lifecycle management in the AquaScene content engine ecosystem. It orchestrates content creation, review, publishing, and distribution workflows while providing comprehensive APIs for content and subscriber management.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Content Manager                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Content   │  │ Newsletter  │  │ Subscriber  │         │
│  │ Management  │  │ Management  │  │ Management  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Lifecycle  │  │  Workflow   │  │  Airtable   │         │
│  │  Manager    │  │ Orchestrator│  │ Integration │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ PostgreSQL  │    │AI Processor │    │  Airtable   │
│  Database   │    │   Service   │    │    API      │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Core Features

### 🎯 Content Lifecycle Management
- **Draft → Review → Approved → Published** workflow
- Automatic content quality scoring and validation  
- Scheduled publishing with optimal timing
- Content archiving and version management
- Bulk operations for content management

### 📧 Newsletter Management
- Newsletter template system with multiple formats
- Content curation and automatic issue creation
- Subscriber segmentation and targeting
- Campaign scheduling and performance tracking
- A/B testing capabilities for subject lines

### 👥 Subscriber Management
- Comprehensive subscriber profiles and preferences
- GDPR-compliant consent management
- Dynamic segmentation with behavioral triggers
- Subscription preference management
- Import/export capabilities with multiple formats

### 🔄 Workflow Orchestration
- Integration with AI Processor for content generation
- Automated content processing pipelines  
- Batch processing for efficiency
- Error handling and retry mechanisms
- Real-time workflow status monitoring

### 📊 Airtable Integration
- Bi-directional sync with Airtable databases
- Schema analysis and automatic mapping
- Metadata table creation and management
- Real-time data synchronization
- Comprehensive workflow tracking

## API Endpoints

### Content Management (`/api/v1/content`)
- `POST /` - Create new content
- `GET /` - List content with filtering and pagination
- `GET /{content_id}` - Get specific content item
- `PUT /{content_id}` - Update content
- `DELETE /{content_id}` - Delete content
- `POST /{content_id}/status` - Update content status with lifecycle management
- `POST /{content_id}/schedule` - Schedule content for publication
- `GET /{content_id}/metrics` - Get content performance metrics

### Newsletter Management (`/api/v1/newsletters`)
- `POST /issues` - Create newsletter issue
- `GET /issues` - List newsletter issues
- `POST /issues/{issue_id}/schedule` - Schedule newsletter campaign
- `POST /issues/{issue_id}/send` - Send newsletter
- `GET /issues/{issue_id}/performance` - Get campaign metrics
- `GET /templates` - List newsletter templates

### Subscriber Management (`/api/v1/subscribers`)  
- `POST /` - Create new subscriber
- `GET /` - List subscribers with filtering
- `GET /{subscriber_id}` - Get subscriber details
- `PUT /{subscriber_id}` - Update subscriber
- `POST /{subscriber_id}/status` - Update subscription status
- `GET /{subscriber_id}/preferences` - Get subscription preferences
- `POST /{subscriber_id}/tags` - Add/remove subscriber tags

### Workflow Management (`/api/v1/workflows`)
- `POST /airtable/test-connection` - Test Airtable API connection
- `POST /airtable/schema-analysis` - Analyze Airtable schema
- `POST /airtable/sync-to-database` - Sync Airtable data to database
- `POST /test-workflow` - Execute end-to-end workflow test
- `GET /status/{workflow_id}` - Get workflow execution status

## Configuration

### Environment Variables

```bash
# Server Configuration
PORT=8002
HOST=0.0.0.0
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/aquascene_content

# External Services  
AI_PROCESSOR_URL=http://ai-processor:8001
WEB_SCRAPER_URL=http://web-scraper:8003

# Airtable Integration
AIRTABLE_API_KEY=your_api_key
AIRTABLE_BASE_ID=your_base_id

# Content Management
AUTO_APPROVE_THRESHOLD=0.85
BATCH_PROCESSING_SIZE=10
DEFAULT_NEWSLETTER_FREQUENCY=weekly

# Monitoring
ENABLE_METRICS=true
LOG_LEVEL=INFO
```

## Installation & Setup

### 1. Install Dependencies
```bash
cd services/content-manager
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run Database Migrations
```bash
# The service will create tables automatically on startup
# or run manually with psql commands
```

### 4. Start the Service
```bash
# Development
python -m src.main

# Production
uvicorn src.main:app --host 0.0.0.0 --port 8002
```

### 5. Verify Installation
```bash
curl http://localhost:8002/health
```

## Key Components

### Database Models
- **Content Models**: GeneratedContent, RawContent, ContentCategory, ContentTag
- **Newsletter Models**: NewsletterIssue, NewsletterTemplate, NewsletterMetric
- **Subscriber Models**: Subscriber, SubscriberSegment, SubscriptionPreference
- **System Models**: AuditLog, SystemEvent, SystemMetric

### Business Services
- **ContentLifecycleService**: Manages content state transitions
- **ContentScheduler**: Handles content and newsletter scheduling
- **WorkflowOrchestrator**: Coordinates multi-step workflows
- **AirtableIntegration**: Manages Airtable data synchronization

### API Features
- Comprehensive CRUD operations for all entities
- Advanced filtering and pagination
- Bulk operations support
- Real-time workflow monitoring
- Performance metrics and analytics

## Integration Points

### With AI Processor
- Sends raw content for AI processing
- Receives generated content with quality scores
- Manages content generation workflows

### With Database
- Full PostgreSQL schema matching infrastructure
- Async database operations with connection pooling
- Comprehensive indexing for performance
- Database triggers for automation

### With Airtable
- Schema analysis and mapping
- Bi-directional data synchronization  
- Metadata table creation
- Real-time workflow tracking

## Error Handling & Monitoring

### Structured Error Handling
- Custom exception hierarchy
- Detailed error context and logging
- Graceful error recovery
- User-friendly error messages

### Comprehensive Logging
- Structured JSON logging
- Request/response tracking
- Business event logging
- Performance metrics

### Health Monitoring
- Health check endpoints
- Prometheus metrics
- Database connection monitoring
- External service health checks

## Development

The Content Manager service is designed as the central orchestration hub for the AquaScene content ecosystem. It provides:

1. **Complete Content Lifecycle Management** - From creation to publication
2. **Advanced Newsletter System** - Template-based campaigns with targeting
3. **Sophisticated Subscriber Management** - GDPR-compliant with segmentation
4. **Workflow Automation** - AI integration and batch processing
5. **Airtable Integration** - Seamless data synchronization

The service follows modern async Python patterns with FastAPI, SQLAlchemy, and comprehensive error handling for production-ready deployment.