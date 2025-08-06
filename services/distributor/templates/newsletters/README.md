# AquaScene Newsletter Templates

## Overview

This directory contains professional HTML email templates designed specifically for the aquascaping content engine. Each template is optimized for email client compatibility, mobile responsiveness, and integration with the Green Aqua partnership.

## Template Categories

### 1. Weekly Digest (`weekly-digest.html`)
**Purpose**: Main newsletter with multiple modular sections for comprehensive weekly content.

**Key Features**:
- Featured aquascape spotlight with technical specifications
- Plant of the week with care requirements
- Community showcase section
- Tech product reviews and comparisons
- Quick maintenance tips
- Contest and event announcements
- Green Aqua partnership integration

**Best For**: Regular weekly newsletter sends, comprehensive content delivery, subscriber retention

**Personalization**: High - includes subscriber name, experience level, and location-based content

### 2. How-To Guide (`how-to-guide.html`)
**Purpose**: Step-by-step tutorial template for detailed aquascaping instructions.

**Key Features**:
- Progress indicator and step numbering
- Materials and tools checklist with Green Aqua links
- Visual step-by-step instructions with images
- Troubleshooting section for common issues
- Maintenance schedule for first 30 days
- Professional tips and warnings

**Best For**: Educational content, skill development, new aquascaper onboarding

**Personalization**: Medium - adjusts difficulty level and provides personalized tips

### 3. Announcements (`announcements.html`)
**Purpose**: Product launches, partnerships, events, and major news announcements.

**Key Features**:
- Urgency indicators with dynamic styling
- Product launch sections with features and pricing
- Partnership announcement layouts
- Event details with speaker profiles
- Countdown timers for limited-time offers
- Social proof testimonials

**Best For**: Product launches, event promotions, partnership announcements, flash sales

**Personalization**: Medium - subscriber-specific offers and location-based events

### 4. Community Showcase (`community-showcase.html`)
**Purpose**: Highlighting community member submissions and achievements.

**Key Features**:
- Featured aquascaper profiles with tank specifications
- Community gallery with submission highlights
- Success story transformations with before/after images
- Monthly challenge spotlights
- Member achievement recognition
- Social media integration

**Best For**: Community engagement, user-generated content, member retention

**Personalization**: High - community-specific content and achievement recognition

### 5. Expert Interview (`expert-interview.html`)
**Purpose**: In-depth Q&A format interviews with industry professionals.

**Key Features**:
- Expert profile with credentials and statistics
- Structured Q&A format with highlighted quotes
- Featured works gallery
- Professional tips and recommendations
- Product recommendations with Green Aqua integration
- Media integration (video/podcast links)

**Best For**: Thought leadership, educational content, expert knowledge sharing

**Personalization**: Low - content is expert-focused but includes subscriber greeting

## Technical Specifications

### Email Client Compatibility
- ✅ Gmail (Desktop & Mobile)
- ✅ Outlook (2016+, Web, Mobile)
- ✅ Apple Mail (macOS & iOS)
- ✅ Yahoo Mail
- ✅ Thunderbird
- ✅ Android Email Apps

### Responsive Design
- Mobile-first approach
- Breakpoint: 600px
- Fluid layouts for all screen sizes
- Touch-friendly buttons (minimum 44px height)
- Optimized typography for mobile reading

### Performance Optimization
- Inline CSS for maximum compatibility
- Optimized image loading with fallbacks
- Maximum email size: 1-2MB depending on template
- Compressed inline styles
- Fallback fonts for broad compatibility

## Usage Instructions

### 1. Template Selection
Choose the appropriate template based on your content type:
- **Weekly content**: Use `weekly-digest.html`
- **Educational content**: Use `how-to-guide.html`
- **Product/event announcements**: Use `announcements.html`
- **Community content**: Use `community-showcase.html`
- **Expert content**: Use `expert-interview.html`

### 2. Content Population
Each template uses a variable substitution system. Refer to the corresponding `.yml` configuration file for available variables.

**Example variable usage**:
```html
<!-- In template -->
<h1>{{newsletter_title|default:"AquaScene Weekly"}}</h1>
<p>Hello {{subscriber_name|default:"Fellow Aquascaper"}}!</p>

<!-- With data -->
newsletter_title: "AquaScene Weekly - Nature Aquarium Special"
subscriber_name: "Maria"
```

### 3. Green Aqua Integration
All templates include Green Aqua partnership elements:
- Partnership badges
- Product recommendation links
- Affiliate tracking parameters
- Co-branded styling elements

**Green Aqua Link Format**:
```html
<a href="{{green_aqua_link}}?ref=aquascene&campaign={{campaign_id}}">
```

### 4. Personalization
Templates support multiple personalization levels:

**Basic Personalization**:
- Subscriber name
- Email preferences
- Subscription date

**Advanced Personalization**:
- Experience level (Beginner/Intermediate/Advanced)
- Geographic location
- Previous purchase history
- Engagement patterns

### 5. A/B Testing
Templates are designed for A/B testing:
- Subject line variations
- Content order changes
- CTA button styles
- Send time optimization

## Template Customization

### CSS Modifications
All styles are inline for email compatibility. Key style areas:

**Color Scheme**:
```css
/* Primary Colors */
--primary-blue: #1976d2;
--primary-green: #4caf50;
--aqua-teal: #006d75;
--green-aqua: #2e7d32;

/* Secondary Colors */
--light-blue: #e3f2fd;
--light-green: #e8f5e8;
--warning-orange: #ff9800;
--accent-purple: #9c27b0;
```

**Typography**:
```css
font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
/* Headers: 24-36px */
/* Body: 16px */
/* Captions: 14px */
/* Small text: 12px */
```

### Content Sections
Templates use modular sections that can be:
- Reordered based on content priority
- Hidden if content not available
- Duplicated for multiple items
- Customized per subscriber segment

### Image Requirements
**Featured Images**:
- Format: JPG, PNG, WebP
- Minimum width: 600px
- Maximum file size: 1MB
- Aspect ratio: 16:9 or 4:3 recommended

**Profile Images**:
- Format: JPG, PNG
- Dimensions: 120x120px minimum
- Circular crop compatible
- Maximum file size: 200KB

## AI Content Generation

### Content Hints
Each template includes AI generation hints in the configuration files:

```yaml
ai_generation:
  content_areas:
    - featured_setup: "Generate aquascape descriptions with technical specifications"
    - plant_spotlight: "Provide plant care information and design usage tips"
  tone: "Educational yet accessible, encouraging, community-focused"
  expertise_level: "Mixed audience from beginners to advanced"
```

### Content Guidelines
**Tone**: Educational, encouraging, community-focused
**Voice**: Professional but approachable
**Technical Level**: Accessible to beginners, valuable to experts
**Length**: Optimized for email scanning behavior

## Integration Examples

### Basic Template Usage
```javascript
// Template rendering example
const template = await loadTemplate('weekly-digest.html');
const content = {
  newsletter_title: "AquaScene Weekly",
  week_number: 23,
  theme: "Nature Aquarium Fundamentals",
  subscriber_name: "Maria",
  featured_setup: {
    hero_image: "https://example.com/aquascape.jpg",
    designer_name: "Alexander Petrov",
    tank_size: "120L (60x40x50cm)"
  }
};

const renderedEmail = renderTemplate(template, content);
```

### Green Aqua Integration
```javascript
// Product recommendation integration
const productRecommendation = {
  name: "ADA Pro-Tweezers Straight",
  green_aqua_link: "https://greenaqua.hu/products/ada-pro-tweezers?ref=aquascene&utm_source=newsletter&utm_campaign=weekly_digest",
  reason: "Essential for precise plant placement"
};
```

### Personalization Implementation
```javascript
// Dynamic personalization
const personalizedContent = {
  subscriber_name: subscriber.name,
  experience_level: subscriber.experience_level,
  location: subscriber.location,
  plant_spotlight: getPlantForExperienceLevel(subscriber.experience_level),
  tips: getLocationSpecificTips(subscriber.location)
};
```

## Analytics and Tracking

### Built-in Tracking
Templates include tracking for:
- Email opens (tracking pixel)
- Link clicks (UTM parameters)
- Social shares (tracking URLs)
- CTA button engagement
- Section-specific interactions

### UTM Parameters
Standard UTM structure:
```
utm_source=newsletter
utm_medium=email
utm_campaign={{campaign_name}}
utm_content={{template_name}}
utm_term={{subscriber_segment}}
```

### Green Aqua Affiliate Tracking
```
?ref=aquascene
&utm_source=newsletter
&utm_medium=email
&campaign={{campaign_id}}
&subscriber={{subscriber_id}}
```

## Best Practices

### Content Strategy
1. **Consistency**: Use the same template type for similar content
2. **Personalization**: Always include subscriber name and relevant content
3. **Value-First**: Ensure every email provides clear value to subscribers
4. **Community Focus**: Highlight community members and achievements
5. **Educational Approach**: Balance entertainment with education

### Technical Best Practices
1. **Testing**: Test across multiple email clients before sending
2. **Preview Text**: Always set preview text for better inbox appearance
3. **Subject Lines**: Keep under 50 characters for mobile compatibility
4. **Images**: Always include alt text for accessibility
5. **CTAs**: Use clear, action-oriented button text

### Green Aqua Partnership
1. **Integration**: Include partnership elements naturally in content
2. **Value**: Ensure product recommendations add genuine value
3. **Transparency**: Clearly identify affiliate relationships
4. **Quality**: Only recommend products that align with content quality standards

## Troubleshooting

### Common Issues
**Images not displaying**:
- Check image URLs are publicly accessible
- Ensure proper alt text is included
- Verify image dimensions match template requirements

**Layout breaking in Outlook**:
- Ensure all table-based layouts are properly nested
- Check for missing `mso` conditional comments
- Verify inline styles are complete

**Mobile display issues**:
- Test on actual mobile devices, not just desktop browser resize
- Check touch target sizes (minimum 44px)
- Verify text remains readable at mobile sizes

### Testing Checklist
- [ ] All variables populated correctly
- [ ] Images display across email clients
- [ ] Links work and include proper tracking
- [ ] Mobile responsive design functions properly
- [ ] Personalization elements render correctly
- [ ] Green Aqua integration elements present
- [ ] Spam score acceptable (<5.0)
- [ ] Accessibility standards met

## Support and Updates

### Template Maintenance
Templates are maintained with:
- Regular email client compatibility updates
- Security and performance improvements
- New feature additions based on user feedback
- Green Aqua partnership integration updates

### Version Control
All templates follow semantic versioning:
- Major version: Breaking changes to template structure
- Minor version: New features or significant enhancements
- Patch version: Bug fixes and minor improvements

### Community Feedback
Template improvements are driven by:
- User analytics and engagement data
- Community feedback and requests
- Email client updates and changes
- Industry best practice evolution

For technical support or template customization requests, contact the AquaScene development team.