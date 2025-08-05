# Newsletter Template Integration Guide

## Overview

This guide provides comprehensive instructions for integrating the AquaScene newsletter templates into your content engine pipeline. It covers everything from basic template rendering to advanced AI content generation and analytics tracking.

## Architecture Overview

```
Content Engine Pipeline:
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  Template Engine │───▶│  Email Service  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Generator  │    │  Personalization │    │   Analytics     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Green Aqua API  │    │ Subscriber Data  │    │  Performance    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Template Engine Integration

### 1. Template Loading and Caching

```javascript
// Template loader with caching
class TemplateLoader {
  constructor(templatePath) {
    this.templatePath = templatePath;
    this.cache = new Map();
  }

  async loadTemplate(templateName) {
    if (this.cache.has(templateName)) {
      return this.cache.get(templateName);
    }

    const htmlTemplate = await fs.readFile(
      `${this.templatePath}/${templateName}.html`, 
      'utf-8'
    );
    const textTemplate = await fs.readFile(
      `${this.templatePath}/${templateName}.txt`, 
      'utf-8'
    );
    const config = await yaml.load(
      await fs.readFile(`${this.templatePath}/${templateName}.yml`, 'utf-8')
    );

    const template = {
      html: htmlTemplate,
      text: textTemplate,
      config: config,
      name: templateName
    };

    this.cache.set(templateName, template);
    return template;
  }
}
```

### 2. Content Validation

```javascript
// Content validator based on template configuration
class ContentValidator {
  static validate(content, templateConfig) {
    const errors = [];
    const variables = templateConfig.variables;

    for (const [key, spec] of Object.entries(variables)) {
      if (spec.required && !(key in content)) {
        errors.push(`Required field '${key}' is missing`);
        continue;
      }

      if (key in content) {
        const value = content[key];
        
        // Type validation
        if (spec.type === 'string' && typeof value !== 'string') {
          errors.push(`Field '${key}' must be a string`);
        }
        
        // Length validation
        if (spec.max_length && value.length > spec.max_length) {
          errors.push(`Field '${key}' exceeds maximum length of ${spec.max_length}`);
        }

        // Enum validation
        if (spec.enum && !spec.enum.includes(value)) {
          errors.push(`Field '${key}' must be one of: ${spec.enum.join(', ')}`);
        }

        // URL validation
        if (spec.type === 'url') {
          try {
            new URL(value);
          } catch {
            errors.push(`Field '${key}' must be a valid URL`);
          }
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors: errors
    };
  }
}
```

### 3. Template Rendering Engine

```javascript
// Main template renderer with Handlebars
const handlebars = require('handlebars');

class NewsletterRenderer {
  constructor(templateLoader) {
    this.templateLoader = templateLoader;
    this.setupHelpers();
  }

  setupHelpers() {
    // Date formatting helper
    handlebars.registerHelper('date', function(date, format) {
      return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    });

    // Default value helper
    handlebars.registerHelper('default', function(value, defaultValue) {
      return value || defaultValue;
    });

    // Green Aqua affiliate link helper
    handlebars.registerHelper('gaLink', function(url, campaign, subscriber) {
      const params = new URLSearchParams({
        ref: 'aquascene',
        utm_source: 'newsletter',
        utm_campaign: campaign,
        subscriber_id: subscriber.id
      });
      return `${url}?${params.toString()}`;
    });

    // Conditional sections
    handlebars.registerHelper('ifEquals', function(arg1, arg2, options) {
      return (arg1 == arg2) ? options.fn(this) : options.inverse(this);
    });
  }

  async render(templateName, content, subscriber) {
    const template = await this.templateLoader.loadTemplate(templateName);
    
    // Validate content
    const validation = ContentValidator.validate(content, template.config);
    if (!validation.valid) {
      throw new Error(`Content validation failed: ${validation.errors.join(', ')}`);
    }

    // Add subscriber context
    const renderContext = {
      ...content,
      subscriber: subscriber,
      generated_at: new Date().toISOString(),
      template_version: template.config.template.version
    };

    // Compile and render
    const htmlCompiled = handlebars.compile(template.html);
    const textCompiled = handlebars.compile(template.text);

    return {
      html: htmlCompiled(renderContext),
      text: textCompiled(renderContext),
      subject: this.generateSubject(templateName, content, subscriber),
      metadata: {
        template: templateName,
        subscriber_id: subscriber.id,
        campaign_id: content.campaign_id,
        rendered_at: new Date().toISOString()
      }
    };
  }

  generateSubject(templateName, content, subscriber) {
    const subjectTemplates = {
      'weekly-digest': `${content.newsletter_title || 'AquaScene Weekly'} - Week ${content.week_number}`,
      'how-to-guide': `Guide: ${content.guide_title}`,
      'announcements': content.announcement_title,
      'community-showcase': `Community Spotlight: ${content.showcase_title}`,
      'expert-interview': `Expert Interview: ${content.expert?.name || 'Industry Leader'}`
    };

    let subject = subjectTemplates[templateName] || 'AquaScene Newsletter';
    
    // Personalize if subscriber name available
    if (subscriber.first_name) {
      subject = `${subscriber.first_name}, ${subject}`;
    }

    return subject;
  }
}
```

## AI Content Generation Integration

### 1. Content Generation Service

```javascript
class AIContentGenerator {
  constructor(openaiClient, templateLoader) {
    this.openai = openaiClient;
    this.templateLoader = templateLoader;
  }

  async generateContent(templateName, parameters, subscriber) {
    const template = await this.templateLoader.loadTemplate(templateName);
    const aiHints = template.config.ai_generation;

    const prompt = this.buildPrompt(templateName, aiHints, parameters, subscriber);
    
    const response = await this.openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        {
          role: "system",
          content: `You are an expert aquascaping content creator writing for the AquaScene newsletter. 
                   Generate content that is ${aiHints.tone}. 
                   Target audience expertise level: ${aiHints.expertise_level}.
                   Always maintain educational value while being engaging.`
        },
        {
          role: "user",
          content: prompt
        }
      ],
      temperature: 0.7,
      max_tokens: 2000
    });

    return this.parseAIResponse(response.choices[0].message.content, template.config);
  }

  buildPrompt(templateName, aiHints, parameters, subscriber) {
    const prompts = {
      'weekly-digest': this.buildWeeklyDigestPrompt(aiHints, parameters, subscriber),
      'how-to-guide': this.buildHowToPrompt(aiHints, parameters, subscriber),
      'announcements': this.buildAnnouncementPrompt(aiHints, parameters, subscriber),
      'community-showcase': this.buildCommunityPrompt(aiHints, parameters, subscriber),
      'expert-interview': this.buildInterviewPrompt(aiHints, parameters, subscriber)
    };

    return prompts[templateName] || this.buildGenericPrompt(aiHints, parameters);
  }

  buildWeeklyDigestPrompt(aiHints, parameters, subscriber) {
    return `Generate content for a weekly aquascaping newsletter with these sections:
    
    Theme: ${parameters.theme || 'General Aquascaping'}
    Week number: ${parameters.week_number || 1}
    
    Required sections:
    1. Featured Setup: Create an inspiring aquascape description with technical specs
    2. Plant Spotlight: Detail care requirements and design uses for ${parameters.plant_name || 'a popular aquatic plant'}
    3. Community Feature: Write about a community member's success story
    4. Tech Talk: Review a piece of aquascaping equipment
    5. Quick Tips: Provide 5 practical maintenance tips
    
    Subscriber context: ${subscriber.experience_level || 'mixed'} level aquascaper
    Location: ${subscriber.location || 'general'}
    
    Make content specific, actionable, and encouraging. Include technical details but keep explanations accessible.`;
  }

  buildHowToPrompt(aiHints, parameters, subscriber) {
    return `Create a comprehensive step-by-step aquascaping guide for: ${parameters.guide_title}
    
    Guide specifications:
    - Difficulty: ${parameters.difficulty_level || 'Intermediate'}
    - Estimated time: ${parameters.estimated_time || '2-3 hours'}
    - Budget: ${parameters.estimated_cost || '€150-300'}
    
    Include:
    1. Engaging introduction explaining the value and outcome
    2. Complete materials list with specific products
    3. 6-8 detailed steps with tips and warnings
    4. Common troubleshooting issues and solutions
    5. 30-day maintenance schedule
    
    Target audience: ${subscriber.experience_level || 'intermediate'} aquascaper
    Tone: Clear, instructional, encouraging, safety-conscious
    
    Each step should be independently completable with clear success indicators.`;
  }

  parseAIResponse(content, templateConfig) {
    // Parse structured AI response into template variables
    // This would include sophisticated parsing logic to extract
    // structured data from the AI response
    
    try {
      // Attempt to parse as JSON if structured
      if (content.startsWith('{')) {
        return JSON.parse(content);
      }
      
      // Otherwise, parse as markdown sections
      return this.parseMarkdownSections(content, templateConfig);
    } catch (error) {
      console.error('Failed to parse AI response:', error);
      return { error: 'Failed to parse generated content' };
    }
  }
}
```

### 2. Green Aqua API Integration

```javascript
class GreenAquaIntegration {
  constructor(apiKey, affiliateId) {
    this.apiKey = apiKey;
    this.affiliateId = affiliateId;
    this.baseUrl = 'https://api.greenaqua.hu/v1';
  }

  async getProductRecommendations(category, priceRange) {
    const response = await fetch(`${this.baseUrl}/products/recommendations`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        category: category,
        price_range: priceRange,
        affiliate_id: this.affiliateId,
        include_links: true
      })
    });

    const data = await response.json();
    return data.products.map(product => ({
      ...product,
      green_aqua_link: this.addAffiliateTracking(product.url)
    }));
  }

  async getPlantInformation(plantName) {
    const response = await fetch(`${this.baseUrl}/plants/search?name=${encodeURIComponent(plantName)}`, {
      headers: {
        'Authorization': `Bearer ${this.apiKey}`
      }
    });

    const data = await response.json();
    if (data.plants.length > 0) {
      const plant = data.plants[0];
      return {
        name: plant.name,
        scientific_name: plant.scientific_name,
        difficulty: plant.care_level,
        growth_rate: plant.growth_rate,
        light_requirements: plant.light,
        co2_requirements: plant.co2,
        temperature_range: plant.temperature,
        ph_range: plant.ph,
        care_tips: plant.care_instructions,
        source_link: this.addAffiliateTracking(plant.product_url)
      };
    }
    
    return null;
  }

  addAffiliateTracking(url, campaign = 'newsletter') {
    const params = new URLSearchParams({
      ref: 'aquascene',
      utm_source: 'newsletter',
      utm_medium: 'email',
      utm_campaign: campaign,
      affiliate: this.affiliateId
    });
    
    return `${url}?${params.toString()}`;
  }
}
```

### 3. Personalization Engine

```javascript
class PersonalizationEngine {
  constructor(subscriberDb) {
    this.subscriberDb = subscriberDb;
  }

  async personalizeContent(content, subscriber, templateName) {
    const personalizedContent = { ...content };

    // Basic personalization
    personalizedContent.subscriber_name = subscriber.first_name || 'Fellow Aquascaper';

    // Experience-level based content
    if (templateName === 'weekly-digest') {
      personalizedContent.tips = await this.getExperienceLevelTips(subscriber.experience_level);
      personalizedContent.plant_spotlight = await this.getPlantForLevel(subscriber.experience_level);
    }

    // Location-based personalization
    if (subscriber.location) {
      personalizedContent.local_events = await this.getLocalEvents(subscriber.location);
      personalizedContent.seasonal_tips = await this.getSeasonalTips(subscriber.location);
    }

    // Engagement-based personalization
    const engagementData = await this.subscriberDb.getEngagementHistory(subscriber.id);
    if (engagementData.preferred_content_types) {
      personalizedContent.content_priority = this.prioritizeContent(
        personalizedContent, 
        engagementData.preferred_content_types
      );
    }

    // Purchase history based recommendations
    if (subscriber.purchase_history) {
      personalizedContent.product_recommendations = await this.getPersonalizedProducts(
        subscriber.purchase_history
      );
    }

    return personalizedContent;
  }

  async getExperienceLevelTips(experienceLevel) {
    const tipSets = {
      beginner: [
        "Start with easy plants like Java Fern and Anubias - they're nearly impossible to kill",
        "Change 25% of your water weekly - consistency matters more than perfect parameters",
        "Don't rush adding CO2 - master the basics first with low-tech plants"
      ],
      intermediate: [
        "Trim plants before they reach the surface to maintain proportions",
        "Use a drop checker to monitor CO2 levels - aim for lime green color",
        "Consider adding trace elements if plants show yellowing despite good NPK"
      ],
      advanced: [
        "Experiment with different hardscape materials to create unique textures",
        "Fine-tune your fertilization based on plant uptake rates and growth patterns",
        "Document your setups with detailed parameters for future reference"
      ]
    };

    return tipSets[experienceLevel] || tipSets.intermediate;
  }
}
```

## Email Service Integration

### 1. Multi-Provider Email Service

```javascript
class EmailService {
  constructor(providers) {
    this.providers = providers; // e.g., SendGrid, Mailgun, AWS SES
    this.primaryProvider = providers[0];
  }

  async sendNewsletter(renderedContent, subscribers, options = {}) {
    const results = [];
    
    for (const subscriber of subscribers) {
      try {
        const personalizedContent = await this.personalizeForSend(
          renderedContent, 
          subscriber, 
          options
        );

        const result = await this.sendSingle(personalizedContent, subscriber, options);
        results.push(result);
        
        // Rate limiting
        await this.sleep(options.rateLimitMs || 100);
        
      } catch (error) {
        console.error(`Failed to send to ${subscriber.email}:`, error);
        results.push({
          subscriber_id: subscriber.id,
          success: false,
          error: error.message
        });
      }
    }

    return results;
  }

  async sendSingle(content, subscriber, options) {
    const emailData = {
      to: subscriber.email,
      from: options.from || 'hello@aquascene.com',
      subject: content.subject,
      html: content.html,
      text: content.text,
      headers: {
        'List-Unsubscribe': `<${options.unsubscribeUrl}?subscriber=${subscriber.id}>`,
        'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click'
      },
      tracking: {
        open_tracking: true,
        click_tracking: true,
        subscription_tracking: true
      },
      metadata: content.metadata
    };

    // Try primary provider first
    try {
      return await this.primaryProvider.send(emailData);
    } catch (error) {
      // Fallback to secondary providers
      for (let i = 1; i < this.providers.length; i++) {
        try {
          console.log(`Falling back to provider ${i} for ${subscriber.email}`);
          return await this.providers[i].send(emailData);
        } catch (fallbackError) {
          console.error(`Provider ${i} also failed:`, fallbackError);
        }
      }
      throw error;
    }
  }

  personalizeForSend(content, subscriber, options) {
    // Add tracking pixels and personalized links
    let personalizedHtml = content.html;
    let personalizedText = content.text;

    // Add tracking pixel
    const trackingPixel = `<img src="${options.trackingBaseUrl}/open/${subscriber.id}/${options.campaignId}" width="1" height="1" style="display: none;" />`;
    personalizedHtml = personalizedHtml.replace('</body>', `${trackingPixel}</body>`);

    // Replace tracking links
    const linkRegex = /href="([^"]+)"/g;
    personalizedHtml = personalizedHtml.replace(linkRegex, (match, url) => {
      if (url.startsWith('http')) {
        const trackedUrl = `${options.trackingBaseUrl}/click/${subscriber.id}/${options.campaignId}?url=${encodeURIComponent(url)}`;
        return `href="${trackedUrl}"`;
      }
      return match;
    });

    return {
      ...content,
      html: personalizedHtml,
      text: personalizedText
    };
  }
}
```

### 2. Analytics and Tracking

```javascript
class NewsletterAnalytics {
  constructor(database) {
    this.db = database;
  }

  async trackOpen(subscriberId, campaignId, userAgent, ip) {
    await this.db.events.create({
      type: 'email_open',
      subscriber_id: subscriberId,
      campaign_id: campaignId,
      timestamp: new Date(),
      metadata: {
        user_agent: userAgent,
        ip_address: this.anonymizeIP(ip)
      }
    });

    // Update subscriber engagement score
    await this.updateEngagementScore(subscriberId, 'open', 1);
  }

  async trackClick(subscriberId, campaignId, url, userAgent, ip) {
    await this.db.events.create({
      type: 'email_click',
      subscriber_id: subscriberId,
      campaign_id: campaignId,
      timestamp: new Date(),
      metadata: {
        clicked_url: url,
        user_agent: userAgent,
        ip_address: this.anonymizeIP(ip)
      }
    });

    // Update subscriber engagement score
    await this.updateEngagementScore(subscriberId, 'click', 3);

    // Track specific link categories
    if (url.includes('greenaqua.hu')) {
      await this.trackGreenAquaConversion(subscriberId, campaignId, url);
    }
  }

  async generateCampaignReport(campaignId) {
    const [opens, clicks, unsubscribes, complaints] = await Promise.all([
      this.db.events.count({ where: { campaign_id: campaignId, type: 'email_open' } }),
      this.db.events.count({ where: { campaign_id: campaignId, type: 'email_click' } }),
      this.db.events.count({ where: { campaign_id: campaignId, type: 'unsubscribe' } }),
      this.db.events.count({ where: { campaign_id: campaignId, type: 'spam_complaint' } })
    ]);

    const totalSent = await this.db.campaigns.findById(campaignId).total_sent;

    return {
      campaign_id: campaignId,
      total_sent: totalSent,
      opens: opens,
      clicks: clicks,
      unsubscribes: unsubscribes,
      complaints: complaints,
      open_rate: (opens / totalSent) * 100,
      click_rate: (clicks / totalSent) * 100,
      click_to_open_rate: opens > 0 ? (clicks / opens) * 100 : 0,
      unsubscribe_rate: (unsubscribes / totalSent) * 100,
      complaint_rate: (complaints / totalSent) * 100
    };
  }

  async updateEngagementScore(subscriberId, action, points) {
    const subscriber = await this.db.subscribers.findById(subscriberId);
    const currentScore = subscriber.engagement_score || 0;
    
    // Apply decay factor for time since last action
    const daysSinceLastAction = subscriber.last_action_date 
      ? (Date.now() - subscriber.last_action_date.getTime()) / (1000 * 60 * 60 * 24)
      : 30;
    
    const decayFactor = Math.max(0.5, 1 - (daysSinceLastAction / 30));
    const newScore = (currentScore * decayFactor) + points;

    await this.db.subscribers.update(subscriberId, {
      engagement_score: Math.min(100, newScore),
      last_action_date: new Date(),
      last_action_type: action
    });
  }
}
```

## Complete Integration Example

### 1. Newsletter Campaign Service

```javascript
class NewsletterCampaignService {
  constructor({
    templateLoader,
    renderer,
    aiGenerator,
    greenAquaApi,
    personalizationEngine,
    emailService,
    analytics,
    subscriberDb
  }) {
    this.templateLoader = templateLoader;
    this.renderer = renderer;
    this.aiGenerator = aiGenerator;
    this.greenAquaApi = greenAquaApi;
    this.personalizationEngine = personalizationEngine;
    this.emailService = emailService;
    this.analytics = analytics;
    this.subscriberDb = subscriberDb;
  }

  async createAndSendCampaign({
    templateName,
    contentParameters,
    subscriberSegment,
    scheduledTime,
    campaignName
  }) {
    try {
      // 1. Generate base content with AI
      console.log('Generating AI content...');
      const aiContent = await this.aiGenerator.generateContent(
        templateName,
        contentParameters,
        { experience_level: 'mixed' } // Default for bulk generation
      );

      // 2. Enhance with Green Aqua data
      console.log('Enhancing with Green Aqua data...');
      if (templateName === 'weekly-digest' && aiContent.plant_spotlight) {
        const plantData = await this.greenAquaApi.getPlantInformation(
          aiContent.plant_spotlight.name
        );
        if (plantData) {
          aiContent.plant_spotlight = { ...aiContent.plant_spotlight, ...plantData };
        }
      }

      // 3. Get subscriber list
      console.log('Loading subscribers...');
      const subscribers = await this.subscriberDb.getSegment(subscriberSegment);

      // 4. Create campaign record
      const campaign = await this.subscriberDb.campaigns.create({
        name: campaignName,
        template_name: templateName,
        content: aiContent,
        subscriber_count: subscribers.length,
        status: 'preparing',
        scheduled_time: scheduledTime,
        created_at: new Date()
      });

      // 5. If scheduled for later, save and schedule
      if (scheduledTime > new Date()) {
        await this.scheduleForLater(campaign.id, scheduledTime);
        return { campaign_id: campaign.id, status: 'scheduled' };
      }

      // 6. Send immediately
      return await this.sendCampaignNow(campaign.id, aiContent, subscribers);

    } catch (error) {
      console.error('Campaign creation failed:', error);
      throw error;
    }
  }

  async sendCampaignNow(campaignId, baseContent, subscribers) {
    console.log(`Sending campaign ${campaignId} to ${subscribers.length} subscribers...`);
    
    const results = [];
    let successCount = 0;
    let errorCount = 0;

    for (const subscriber of subscribers) {
      try {
        // Personalize content for this subscriber
        const personalizedContent = await this.personalizationEngine.personalizeContent(
          baseContent,
          subscriber,
          baseContent.template_name
        );

        // Render template
        const renderedContent = await this.renderer.render(
          baseContent.template_name,
          personalizedContent,
          subscriber
        );

        // Send email
        const sendResult = await this.emailService.sendSingle(
          renderedContent,
          subscriber,
          {
            campaignId: campaignId,
            trackingBaseUrl: process.env.TRACKING_BASE_URL,
            unsubscribeUrl: process.env.UNSUBSCRIBE_URL
          }
        );

        results.push({
          subscriber_id: subscriber.id,
          success: true,
          message_id: sendResult.message_id
        });
        successCount++;

      } catch (error) {
        console.error(`Failed to send to subscriber ${subscriber.id}:`, error);
        results.push({
          subscriber_id: subscriber.id,
          success: false,
          error: error.message
        });
        errorCount++;
      }

      // Rate limiting
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    // Update campaign with results
    await this.subscriberDb.campaigns.update(campaignId, {
      status: 'sent',
      sent_at: new Date(),
      success_count: successCount,
      error_count: errorCount,
      total_sent: successCount
    });

    console.log(`Campaign ${campaignId} completed: ${successCount} sent, ${errorCount} errors`);

    return {
      campaign_id: campaignId,
      status: 'completed',
      sent: successCount,
      errors: errorCount,
      results: results
    };
  }
}
```

### 2. Usage Example

```javascript
// Initialize all services
const templateLoader = new TemplateLoader('./templates/newsletters/');
const renderer = new NewsletterRenderer(templateLoader);
const aiGenerator = new AIContentGenerator(openaiClient, templateLoader);
const greenAquaApi = new GreenAquaIntegration(process.env.GREEN_AQUA_API_KEY, 'aquascene');
const personalizationEngine = new PersonalizationEngine(subscriberDb);
const emailService = new EmailService([sendgridProvider, mailgunProvider]);
const analytics = new NewsletterAnalytics(database);

const campaignService = new NewsletterCampaignService({
  templateLoader,
  renderer,
  aiGenerator,
  greenAquaApi,
  personalizationEngine,
  emailService,
  analytics,
  subscriberDb
});

// Create and send a weekly digest
async function sendWeeklyDigest() {
  try {
    const result = await campaignService.createAndSendCampaign({
      templateName: 'weekly-digest',
      contentParameters: {
        week_number: 23,
        theme: 'Nature Aquarium Fundamentals',
        featured_tank_style: 'iwagumi'
      },
      subscriberSegment: 'active_subscribers',
      campaignName: 'Weekly Digest - Week 23'
    });

    console.log('Campaign result:', result);
    
    // Generate analytics report after 24 hours
    setTimeout(async () => {
      const report = await analytics.generateCampaignReport(result.campaign_id);
      console.log('Campaign performance:', report);
    }, 24 * 60 * 60 * 1000);

  } catch (error) {
    console.error('Failed to send weekly digest:', error);
  }
}

// Schedule campaigns
sendWeeklyDigest();
```

## Performance Optimization

### 1. Template Caching Strategy

```javascript
class OptimizedTemplateCache {
  constructor(maxSize = 100) {
    this.cache = new Map();
    this.maxSize = maxSize;
    this.accessTimes = new Map();
  }

  get(key) {
    if (this.cache.has(key)) {
      this.accessTimes.set(key, Date.now());
      return this.cache.get(key);
    }
    return null;
  }

  set(key, value) {
    if (this.cache.size >= this.maxSize) {
      // Remove least recently used item
      let oldestKey = null;
      let oldestTime = Date.now();
      
      for (const [k, time] of this.accessTimes.entries()) {
        if (time < oldestTime) {
          oldestTime = time;
          oldestKey = k;
        }
      }
      
      if (oldestKey) {
        this.cache.delete(oldestKey);
        this.accessTimes.delete(oldestKey);
      }
    }
    
    this.cache.set(key, value);
    this.accessTimes.set(key, Date.now());
  }
}
```

### 2. Batch Processing

```javascript
class BatchProcessor {
  static async processBatch(items, processor, batchSize = 100, delayMs = 1000) {
    const results = [];
    
    for (let i = 0; i < items.length; i += batchSize) {
      const batch = items.slice(i, i + batchSize);
      
      console.log(`Processing batch ${Math.floor(i/batchSize) + 1}/${Math.ceil(items.length/batchSize)}`);
      
      const batchPromises = batch.map(item => processor(item));
      const batchResults = await Promise.allSettled(batchPromises);
      
      results.push(...batchResults);
      
      // Delay between batches to respect rate limits
      if (i + batchSize < items.length) {
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }
    }
    
    return results;
  }
}
```

This integration guide provides a complete framework for implementing the AquaScene newsletter templates in a production environment with AI content generation, personalization, analytics, and performance optimization.