# Getting Started Guide - AquaScene Content Engine

**Version:** 1.0  
**Last Updated:** August 6, 2025  
**Target Audience:** New Users (All Personas)

## Welcome to AquaScene Content Engine!

This guide will help you get up and running with the AquaScene Content Engine quickly and efficiently. Whether you're a content creator, system administrator, or business user, this guide provides step-by-step instructions tailored to your needs.

## Quick Start Overview

The AquaScene Content Engine is an AI-powered platform that generates high-quality aquascaping content for newsletters, social media, blogs, and more. Here's what you can accomplish in your first 30 minutes:

- ✅ Access the admin dashboard
- ✅ Generate your first piece of content  
- ✅ Download and use generated content
- ✅ Set up automated content workflows

## Prerequisites

Before you begin, ensure you have:

### For Content Creators
- Access to the AquaScene admin dashboard
- At least one AI service API key (OpenAI, Anthropic, or local Ollama setup)
- Basic understanding of your content marketing goals

### For System Administrators  
- Docker and Docker Compose installed
- Access to server/hosting environment
- Basic familiarity with containerized applications

### For Business Users
- Access credentials provided by your system administrator
- Understanding of your business content requirements

## Path 1: Content Creator Quick Start

*Perfect for marketing managers and content strategists*

### Step 1: Access the Dashboard (2 minutes)

1. **Navigate to the Admin Dashboard**
   - Open your web browser
   - Go to the dashboard URL provided by your administrator
   - Default local URL: `http://localhost:3001`

2. **Log In**
   - Enter your username and password
   - If no authentication is set up, you'll go directly to the dashboard

3. **Familiarize Yourself with the Interface**
   - Main navigation on the left sidebar
   - Dashboard shows system status and statistics
   - Each service has its own dedicated page

### Step 2: Generate Your First Content (5 minutes)

1. **Go to AI Processor**
   - Click "AI Processor" in the left sidebar
   - This is where content generation happens

2. **Try a Single Content Generation**
   ```
   Content Type: Newsletter Article
   Topic: "Top 5 Beginner-Friendly Aquatic Plants"
   Target Audience: Beginners
   SEO Keywords: beginner aquatic plants, easy aquarium plants
   Brand Voice: Friendly and educational
   Optimize Content: Yes
   ```

3. **Click "Generate Content"**
   - Wait for the AI to generate your content (usually 30-60 seconds)
   - Review the generated content for quality and accuracy

4. **Download Your Content**
   - Use the download button to save the content
   - Content is available in multiple formats (HTML, Markdown, Plain Text)

### Step 3: Set Up Batch Content Generation (10 minutes)

1. **Navigate to Batch Generation**
   - In the AI Processor section, find the batch generation option
   - This allows you to create multiple content pieces at once

2. **Create a Weekly Content Plan**
   ```
   Batch Name: "Weekly Aquascaping Content - Week 1"
   Processing Mode: Concurrent
   Max Concurrent: 3 (adjust based on your API limits)
   
   Content Requests:
   1. Newsletter Article: "Aquarium Maintenance Checklist"
   2. Instagram Caption: "Beautiful nature aquarium showcase"
   3. How-To Guide: "Setting up CO2 injection system"
   4. Product Review: "Best LED lights for planted tanks"
   ```

3. **Monitor Progress**
   - Watch the real-time progress indicator
   - Review individual pieces as they complete
   - Download the batch when finished

### Step 4: Explore Airtable Integration (5 minutes)

1. **Go to Airtable Workflow**
   - Click "Airtable Workflow" in the sidebar
   - This feature helps organize and track your content

2. **Connect Your Airtable Base (Optional)**
   - Enter your Airtable API key and Base ID
   - Test the connection to ensure it works
   - This will help you manage content metadata and organization

### Step 5: Review and Optimize (8 minutes)

1. **Check Content Quality**
   - Review generated content for accuracy
   - Ensure brand voice consistency
   - Make note of any adjustments needed

2. **Test Distribution**
   - Go to the Distributor section
   - Review options for newsletter and social media distribution
   - Set up basic distribution preferences

3. **Monitor System Performance**
   - Return to the Dashboard
   - Check service health status
   - Review generation statistics

## Path 2: System Administrator Quick Start

*Perfect for IT managers and DevOps professionals*

### Step 1: System Deployment (15 minutes)

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd aquascene-content-engine
   ```

2. **Configure Environment**
   ```bash
   # Copy environment template
   cp services/ai-processor/.env.example services/ai-processor/.env
   
   # Edit .env file with your API keys
   nano services/ai-processor/.env
   ```

3. **Deploy with Docker Compose**
   ```bash
   # Production deployment
   docker-compose up -d
   
   # Verify all services are running
   docker-compose ps
   ```

4. **Verify System Health**
   ```bash
   # Check core AI processor
   curl http://localhost:8001/health
   
   # Check all service endpoints
   curl http://localhost:8000/health  # Content Manager
   curl http://localhost:8002/health  # Web Scraper
   curl http://localhost:8003/health  # Distributor
   curl http://localhost:8004/health  # Subscriber Manager
   ```

### Step 2: Monitoring Setup (10 minutes)

1. **Access Grafana Dashboard**
   - Navigate to `http://localhost:3000`
   - Default login: admin/admin (change immediately)
   - Review pre-configured dashboards

2. **Configure Prometheus Monitoring**
   - Navigate to `http://localhost:9090`
   - Verify all targets are being scraped
   - Check that metrics are being collected

3. **Set Up Alerting (Optional)**
   - Configure alert rules in Prometheus
   - Set up notification channels in Grafana
   - Test alert delivery

### Step 3: User Management (5 minutes)

1. **Review User Access**
   - Document how users will access the system
   - Set up any required authentication
   - Create user documentation

2. **Configure Service Settings**
   - Review AI model configurations
   - Set rate limits and quotas
   - Configure backup schedules

### Step 4: Integration Testing (15 minutes)

1. **Test End-to-End Workflow**
   ```bash
   # Run the complete test suite
   ./run-full-test-suite.sh
   ```

2. **Verify External Integrations**
   - Test AI service API connections
   - Verify email service integration
   - Test file storage and retrieval

3. **Performance Validation**
   - Run load tests if needed
   - Verify resource usage is within limits
   - Test failover scenarios

## Path 3: Business User Quick Start

*Perfect for business owners and partnership managers*

### Step 1: Dashboard Overview (5 minutes)

1. **Access the System**
   - Get login credentials from your administrator
   - Navigate to the dashboard URL
   - Review the main dashboard for key metrics

2. **Understand Key Metrics**
   - **Content Generation Count**: How much content is being created
   - **Cost Savings**: Money saved vs. manual content creation
   - **Quality Scores**: Average quality of generated content
   - **System Uptime**: Reliability metrics

### Step 2: Review Content Output (10 minutes)

1. **Sample Content Generation**
   - Work with your content team to generate sample content
   - Review quality and brand alignment
   - Compare to manually created content

2. **Assess Business Impact**
   - Calculate time savings per week
   - Review cost per piece of content
   - Evaluate content quality and consistency

### Step 3: Partnership Value Assessment (5 minutes)

1. **Green Aqua Content Focus**
   - Review how content supports partnership goals
   - Assess product-focused educational content
   - Evaluate market authority building

2. **ROI Calculation**
   - Compare old content creation costs vs. new costs
   - Factor in time savings and increased volume
   - Calculate partnership value enhancement

### Step 4: Strategic Planning (10 minutes)

1. **Content Strategy Alignment**
   - Ensure generated content matches business goals
   - Review content types and topics
   - Plan for scaling content production

2. **Success Metrics Definition**
   - Define what success looks like for your business
   - Set up tracking for key business metrics
   - Plan regular review meetings

## Common First-Day Tasks

### For All Users

#### Understanding the System
- [ ] Review the main dashboard and understand what each metric means
- [ ] Familiarize yourself with the navigation and main sections
- [ ] Understand your role and permissions within the system

#### Testing Basic Functionality
- [ ] Generate at least one piece of content successfully
- [ ] Review the quality and accuracy of generated content
- [ ] Test downloading and using generated content

#### Setting Expectations
- [ ] Understand typical generation times (30-90 seconds per piece)
- [ ] Learn about quality validation and fact-checking features
- [ ] Know when and how to contact support for help

### Content Creator Specific
- [ ] Set up your preferred content types and templates
- [ ] Configure brand voice and style preferences
- [ ] Test batch generation with a small set of content
- [ ] Review integration options for your existing tools

### Administrator Specific
- [ ] Verify all services are running and healthy
- [ ] Set up monitoring and alerting
- [ ] Document system configuration and access procedures
- [ ] Test backup and recovery procedures

### Business User Specific
- [ ] Review cost savings and ROI calculations
- [ ] Understand how the system supports business goals
- [ ] Plan integration with existing business processes
- [ ] Set up reporting and review schedules

## Success Checklist

By the end of your first session, you should be able to:

- ✅ Access the AquaScene Content Engine dashboard
- ✅ Generate at least one piece of high-quality content
- ✅ Understand the content generation workflow
- ✅ Navigate the main sections of the system
- ✅ Know where to find help and documentation
- ✅ Have a plan for regular usage based on your role

## Next Steps

### After Your First Day
1. **Content Creators**: Set up regular content generation schedules
2. **Administrators**: Implement monitoring and backup procedures  
3. **Business Users**: Plan content strategy integration with business goals

### Week 1 Goals
- Generate and use content in your regular workflows
- Identify optimization opportunities
- Train other team members who will use the system
- Set up any required integrations with existing tools

### Month 1 Goals
- Measure and report on ROI and business impact
- Optimize content generation strategies based on results
- Implement advanced features like custom templates
- Plan for scaling content production

## Getting Help

### Documentation Resources
- **[User Personas and Stories](USER-PERSONAS-AND-STORIES.md)** - Understand different user types and their needs
- **[Admin Dashboard Guide](ADMIN-DASHBOARD-GUIDE.md)** - Detailed dashboard documentation
- **[API Reference](API-REFERENCE.md)** - Complete API documentation for advanced users
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Solutions for common issues

### Support Channels
- **System Health**: Check the Dashboard for real-time system status
- **Error Messages**: Most errors include specific guidance for resolution
- **Log Files**: Administrators can access detailed logs for troubleshooting

### Best Practices
- Start with single content generation before trying batch processing
- Always review generated content before publishing
- Monitor system performance metrics regularly
- Keep API keys secure and rotate them regularly

---

**Tips for Success:**
- Take it slow - the system is powerful but requires some learning
- Focus on quality over quantity initially
- Use the monitoring features to understand system performance
- Don't hesitate to experiment with different content types and settings

Welcome to the future of AI-powered aquascaping content creation! 🌱

---

**Document Status:** Complete ✅  
**Review Date:** August 6, 2025  
**Next Review:** September 6, 2025  
**Owner:** AquaScene UX Team