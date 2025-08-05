# AquaScene Content Generation Engine - AI Agent Guide

## 🎯 Project Overview
This is the AI-powered content generation engine for AquaScene, a Bulgarian aquascaping startup building authority to secure Green Aqua partnership. The system automates content creation, newsletter distribution, and social media management.

## 🏗️ Architecture
```
Microservices Architecture:
├── Content Manager API (Port 8000) - Main content management
├── AI Processor (Port 8001) - GPT-4/Claude content generation
├── Web Scraper (Port 8002) - Ethical content acquisition
├── Distributor (Port 8003) - Newsletter + Instagram automation
├── Subscriber Manager (Port 8004) - User segmentation
└── Admin Dashboard (Port 3001) - Management interface
```

## 📁 Repository Structure
```
/aquascene-content-engine/
├── services/               # Microservices
│   ├── ai-processor/      # AI content generation
│   ├── distributor/       # Content distribution
│   │   ├── instagram/     # Instagram automation
│   │   └── templates/     # Newsletter templates
│   └── [other services]   # Placeholders for future
├── infrastructure/        # Deployment configs
│   ├── database/         # PostgreSQL schemas
│   ├── nginx/           # Reverse proxy
│   └── redis/           # Caching configs
├── docker-compose.yml    # Development environment
├── docker-compose.production.yml # Production
└── .env.example         # Configuration template
```

## 🚀 Quick Start
```bash
# Setup
cp .env.example .env
# Edit .env with API keys

# Start all services
docker-compose up -d

# Access admin dashboard
open http://localhost:3001
# Login: admin@aquascene.bg / admin
```

## 🔑 Key Features
- **AI Content Generation**: GPT-4/Claude integration for articles, newsletters, social posts
- **Newsletter Automation**: 5 professional templates with personalization
- **Instagram Business API**: Compliant automation with visual templates
- **Web Scraping**: Ethical content acquisition from aquascaping sources
- **Subscriber Management**: Segmentation, personalization, analytics
- **Admin Dashboard**: Complete management interface

## 💡 Important Contexts
- **Target Market**: Bulgarian aquascaping enthusiasts
- **Partnership Goal**: Green Aqua Hungary
- **Content Strategy**: Education + Authority building
- **Languages**: English, Bulgarian, Hungarian
- **Revenue Model**: Newsletter monetization + Partnership commissions

## 📊 Services Details

### AI Processor Service
- Location: `/services/ai-processor/`
- Purpose: Generate high-quality content
- Models: GPT-4, Claude, Ollama (local)
- Templates: Newsletter, Instagram, Blog
- Quality: Fact-checking, brand voice, SEO

### Distributor Service
- Location: `/services/distributor/`
- Newsletter: HTML/Text templates, SendGrid
- Instagram: Business API, visual generation
- Scheduling: Optimal timing, batch sending
- Analytics: Open rates, engagement tracking

### Instagram Automation
- Location: `/services/distributor/instagram/`
- Posts: 1-3 daily with optimal timing
- Visuals: Pillow-based template generation
- Hashtags: Bulgarian + International optimization
- Compliance: Rate limiting, error handling

### Newsletter Templates
- Location: `/services/distributor/templates/newsletters/`
- Types: Weekly digest, How-to, Announcements, Community, Expert interviews
- Format: HTML + Plain text + YAML config
- Personalization: Subscriber tokens, segmentation
- Green Aqua: Partnership integration points

## 🛠️ Development Commands
```bash
# Run specific service
docker-compose up ai-processor

# View logs
docker-compose logs -f distributor

# Run tests
docker-compose exec ai-processor pytest

# Database access
docker-compose exec postgres psql -U aquascene

# Redis CLI
docker-compose exec redis redis-cli
```

## 📝 Environment Variables
Key variables in `.env`:
- `OPENAI_API_KEY` - GPT-4 access
- `ANTHROPIC_API_KEY` - Claude access
- `SENDGRID_API_KEY` - Email sending
- `INSTAGRAM_ACCESS_TOKEN` - Instagram API
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection

## 🔗 Related Repositories
- **aquascene**: Main platform with 15 themes
- **aquascene-waitlist**: Waitlist SPA on GitHub Pages
- **3vantage-docs**: Comprehensive documentation

## 📚 Documentation
Full documentation: https://github.com/3vantage/3vantage-docs

Key guides:
- `/guides/developer-guide.md` - Development workflow
- `/guides/installation-guide.md` - Setup instructions
- `/guides/ai-content-generation.md` - AI pipeline
- `/guides/newsletter-system.md` - Email automation
- `/guides/instagram-automation.md` - Social media

## 🎯 Business Goals
1. Build authority in Bulgarian aquascaping market
2. Generate 1000+ newsletter subscribers
3. Achieve 25%+ email open rates
4. Secure Green Aqua partnership
5. €2-5 monthly revenue per subscriber

## 🐛 Common Issues
- **Docker not starting**: Check ports 8000-8004, 3001
- **AI not generating**: Verify API keys in .env
- **Instagram failing**: Check access token expiration
- **Database errors**: Run migrations with init script
- **Email not sending**: Verify SendGrid configuration

## 📞 Contact
- Owner: gerasimovkris@3vantage.com
- Organization: 3vantage
- Location: Bulgaria