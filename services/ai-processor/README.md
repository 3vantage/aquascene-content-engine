# AI Content Processor Service

The AI Content Processor is a sophisticated content generation service designed specifically for aquascaping content. It provides multi-LLM support, intelligent routing, quality validation, and batch processing capabilities.

## 🌟 Features

### Multi-LLM Support
- **OpenAI GPT-4/GPT-3.5**: Premium content generation with advanced reasoning
- **Anthropic Claude**: Excellent for creative and engaging content
- **Local Ollama**: Privacy-focused local model support for sensitive operations

### Intelligent Content Generation
- **Smart Routing**: Automatically selects the best LLM based on content type and requirements
- **Fallback System**: Seamless failover between providers for reliability
- **Quality Validation**: Comprehensive validation using aquascaping knowledge base
- **Template Integration**: Works with existing newsletter and Instagram templates

### Advanced Features
- **Batch Processing**: Efficient processing of multiple content requests
- **Content Optimization**: SEO, engagement, and social media optimization
- **Real-time Monitoring**: Performance metrics and health monitoring
- **Aquascaping Knowledge Base**: Specialized knowledge for accurate content

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Content Processor                     │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Web Service (Port 8001)                          │
├─────────────────────────────────────────────────────────────┤
│  Content Orchestrator                                      │
│  ├── LLM Client Manager (OpenAI, Claude, Ollama)          │
│  ├── Quality Validator (Accuracy, Brand, SEO)             │
│  ├── Template Manager (Newsletter, Instagram, etc.)       │
│  ├── Content Optimizer (SEO, Engagement, Social)          │
│  └── Batch Processor (Concurrent, Sequential, Adaptive)   │
├─────────────────────────────────────────────────────────────┤
│  Knowledge Base                                            │
│  ├── Aquascaping Plants Database                          │
│  ├── Equipment Knowledge                                   │
│  ├── Techniques & Best Practices                          │
│  └── Common Problems & Solutions                          │
├─────────────────────────────────────────────────────────────┤
│  Monitoring & Observability                               │
│  ├── Performance Metrics                                  │
│  ├── Health Checks                                        │
│  ├── Alert System                                         │
│  └── Structured Logging                                   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker (optional)
- At least one LLM API key (OpenAI or Anthropic)

### Installation

1. **Clone and Setup**
   ```bash
   cd services/ai-processor
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Run the Service**
   ```bash
   python src/main.py
   ```

   Or with Docker:
   ```bash
   docker build -t ai-processor .
   docker run -p 8001:8001 --env-file .env ai-processor
   ```

### Docker Compose Integration

Add to your main docker-compose.yml:

```yaml
services:
  ai-processor:
    build: ./services/ai-processor
    ports:
      - "8001:8001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=postgresql://user:pass@db:5432/content_engine
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./services/distributor/templates:/app/templates:ro
    restart: unless-stopped
```

## 📖 API Usage

### Generate Single Content

```bash
curl -X POST "http://localhost:8001/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "newsletter_article",
    "topic": "Setting up your first planted aquarium",
    "target_audience": "beginners",
    "seo_keywords": ["planted aquarium", "aquascaping", "beginner guide"],
    "brand_voice": "friendly and educational",
    "max_length": 1500,
    "optimize_content": true
  }'
```

### Batch Content Generation

```bash
curl -X POST "http://localhost:8001/batch/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Content Batch",
    "processing_mode": "concurrent",
    "max_concurrent": 3,
    "requests": [
      {
        "content_type": "newsletter_article",
        "topic": "Top 5 beginner aquatic plants"
      },
      {
        "content_type": "instagram_caption",
        "topic": "Beautiful nature aquarium showcase"
      },
      {
        "content_type": "how_to_guide",
        "topic": "How to trim carpet plants"
      }
    ]
  }'
```

### Monitor Service Health

```bash
curl "http://localhost:8001/health"
curl "http://localhost:8001/stats"
```

## 🎯 Content Types Supported

| Content Type | Description | Optimizations |
|--------------|-------------|---------------|
| `newsletter_article` | Educational articles for newsletters | SEO, Readability, CTA |
| `instagram_caption` | Social media captions with hashtags | Engagement, Hashtags, Visual |
| `how_to_guide` | Step-by-step instructional content | Structure, Clarity, Completeness |
| `product_review` | Product evaluations and reviews | Objectivity, Balance, Detail |
| `seo_blog_post` | SEO-optimized blog articles | Keywords, Structure, Meta |
| `community_post` | Community engagement content | Discussion, Questions, Social |
| `weekly_digest` | Summary and roundup content | Conciseness, Links, Highlights |
| `expert_interview` | Q&A and interview formats | Authority, Quotes, Structure |

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | * |
| `ANTHROPIC_API_KEY` | Anthropic API key | - | * |
| `OLLAMA_BASE_URL` | Ollama service URL | `http://localhost:11434` | |
| `MAX_CONCURRENT_REQUESTS` | Max concurrent processing | `5` | |
| `DEFAULT_TEMPERATURE` | LLM temperature setting | `0.7` | |
| `ENABLE_CACHING` | Enable response caching | `true` | |
| `LOG_LEVEL` | Logging level | `INFO` | |

### Content Optimization Settings

```python
# Enable/disable optimization features
ENABLE_SEO_OPTIMIZATION=true
ENABLE_ENGAGEMENT_OPTIMIZATION=true  
ENABLE_SOCIAL_OPTIMIZATION=true

# Brand configuration
BRAND_VOICE="professional and educational"
TARGET_AUDIENCE="aquascaping enthusiasts"
COMPANY_NAME="AquaScene"
```

## 🧠 LLM Provider Selection

The service intelligently routes requests to the best LLM provider based on:

- **Content Type**: Different models excel at different content types
- **Cost Optimization**: Balance quality with cost efficiency
- **Performance**: Route to fastest available provider
- **Availability**: Automatic failover to backup providers

### Routing Strategies

1. **Cost Optimized**: Prioritizes lower-cost providers
2. **Quality First**: Uses premium models for best results
3. **Speed First**: Routes to fastest responding provider
4. **Balanced**: Optimal mix of cost, quality, and speed
5. **Round Robin**: Distributes load evenly

## 📊 Quality Validation

Content goes through comprehensive quality checks:

### Accuracy Validation
- Fact-checking against aquascaping knowledge base
- Plant care information verification
- Equipment recommendation validation

### Brand Consistency
- Voice and tone analysis
- Brand guideline compliance
- Terminology consistency

### Content Structure
- Format requirements validation
- Length and readability checks
- SEO optimization verification

### Aquascaping Expertise
- Technical accuracy validation
- Best practice compliance
- Common mistake detection

## 📈 Monitoring & Observability

### Health Endpoints
- `/health` - Service health status
- `/stats` - Performance statistics
- `/metrics` - Prometheus metrics (if enabled)

### Key Metrics Tracked
- Request throughput and latency
- Error rates by provider and content type
- Quality scores and validation results
- Resource usage (CPU, memory)
- Cost tracking and optimization

### Alerting
Automatic alerts for:
- High error rates (>5% warning, >10% critical)
- Slow response times (>15s warning, >30s critical)
- Resource exhaustion (>80% memory, >90% CPU)
- Provider availability issues

## 🔧 Development

### Running Tests
```bash
pytest tests/ -v --cov=src
```

### Code Quality
```bash
black src/
flake8 src/
mypy src/
```

### Local Development with Ollama

1. **Install Ollama**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Pull Models**
   ```bash
   ollama pull llama3.1:8b
   ollama pull mistral:7b
   ```

3. **Configure Environment**
   ```bash
   export OLLAMA_BASE_URL=http://localhost:11434
   export OLLAMA_MODELS=llama3.1:8b,mistral:7b
   ```

### Adding New Content Types

1. **Define Content Type**
   ```python
   # In base_client.py
   class ContentType(Enum):
       NEW_TYPE = "new_type"
   ```

2. **Add Templates**
   ```bash
   mkdir -p templates/new_type
   # Add template files
   ```

3. **Configure Validation**
   ```python
   # In quality_validator.py
   def _validate_new_type_specific(self, content: str) -> ValidationScore:
       # Add validation logic
   ```

4. **Update Optimization**
   ```python
   # In content_optimizer.py
   self.content_rules[ContentType.NEW_TYPE] = {
       "max_length": 2000,
       "require_cta": True
   }
   ```

## 🚨 Troubleshooting

### Common Issues

**Service Won't Start**
- Check API keys are configured
- Verify all dependencies installed
- Check port 8001 is available

**Poor Content Quality**
- Review knowledge base entries
- Adjust temperature settings
- Check validation thresholds

**High Latency**
- Enable caching
- Reduce concurrent requests
- Check LLM provider status

**Memory Issues**
- Reduce batch sizes
- Enable adaptive processing
- Monitor system resources

### Debugging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
export ENABLE_DEBUG_ENDPOINTS=true
```

Check service status:
```bash
curl http://localhost:8001/health | jq .
```

Monitor logs:
```bash
docker logs -f ai-processor
```

## 🤝 Integration

### With Newsletter Service
The AI processor integrates seamlessly with the existing newsletter templates:

```python
# Newsletter generation with template
response = await client.post("/generate", {
    "content_type": "newsletter_article",
    "template_name": "weekly-digest",
    "topic": "Latest aquascaping trends"
})
```

### With Instagram Service
Works with Instagram automation for caption generation:

```python
# Instagram caption with hashtag optimization
response = await client.post("/generate", {
    "content_type": "instagram_caption", 
    "topic": "Beautiful planted tank setup",
    "optimization_strategy": "social_focused"
})
```

### With Content Management
Integrates with existing content workflows:

```python
# Batch generation for content calendar
response = await client.post("/batch/generate", {
    "name": "Monthly Content Calendar",
    "requests": content_calendar_requests
})
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Code Style
- Follow PEP 8
- Use type hints
- Add docstrings to public methods
- Write comprehensive tests

## 📄 License

This project is part of the AquaScene Content Engine and follows the same licensing terms.

## 🆘 Support

For issues and questions:
1. Check this documentation
2. Review the troubleshooting section
3. Check existing GitHub issues
4. Create a new issue with detailed reproduction steps

---

**Built with ❤️ for the aquascaping community**