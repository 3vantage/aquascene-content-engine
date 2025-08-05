# Instagram Automation System for Aquascaping Content

A production-ready Instagram automation system specifically designed for aquascaping content creators. Features compliant Instagram Business API integration, intelligent content scheduling, visual template generation, and comprehensive analytics.

## 🌟 Features

### Core Automation
- **Compliant Instagram Business API Integration** - Proper rate limiting and error handling
- **Intelligent Content Scheduling** - Optimal timing analysis based on audience engagement
- **Automated Posting** - 1-3 posts daily without manual intervention
- **Content Queue Management** - Approval workflows and validation

### Content Generation
- **Visual Template System** - Pre-designed templates for different post types
- **Hashtag Optimization** - Dynamic hashtag generation for Bulgarian and international markets
- **Bilingual Support** - Bulgarian and English content templates
- **Content Validation** - Brand compliance and policy checking

### Analytics & Optimization
- **Performance Tracking** - Comprehensive engagement and reach analytics
- **Optimal Timing Analysis** - Data-driven posting schedule optimization
- **Hashtag Performance** - Track and optimize hashtag effectiveness
- **Content Insights** - Performance analysis by content type

### Safety & Reliability
- **Error Handling** - Comprehensive retry logic and recovery mechanisms
- **Rate Limiting** - Respects Instagram API limits with buffer
- **Health Monitoring** - System health checks and alerts
- **Circuit Breaker** - Prevents cascading failures

## 🏗️ Architecture

```
instagram/
├── api/                    # Instagram Business API client
├── scheduler/              # Content scheduling and timing
├── queue/                  # Content queue management
├── templates/              # Visual and content templates
├── analytics/              # Performance tracking
├── utils/                  # Utilities (hashtags, error handling)
├── config/                 # Configuration management
└── instagram_automation.py # Main orchestrator
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
cd /path/to/aquascene-content-engine/services/distributor/instagram

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create configuration file:
```bash
python instagram_automation.py --create-config
```

Edit `config/config.yaml` with your Instagram Business API credentials:
```yaml
instagram_api:
  access_token: "YOUR_ACCESS_TOKEN"
  business_account_id: "YOUR_BUSINESS_ACCOUNT_ID"
  app_id: "YOUR_APP_ID"
  app_secret: "YOUR_APP_SECRET"
```

### 3. Environment Variables

Set required environment variables:
```bash
export INSTAGRAM_ACCESS_TOKEN="your_access_token"
export INSTAGRAM_BUSINESS_ACCOUNT_ID="your_business_account_id"
export ENVIRONMENT="production"
```

### 4. Run the System

```bash
# Start the automation system
python instagram_automation.py

# Or with custom config
python instagram_automation.py --config path/to/config.yaml
```

## 📊 Content Types Supported

### Educational Content
- **Beginner Guides** - Step-by-step aquascaping tutorials
- **Plant Care Tips** - Specific plant requirements and care
- **Equipment Reviews** - Lighting, filtration, CO2 systems
- **Technique Tutorials** - Trimming, planting, maintenance

### Showcase Content
- **Tank Transformations** - Before/after aquascape changes
- **Plant Spotlights** - Featured plant profiles
- **Fish Spotlights** - Compatible fish for planted tanks
- **Community Features** - User-submitted aquascapes

### Engagement Content
- **Behind the Scenes** - Setup process and maintenance
- **Community Q&A** - Answering common questions
- **Polls and Questions** - Interactive engagement posts
- **Partnership Content** - Brand collaborations

## 🎨 Visual Templates

The system includes pre-designed visual templates:

- **Educational Carousels** - Multi-slide tutorials
- **Before/After Comparisons** - Transformation showcases
- **Plant/Fish Profiles** - Detailed species information
- **Quote Cards** - Inspirational aquascaping quotes
- **Step-by-Step Tutorials** - Process documentation

## 🏷️ Hashtag Strategy

### Bulgarian Market
- Primary: `#аквариум #акваскейп #растения #природа`
- Niche: `#аквариумнирастения #подводнаградина #акваскейпинг`
- Location: `#софия #пловдив #варна #българия`

### International Market
- Popular: `#aquascaping #plantedtank #aquarium #natureaquarium`
- Niche: `#iwagumi #dutchstyle #aquascape #co2aquarium`
- Community: `#aquascaper #plantedtankcommunity #freshwateraquarium`

## 📈 Analytics Dashboard

Track performance with built-in analytics:

- **Engagement Rates** - Likes, comments, saves per post
- **Reach and Impressions** - Audience growth metrics
- **Optimal Posting Times** - Best times for your audience
- **Hashtag Performance** - Most effective hashtags
- **Content Type Analysis** - Which content performs best

## ⚙️ Configuration Options

### Posting Schedule
```yaml
scheduling:
  default_posts_per_day: 2
  min_interval_hours: 4
  optimal_hours: [9, 13, 17, 19, 21]
  timezone: "Europe/Sofia"
```

### Content Settings
```yaml
content:
  default_language: "bg"
  bilingual_posts: true
  max_hashtags: 30
  auto_hashtag_generation: true
```

### Analytics
```yaml
analytics:
  collection_enabled: true
  collection_interval_hours: 6
  retention_days: 90
  performance_alerts_enabled: true
```

## 🔒 Security Features

- **Token Encryption** - API tokens stored encrypted
- **Rate Limit Compliance** - Respects Instagram API limits
- **Error Recovery** - Automatic retry with exponential backoff
- **Health Monitoring** - System health checks and alerts
- **Audit Logging** - Complete action history

## 🛠️ Development

### Project Structure
```
instagram/
├── api/
│   └── instagram_client.py      # Instagram Business API client
├── scheduler/
│   └── content_scheduler.py     # Scheduling and timing logic
├── queue/
│   └── content_queue.py         # Content management and validation
├── templates/
│   ├── content_templates.py     # Text content templates
│   └── visual/
│       └── template_generator.py # Visual template generation
├── analytics/
│   └── performance_tracker.py   # Analytics and insights
├── utils/
│   ├── hashtag_optimizer.py     # Hashtag research and optimization
│   └── error_handler.py         # Error handling and recovery
└── config/
    └── config_manager.py        # Configuration management
```

### Adding New Templates

1. **Content Templates** - Add to `templates/content_templates.py`
2. **Visual Templates** - Add to `templates/visual/template_generator.py`
3. **Post Types** - Update `scheduler/content_scheduler.py`

### Custom Hashtag Categories

Add new hashtag categories in `utils/hashtag_optimizer.py`:
```python
def _initialize_hashtag_data(self):
    # Add your custom hashtags here
    custom_hashtags = {
        "your_hashtag": (post_count, engagement_rate, hashtag_type)
    }
```

## 📋 Production Deployment

### System Requirements
- Python 3.8+
- 2GB RAM minimum
- 10GB storage for databases and logs
- Stable internet connection

### Deployment Steps

1. **Server Setup**
```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
```

2. **Application Setup**
```bash
# Install requirements
pip install -r requirements.txt

# Set up configuration
python instagram_automation.py --create-config
# Edit config/config.yaml with production settings
```

3. **Service Configuration**
```bash
# Create systemd service (optional)
sudo cp instagram-automation.service /etc/systemd/system/
sudo systemctl enable instagram-automation
sudo systemctl start instagram-automation
```

### Monitoring

- **Log Files** - Check `instagram_automation.log`
- **Health Endpoint** - Monitor system health
- **Database Backups** - Automatic database backups
- **Performance Metrics** - Built-in analytics dashboard

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues

1. **API Rate Limits** - System automatically handles rate limiting
2. **Authentication Errors** - Check your access token and permissions
3. **Image Upload Failures** - Verify image URLs are accessible
4. **Database Locks** - System uses proper database connection pooling

### Getting Help

- Check the logs in `instagram_automation.log`
- Review configuration in `config/config.yaml`
- Monitor system health endpoint
- Check Instagram Business API status

## 🔄 Updates

The system includes automatic updates for:
- Hashtag performance data
- Optimal posting times
- Content template effectiveness
- Error pattern recognition

Regular maintenance includes:
- Database cleanup (based on retention policy)
- Performance report generation
- Security token rotation
- System health monitoring

---

Built with ❤️ for the aquascaping community in Bulgaria and beyond.