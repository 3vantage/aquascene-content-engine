# AquaScene Content Engine - API Reference

**Version:** 1.0  
**Last Updated:** August 6, 2025  
**Base URL:** `http://localhost:8000` (Development) | `https://api.your-domain.com` (Production)

## Overview

The AquaScene Content Engine provides a comprehensive REST API for AI-powered content generation, management, and distribution. This reference covers all endpoints, request/response formats, authentication, and integration examples.

## Table of Contents

1. [Authentication](#authentication)
2. [Content Manager API](#content-manager-api)
3. [AI Processor API](#ai-processor-api)
4. [Web Scraper API](#web-scraper-api)
5. [Subscriber Manager API](#subscriber-manager-api)
6. [Distributor API](#distributor-api)
7. [Admin Dashboard API](#admin-dashboard-api)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [SDK Examples](#sdk-examples)

## Authentication

### JWT Token Authentication

All API endpoints (except health checks) require JWT authentication.

#### Obtain Access Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "admin@aquascene.bg",
    "password": "your-password"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "expires_in": 86400
    },
    "error": null,
    "meta": {
        "timestamp": "2025-08-06T12:00:00Z"
    }
}
```

#### Using Bearer Token

Include the token in the Authorization header for all authenticated requests:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### API Key Authentication (Alternative)

For server-to-server communication:

```http
X-API-Key: your-api-key-here
```

## Content Manager API

**Base URL:** `http://localhost:8000/api/v1`

### Content Operations

#### Create Content

```http
POST /api/v1/content
Authorization: Bearer {token}
Content-Type: application/json

{
    "title": "Beginner's Guide to Planted Aquariums",
    "content": "Planted aquariums are a beautiful way to...",
    "content_type": "newsletter_article",
    "status": "draft",
    "tags": ["beginner", "planted-tank", "aquascaping"],
    "metadata": {
        "target_audience": "beginners",
        "seo_keywords": ["planted aquarium", "aquascaping basics"],
        "estimated_read_time": 5
    }
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Beginner's Guide to Planted Aquariums",
        "content_type": "newsletter_article",
        "status": "draft",
        "created_at": "2025-08-06T12:00:00Z",
        "updated_at": "2025-08-06T12:00:00Z",
        "word_count": 1250,
        "quality_score": 8.5
    },
    "error": null
}
```

#### Get Content

```http
GET /api/v1/content/{id}
Authorization: Bearer {token}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Beginner's Guide to Planted Aquariums",
        "content": "Full content text here...",
        "content_type": "newsletter_article",
        "status": "draft",
        "tags": ["beginner", "planted-tank"],
        "metadata": {
            "target_audience": "beginners",
            "seo_keywords": ["planted aquarium", "aquascaping basics"],
            "quality_score": 8.5,
            "generated_by": "ai-processor",
            "generation_cost": 0.05
        },
        "created_at": "2025-08-06T12:00:00Z",
        "updated_at": "2025-08-06T12:00:00Z"
    }
}
```

#### List Content

```http
GET /api/v1/content?page=1&limit=20&content_type=newsletter_article&status=published
Authorization: Bearer {token}
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20, max: 100)
- `content_type` (string): Filter by content type
- `status` (string): Filter by status (draft, published, archived)
- `tags` (string): Filter by tags (comma-separated)
- `search` (string): Search in title and content
- `sort` (string): Sort field (created_at, updated_at, quality_score)
- `order` (string): Sort order (asc, desc)

**Response:**
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Beginner's Guide to Planted Aquariums",
                "content_type": "newsletter_article",
                "status": "published",
                "quality_score": 8.5,
                "created_at": "2025-08-06T12:00:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "limit": 20,
            "total": 150,
            "pages": 8
        }
    }
}
```

#### Update Content

```http
PUT /api/v1/content/{id}
Authorization: Bearer {token}
Content-Type: application/json

{
    "title": "Updated Title",
    "content": "Updated content...",
    "status": "published",
    "tags": ["updated", "published"]
}
```

#### Delete Content

```http
DELETE /api/v1/content/{id}
Authorization: Bearer {token}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "message": "Content deleted successfully"
    }
}
```

### Content Publishing

#### Publish Content

```http
POST /api/v1/content/{id}/publish
Authorization: Bearer {token}
Content-Type: application/json

{
    "publish_at": "2025-08-07T09:00:00Z",
    "channels": ["newsletter", "blog", "social"]
}
```

#### Unpublish Content

```http
POST /api/v1/content/{id}/unpublish
Authorization: Bearer {token}
```

### Content Analytics

#### Get Content Analytics

```http
GET /api/v1/content/{id}/analytics
Authorization: Bearer {token}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "views": 1250,
        "engagement_rate": 0.15,
        "average_read_time": 4.2,
        "social_shares": 45,
        "email_opens": 320,
        "click_through_rate": 0.08,
        "quality_metrics": {
            "readability_score": 8.2,
            "seo_score": 7.8,
            "brand_consistency": 9.1
        }
    }
}
```

## AI Processor API

**Base URL:** `http://localhost:8001/api/v1`

### Content Generation

#### Generate Single Content

```http
POST /api/v1/generate
Authorization: Bearer {token}
Content-Type: application/json

{
    "content_type": "newsletter_article",
    "topic": "Setting up your first planted aquarium",
    "target_audience": "beginners",
    "brand_voice": "friendly and educational",
    "max_length": 1500,
    "seo_keywords": ["planted aquarium", "aquascaping", "beginner guide"],
    "optimization_strategy": "seo_focused",
    "llm_provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7,
    "include_images": false,
    "custom_instructions": "Include a call-to-action at the end"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": "gen-550e8400-e29b-41d4-a716-446655440000",
        "content": "Setting up your first planted aquarium can seem daunting...",
        "content_type": "newsletter_article",
        "metadata": {
            "word_count": 1450,
            "quality_score": 8.7,
            "readability_score": 7.9,
            "seo_score": 8.2,
            "brand_consistency_score": 9.0,
            "generation_time_seconds": 12.5,
            "cost_usd": 0.05,
            "llm_provider": "openai",
            "model_used": "gpt-4",
            "validation_passed": true
        },
        "optimizations_applied": [
            "seo_optimization",
            "readability_enhancement",
            "brand_voice_alignment"
        ],
        "suggestions": [
            "Consider adding more specific plant recommendations",
            "Include troubleshooting section"
        ]
    }
}
```

#### Generate Batch Content

```http
POST /api/v1/batch/generate
Authorization: Bearer {token}
Content-Type: application/json

{
    "name": "Weekly Content Calendar",
    "description": "Generate weekly content for newsletter and social media",
    "processing_mode": "concurrent",
    "max_concurrent": 3,
    "priority": "high",
    "requests": [
        {
            "content_type": "newsletter_article",
            "topic": "Top 5 beginner aquatic plants",
            "target_audience": "beginners",
            "max_length": 1200
        },
        {
            "content_type": "instagram_caption",
            "topic": "Beautiful nature aquarium showcase",
            "optimization_strategy": "social_focused",
            "max_length": 300
        },
        {
            "content_type": "how_to_guide",
            "topic": "How to trim carpet plants properly",
            "target_audience": "intermediate",
            "max_length": 1800
        }
    ]
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "batch_id": "batch-550e8400-e29b-41d4-a716-446655440000",
        "status": "processing",
        "total_requests": 3,
        "estimated_completion_time": "2025-08-06T12:05:00Z",
        "processing_started_at": "2025-08-06T12:00:00Z"
    }
}
```

#### Get Batch Status

```http
GET /api/v1/batch/{batch_id}/status
Authorization: Bearer {token}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "batch_id": "batch-550e8400-e29b-41d4-a716-446655440000",
        "status": "completed",
        "progress": {
            "completed": 3,
            "failed": 0,
            "pending": 0,
            "total": 3
        },
        "results": [
            {
                "request_id": 1,
                "status": "completed",
                "content_id": "gen-123",
                "quality_score": 8.7,
                "generation_time": 12.5
            },
            {
                "request_id": 2,
                "status": "completed", 
                "content_id": "gen-124",
                "quality_score": 9.1,
                "generation_time": 8.2
            },
            {
                "request_id": 3,
                "status": "completed",
                "content_id": "gen-125", 
                "quality_score": 8.5,
                "generation_time": 15.1
            }
        ],
        "summary": {
            "total_cost_usd": 0.15,
            "average_quality_score": 8.77,
            "total_generation_time": 35.8,
            "started_at": "2025-08-06T12:00:00Z",
            "completed_at": "2025-08-06T12:04:30Z"
        }
    }
}
```

### Content Types and Templates

#### List Available Content Types

```http
GET /api/v1/content-types
Authorization: Bearer {token}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "content_types": [
            {
                "id": "newsletter_article",
                "name": "Newsletter Article",
                "description": "Educational articles for newsletter distribution",
                "max_length": 2000,
                "typical_length": 1200,
                "optimization_focus": ["seo", "readability", "engagement"],
                "templates_available": 3
            },
            {
                "id": "instagram_caption",
                "name": "Instagram Caption",
                "description": "Social media captions with hashtags",
                "max_length": 400,
                "typical_length": 200,
                "optimization_focus": ["engagement", "hashtags", "visual"],
                "templates_available": 5
            },
            {
                "id": "how_to_guide",
                "name": "How-To Guide",
                "description": "Step-by-step instructional content",
                "max_length": 2500,
                "typical_length": 1500,
                "optimization_focus": ["clarity", "completeness", "structure"],
                "templates_available": 2
            }
        ]
    }
}
```

#### Get Available Templates

```http
GET /api/v1/templates?content_type=newsletter_article
Authorization: Bearer {token}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "templates": [
            {
                "id": "weekly-digest",
                "name": "Weekly Digest",
                "description": "Weekly roundup of aquascaping tips and trends",
                "content_type": "newsletter_article",
                "structure": [
                    "Introduction",
                    "Main Content Sections",
                    "Featured Products",
                    "Call to Action"
                ]
            },
            {
                "id": "how-to-guide",
                "name": "How-To Guide",
                "description": "Step-by-step instructional format",
                "content_type": "newsletter_article",
                "structure": [
                    "Introduction",
                    "Materials Needed",
                    "Step-by-Step Instructions",
                    "Tips and Troubleshooting",
                    "Conclusion"
                ]
            }
        ]
    }
}
```

### AI Service Configuration

#### Get LLM Provider Status

```http
GET /api/v1/llm/providers
Authorization: Bearer {token}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "providers": [
            {
                "name": "openai",
                "status": "healthy",
                "models_available": ["gpt-4", "gpt-3.5-turbo"],
                "rate_limits": {
                    "requests_per_minute": 3000,
                    "tokens_per_minute": 150000
                },
                "current_usage": {
                    "requests_today": 1250,
                    "cost_today_usd": 15.75
                }
            },
            {
                "name": "anthropic",
                "status": "healthy", 
                "models_available": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
                "rate_limits": {
                    "requests_per_minute": 1000,
                    "tokens_per_minute": 80000
                },
                "current_usage": {
                    "requests_today": 450,
                    "cost_today_usd": 8.20
                }
            }
        ]
    }
}
```

#### Update LLM Configuration

```http
PUT /api/v1/llm/config
Authorization: Bearer {token}
Content-Type: application/json

{
    "default_provider": "openai",
    "routing_strategy": "cost_optimized",
    "temperature": 0.7,
    "max_tokens": 2000,
    "enable_caching": true,
    "cache_ttl_seconds": 3600
}
```

### Quality and Validation

#### Validate Content Quality

```http
POST /api/v1/validate
Authorization: Bearer {token}
Content-Type: application/json

{
    "content": "Your content text here...",
    "content_type": "newsletter_article",
    "validation_types": ["quality", "fact_check", "brand_voice", "readability"]
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "overall_score": 8.5,
        "validation_results": {
            "quality_score": 8.7,
            "fact_check_score": 9.2,
            "brand_voice_score": 8.8,
            "readability_score": 7.9
        },
        "issues": [
            {
                "type": "readability",
                "severity": "minor",
                "message": "Consider shortening some sentences for better readability",
                "suggestions": [
                    "Break down complex sentences",
                    "Use more transition words"
                ]
            }
        ],
        "recommendations": [
            "Add more specific examples",
            "Include a glossary for technical terms"
        ]
    }
}
```

### Performance and Statistics

#### Get Service Statistics

```http
GET /api/v1/stats
Authorization: Bearer {token}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "service_info": {
            "version": "1.0.0",
            "uptime_seconds": 86400,
            "started_at": "2025-08-05T12:00:00Z"
        },
        "performance": {
            "requests_total": 15420,
            "requests_per_minute": 12.5,
            "average_response_time_seconds": 2.3,
            "success_rate": 0.96
        },
        "content_generation": {
            "total_generated": 1250,
            "average_quality_score": 8.45,
            "total_cost_usd": 67.80,
            "by_content_type": {
                "newsletter_article": 650,
                "instagram_caption": 420,
                "how_to_guide": 180
            }
        },
        "llm_usage": {
            "openai_requests": 850,
            "anthropic_requests": 400,
            "total_tokens_used": 2450000,
            "cache_hit_rate": 0.35
        }
    }
}
```

## Web Scraper API

**Base URL:** `http://localhost:8002/api/v1`

### Content Scraping

#### Scrape URL

```http
POST /api/v1/scrape
Authorization: Bearer {token}
Content-Type: application/json

{
    "url": "https://example.com/article",
    "scrape_type": "article",
    "extract_images": true,
    "follow_redirects": true,
    "user_agent": "AquaScene-Bot/1.0"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "url": "https://example.com/article",
        "title": "Advanced Aquascaping Techniques",
        "content": "Extracted article content...",
        "metadata": {
            "author": "John Smith",
            "published_date": "2025-08-01T00:00:00Z",
            "word_count": 1850,
            "language": "en"
        },
        "images": [
            {
                "url": "https://example.com/image1.jpg",
                "alt_text": "Beautiful planted aquarium",
                "caption": "Example of Dutch-style aquascaping"
            }
        ],
        "scraped_at": "2025-08-06T12:00:00Z"
    }
}
```

#### Bulk Scraping

```http
POST /api/v1/scrape/bulk
Authorization: Bearer {token}
Content-Type: application/json

{
    "urls": [
        "https://example1.com/article1",
        "https://example2.com/article2",
        "https://example3.com/article3"
    ],
    "scrape_type": "article",
    "concurrent_limit": 3
}
```

## Subscriber Manager API

**Base URL:** `http://localhost:8004/api/v1`

### Subscriber Management

#### Create Subscriber

```http
POST /api/v1/subscribers
Authorization: Bearer {token}
Content-Type: application/json

{
    "email": "user@example.com",
    "name": "John Doe",
    "preferences": {
        "content_types": ["newsletter", "tips"],
        "frequency": "weekly",
        "topics": ["planted-tanks", "aquascaping", "equipment"]
    },
    "source": "website_signup",
    "tags": ["new_subscriber", "aquascaping_enthusiast"]
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": "sub-550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "name": "John Doe",
        "status": "active",
        "subscribed_at": "2025-08-06T12:00:00Z",
        "preferences": {
            "content_types": ["newsletter", "tips"],
            "frequency": "weekly",
            "topics": ["planted-tanks", "aquascaping", "equipment"]
        }
    }
}
```

#### Get Subscriber

```http
GET /api/v1/subscribers/{id}
Authorization: Bearer {token}
```

#### List Subscribers

```http
GET /api/v1/subscribers?page=1&limit=50&status=active&tag=aquascaping_enthusiast
Authorization: Bearer {token}
```

#### Update Subscriber Preferences

```http
PUT /api/v1/subscribers/{id}/preferences
Authorization: Bearer {token}
Content-Type: application/json

{
    "content_types": ["newsletter", "tips", "product_updates"],
    "frequency": "bi_weekly",
    "topics": ["planted-tanks", "aquascaping", "equipment", "maintenance"]
}
```

### Segmentation

#### Create Segment

```http
POST /api/v1/segments
Authorization: Bearer {token}
Content-Type: application/json

{
    "name": "Beginner Aquascapers",
    "description": "New subscribers interested in basic aquascaping",
    "criteria": {
        "tags": ["beginner"],
        "preferences.topics": {"$in": ["planted-tanks", "aquascaping"]},
        "subscribed_within_days": 30
    }
}
```

#### Get Segment Subscribers

```http
GET /api/v1/segments/{id}/subscribers
Authorization: Bearer {token}
```

## Distributor API

**Base URL:** `http://localhost:8003/api/v1`

### Newsletter Distribution

#### Send Newsletter

```http
POST /api/v1/newsletters/send
Authorization: Bearer {token}
Content-Type: application/json

{
    "content_id": "550e8400-e29b-41d4-a716-446655440000",
    "template_id": "weekly-digest",
    "recipients": {
        "segment_ids": ["seg-beginners", "seg-intermediate"],
        "subscriber_ids": ["sub-123", "sub-124"]
    },
    "schedule": {
        "send_at": "2025-08-07T09:00:00Z",
        "timezone": "Europe/Sofia"
    },
    "personalization": {
        "subject_line_variants": [
            "This Week in Aquascaping",
            "Your Weekly Aquascaping Update"
        ],
        "enable_personalization": true
    }
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "campaign_id": "camp-550e8400-e29b-41d4-a716-446655440000",
        "status": "scheduled",
        "recipients_count": 1250,
        "estimated_send_time": "2025-08-07T09:00:00Z"
    }
}
```

#### Get Newsletter Analytics

```http
GET /api/v1/newsletters/{campaign_id}/analytics
Authorization: Bearer {token}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "campaign_id": "camp-550e8400-e29b-41d4-a716-446655440000",
        "sent_count": 1250,
        "delivered_count": 1230,
        "opened_count": 410,
        "clicked_count": 85,
        "unsubscribed_count": 3,
        "bounced_count": 20,
        "rates": {
            "delivery_rate": 0.984,
            "open_rate": 0.333,
            "click_rate": 0.207,
            "unsubscribe_rate": 0.002
        }
    }
}
```

### Social Media Distribution

#### Schedule Instagram Post

```http
POST /api/v1/social/instagram/schedule
Authorization: Bearer {token}
Content-Type: application/json

{
    "content_id": "550e8400-e29b-41d4-a716-446655440000",
    "caption": "Beautiful planted tank setup! 🌱🐠 Learn how to create this look in our latest guide. Link in bio! #aquascaping #plantedtank",
    "media_urls": [
        "https://storage.example.com/images/planted-tank-1.jpg"
    ],
    "schedule": {
        "post_at": "2025-08-07T15:00:00Z",
        "optimal_timing": true
    },
    "hashtags": {
        "auto_generate": true,
        "custom_tags": ["aquascaping", "plantedtank"]
    }
}
```

## Admin Dashboard API

**Base URL:** `http://localhost:3001/api/v1`

### System Administration

#### Get System Overview

```http
GET /api/v1/admin/overview
Authorization: Bearer {token}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "services": {
            "content_manager": {"status": "healthy", "uptime": 86400},
            "ai_processor": {"status": "healthy", "uptime": 86400},
            "web_scraper": {"status": "healthy", "uptime": 86400},
            "subscriber_manager": {"status": "healthy", "uptime": 86400},
            "distributor": {"status": "healthy", "uptime": 86400}
        },
        "metrics": {
            "total_content_pieces": 1250,
            "total_subscribers": 5420,
            "newsletters_sent_today": 3,
            "ai_requests_today": 145
        },
        "alerts": [
            {
                "level": "warning",
                "message": "High memory usage on AI processor",
                "timestamp": "2025-08-06T11:30:00Z"
            }
        ]
    }
}
```

#### Get User Management

```http
GET /api/v1/admin/users
Authorization: Bearer {token}
```

#### System Configuration

```http
GET /api/v1/admin/config
Authorization: Bearer {token}
```

```http
PUT /api/v1/admin/config
Authorization: Bearer {token}
Content-Type: application/json

{
    "system_settings": {
        "maintenance_mode": false,
        "max_api_requests_per_hour": 1000,
        "enable_debug_logging": false
    },
    "ai_settings": {
        "default_provider": "openai",
        "max_concurrent_generations": 5
    }
}
```

## Error Handling

### Standard Error Response Format

All APIs return errors in a consistent format:

```json
{
    "success": false,
    "data": null,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "The request data is invalid",
        "details": {
            "field": "content_type",
            "issue": "must be one of: newsletter_article, instagram_caption, how_to_guide"
        }
    },
    "meta": {
        "timestamp": "2025-08-06T12:00:00Z",
        "request_id": "req-550e8400-e29b-41d4-a716-446655440000"
    }
}
```

### HTTP Status Codes

| Status Code | Description | Usage |
|-------------|-------------|-------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST |
| 202 | Accepted | Async operation started |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 502 | Bad Gateway | Service unavailable |
| 503 | Service Unavailable | Temporary service issue |

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `AUTHENTICATION_REQUIRED` | Authentication token required |
| `INVALID_TOKEN` | JWT token invalid or expired |
| `INSUFFICIENT_PERMISSIONS` | User lacks required permissions |
| `RESOURCE_NOT_FOUND` | Requested resource doesn't exist |
| `DUPLICATE_RESOURCE` | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded |
| `AI_GENERATION_FAILED` | Content generation failed |
| `EXTERNAL_API_ERROR` | External service error |
| `DATABASE_ERROR` | Database operation failed |
| `SYSTEM_MAINTENANCE` | System in maintenance mode |

### Error Handling Examples

```javascript
// JavaScript/Node.js error handling
try {
    const response = await fetch('/api/v1/generate', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    });
    
    const result = await response.json();
    
    if (!result.success) {
        switch (result.error.code) {
            case 'VALIDATION_ERROR':
                console.error('Invalid data:', result.error.details);
                break;
            case 'RATE_LIMIT_EXCEEDED':
                console.warn('Rate limit exceeded, retrying in 60s');
                setTimeout(() => retryRequest(), 60000);
                break;
            case 'AI_GENERATION_FAILED':
                console.error('AI generation failed:', result.error.message);
                break;
            default:
                console.error('Unexpected error:', result.error);
        }
    }
} catch (error) {
    console.error('Network error:', error);
}
```

```python
# Python error handling
import requests

try:
    response = requests.post(
        'http://localhost:8001/api/v1/generate',
        headers={'Authorization': f'Bearer {token}'},
        json=request_data
    )
    
    result = response.json()
    
    if not result['success']:
        error_code = result['error']['code']
        if error_code == 'VALIDATION_ERROR':
            print(f"Validation error: {result['error']['details']}")
        elif error_code == 'RATE_LIMIT_EXCEEDED':
            print("Rate limit exceeded, waiting...")
            time.sleep(60)
        else:
            print(f"API error: {result['error']['message']}")
    
except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
```

## Rate Limiting

### Rate Limits by Endpoint

| Endpoint Pattern | Rate Limit | Window |
|------------------|------------|---------|
| `/api/v1/generate` | 60 requests | 1 hour |
| `/api/v1/batch/generate` | 10 requests | 1 hour |
| `/api/v1/content` | 1000 requests | 1 hour |
| `/api/v1/subscribers` | 500 requests | 1 hour |
| `/api/v1/newsletters/send` | 50 requests | 1 day |

### Rate Limit Headers

All responses include rate limiting information:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1628259600
X-RateLimit-Window: 3600
```

### Rate Limit Exceeded Response

```json
{
    "success": false,
    "error": {
        "code": "RATE_LIMIT_EXCEEDED",
        "message": "API rate limit exceeded",
        "details": {
            "limit": 60,
            "window_seconds": 3600,
            "reset_at": "2025-08-06T13:00:00Z"
        }
    },
    "meta": {
        "retry_after_seconds": 1800
    }
}
```

## SDK Examples

### JavaScript/Node.js SDK

```javascript
class AquaSceneAPI {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.token = token;
    }
    
    async request(method, endpoint, data = null) {
        const url = `${this.baseUrl}${endpoint}`;
        const options = {
            method,
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        return await response.json();
    }
    
    // Content generation
    async generateContent(request) {
        return await this.request('POST', '/api/v1/generate', request);
    }
    
    async generateBatch(batchRequest) {
        return await this.request('POST', '/api/v1/batch/generate', batchRequest);
    }
    
    async getBatchStatus(batchId) {
        return await this.request('GET', `/api/v1/batch/${batchId}/status`);
    }
    
    // Content management
    async createContent(content) {
        return await this.request('POST', '/api/v1/content', content);
    }
    
    async getContent(id) {
        return await this.request('GET', `/api/v1/content/${id}`);
    }
    
    async listContent(filters = {}) {
        const queryString = new URLSearchParams(filters).toString();
        return await this.request('GET', `/api/v1/content?${queryString}`);
    }
}

// Usage
const api = new AquaSceneAPI('http://localhost:8000', 'your-token');

// Generate content
const result = await api.generateContent({
    content_type: 'newsletter_article',
    topic: 'Aquascaping basics for beginners',
    target_audience: 'beginners',
    max_length: 1500
});

console.log(result.data.content);
```

### Python SDK

```python
import requests
from typing import Dict, List, Optional, Any
import time

class AquaSceneAPI:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}")
    
    # Content generation
    def generate_content(self, request: Dict[str, Any]) -> Dict:
        """Generate single piece of content"""
        return self._request('POST', '/api/v1/generate', request)
    
    def generate_batch(self, batch_request: Dict[str, Any]) -> Dict:
        """Generate multiple pieces of content"""
        return self._request('POST', '/api/v1/batch/generate', batch_request)
    
    def get_batch_status(self, batch_id: str) -> Dict:
        """Get status of batch generation"""
        return self._request('GET', f'/api/v1/batch/{batch_id}/status')
    
    def wait_for_batch(self, batch_id: str, poll_interval: int = 5, timeout: int = 300) -> Dict:
        """Wait for batch completion with polling"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_batch_status(batch_id)
            
            if status['data']['status'] in ['completed', 'failed']:
                return status
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Batch {batch_id} did not complete within {timeout} seconds")
    
    # Content management
    def create_content(self, content: Dict[str, Any]) -> Dict:
        """Create new content piece"""
        return self._request('POST', '/api/v1/content', content)
    
    def get_content(self, content_id: str) -> Dict:
        """Get content by ID"""
        return self._request('GET', f'/api/v1/content/{content_id}')
    
    def list_content(self, **filters) -> Dict:
        """List content with optional filters"""
        query_params = '&'.join([f"{k}={v}" for k, v in filters.items()])
        endpoint = f'/api/v1/content?{query_params}' if query_params else '/api/v1/content'
        return self._request('GET', endpoint)
    
    def update_content(self, content_id: str, updates: Dict[str, Any]) -> Dict:
        """Update existing content"""
        return self._request('PUT', f'/api/v1/content/{content_id}', updates)
    
    def delete_content(self, content_id: str) -> Dict:
        """Delete content"""
        return self._request('DELETE', f'/api/v1/content/{content_id}')
    
    # Subscriber management
    def create_subscriber(self, subscriber: Dict[str, Any]) -> Dict:
        """Create new subscriber"""
        return self._request('POST', '/api/v1/subscribers', subscriber)
    
    def get_subscriber(self, subscriber_id: str) -> Dict:
        """Get subscriber by ID"""
        return self._request('GET', f'/api/v1/subscribers/{subscriber_id}')
    
    def list_subscribers(self, **filters) -> Dict:
        """List subscribers with optional filters"""
        query_params = '&'.join([f"{k}={v}" for k, v in filters.items()])
        endpoint = f'/api/v1/subscribers?{query_params}' if query_params else '/api/v1/subscribers'
        return self._request('GET', endpoint)

class APIError(Exception):
    """Custom exception for API errors"""
    pass

# Usage example
if __name__ == "__main__":
    # Initialize API client
    api = AquaSceneAPI('http://localhost:8000', 'your-token')
    
    try:
        # Generate content
        content_request = {
            'content_type': 'newsletter_article',
            'topic': 'Setting up your first planted aquarium',
            'target_audience': 'beginners',
            'max_length': 1500,
            'seo_keywords': ['planted aquarium', 'aquascaping', 'beginner guide']
        }
        
        result = api.generate_content(content_request)
        print(f"Generated content: {result['data']['content'][:100]}...")
        
        # Create content in system
        content_data = {
            'title': 'Beginner Aquascaping Guide',
            'content': result['data']['content'],
            'content_type': 'newsletter_article',
            'status': 'draft'
        }
        
        created = api.create_content(content_data)
        print(f"Created content with ID: {created['data']['id']}")
        
        # List all newsletter articles
        articles = api.list_content(content_type='newsletter_article', status='published')
        print(f"Found {len(articles['data']['items'])} published articles")
        
    except APIError as e:
        print(f"API error: {e}")
```

### cURL Examples

#### Generate Content
```bash
curl -X POST "http://localhost:8001/api/v1/generate" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "newsletter_article",
    "topic": "Setting up your first planted aquarium",
    "target_audience": "beginners",
    "max_length": 1500
  }'
```

#### Create Subscriber
```bash
curl -X POST "http://localhost:8004/api/v1/subscribers" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "preferences": {
      "content_types": ["newsletter"],
      "frequency": "weekly"
    }
  }'
```

#### Send Newsletter
```bash
curl -X POST "http://localhost:8003/api/v1/newsletters/send" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "550e8400-e29b-41d4-a716-446655440000",
    "template_id": "weekly-digest",
    "recipients": {
      "segment_ids": ["seg-beginners"]
    }
  }'
```

## Webhooks

### Webhook Configuration

Configure webhooks to receive real-time notifications about events:

```http
POST /api/v1/webhooks
Authorization: Bearer {token}
Content-Type: application/json

{
    "url": "https://your-app.com/webhooks/aquascene",
    "events": [
        "content.generated",
        "content.published",
        "newsletter.sent",
        "subscriber.created"
    ],
    "secret": "your-webhook-secret"
}
```

### Webhook Events

#### Content Generated
```json
{
    "event": "content.generated",
    "timestamp": "2025-08-06T12:00:00Z",
    "data": {
        "content_id": "gen-550e8400-e29b-41d4-a716-446655440000",
        "content_type": "newsletter_article",
        "quality_score": 8.7,
        "generation_time": 12.5,
        "cost": 0.05
    }
}
```

#### Newsletter Sent
```json
{
    "event": "newsletter.sent",
    "timestamp": "2025-08-06T12:00:00Z",
    "data": {
        "campaign_id": "camp-550e8400-e29b-41d4-a716-446655440000",
        "recipients_count": 1250,
        "subject": "This Week in Aquascaping"
    }
}
```

### Webhook Security

Verify webhook authenticity using HMAC signatures:

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## Testing and Development

### Health Check Endpoints

All services provide health check endpoints for monitoring:

```http
GET /health
```

**Response:**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 86400,
    "dependencies": {
        "database": "healthy",
        "redis": "healthy",
        "external_apis": "healthy"
    },
    "timestamp": "2025-08-06T12:00:00Z"
}
```

### Development Environment

For development and testing, use the following base URLs:

- Content Manager: `http://localhost:8000`
- AI Processor: `http://localhost:8001`
- Web Scraper: `http://localhost:8002`
- Distributor: `http://localhost:8003`
- Subscriber Manager: `http://localhost:8004`
- Admin Dashboard: `http://localhost:3001`

### Postman Collection

A Postman collection is available at `/docs/postman/aquascene-api-collection.json` with:

- Pre-configured requests for all endpoints
- Environment variables for easy switching between dev/staging/prod
- Test scripts for response validation
- Authentication setup

Import the collection and set up your environment variables:

```json
{
    "base_url": "http://localhost:8000",
    "ai_base_url": "http://localhost:8001",
    "auth_token": "your-jwt-token-here"
}
```

## Support and Feedback

### API Versioning

The API uses semantic versioning:
- Major version changes: Breaking changes (URL path: `/api/v2/`)
- Minor version changes: New features (backwards compatible)
- Patch version changes: Bug fixes

### Deprecation Policy

- Deprecated endpoints remain functional for 6 months
- Deprecation warnings included in response headers
- Migration guides provided for breaking changes

### Getting Help

1. **Documentation**: Check this API reference and service-specific docs
2. **Health Status**: Monitor service health endpoints
3. **Error Logs**: Check structured error responses and logging
4. **Support**: Contact the development team for assistance

---

**Document Status:** Complete ✅  
**Last Updated:** August 6, 2025  
**API Version:** 1.0.0  
**Owner:** AquaScene Development Team