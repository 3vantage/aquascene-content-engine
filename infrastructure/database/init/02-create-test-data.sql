-- AquaScene Content Engine - Test Data Creation Script
-- This script creates sample data for development and testing
-- Version: 1.0

-- Only run in development or test environments
DO $$
BEGIN
    IF current_setting('server_version_num')::int >= 140000 THEN
        -- PostgreSQL 14+ version check
        IF NOT EXISTS (SELECT 1 FROM pg_settings WHERE name = 'cluster_name' AND setting LIKE '%production%') THEN
            RAISE NOTICE 'Creating test data for development environment...';
        ELSE
            RAISE EXCEPTION 'Test data creation is not allowed in production environment';
        END IF;
    END IF;
END $$;

-- ===================
-- SAMPLE CONTENT CATEGORIES AND TAGS
-- ===================

-- Additional content categories for testing
INSERT INTO content_categories (name, slug, description, parent_id) VALUES
('Advanced Techniques', 'advanced-techniques', 'Expert-level aquascaping methods', 1),
('Lighting Systems', 'lighting-systems', 'LED and lighting equipment', 3),
('CO2 Systems', 'co2-systems', 'Carbon dioxide injection systems', 3),
('Hardscape Materials', 'hardscape-materials', 'Rocks, driftwood, and substrates', 1),
('Nano Aquascapes', 'nano-aquascapes', 'Small tank aquascaping', 4),
('Competition Layouts', 'competition-layouts', 'Contest-winning aquascapes', 4),
('Aquatic Moss', 'aquatic-moss', 'Moss species and cultivation', 2),
('Carpeting Plants', 'carpeting-plants', 'Ground cover plant species', 2),
('Stem Plants', 'stem-plants', 'Fast-growing background plants', 2),
('Epiphytes', 'epiphytes', 'Plants that grow on hardscape', 2)
ON CONFLICT (name) DO NOTHING;

-- Sample content tags
INSERT INTO content_tags (name, slug, description) VALUES
('beginner-friendly', 'beginner-friendly', 'Suitable for aquascaping beginners'),
('high-tech', 'high-tech', 'Requires CO2 and high lighting'),
('low-tech', 'low-tech', 'Natural method without CO2'),
('dutch-style', 'dutch-style', 'Dutch aquascaping style'),
('nature-style', 'nature-style', 'Nature aquarium style'),
('iwagumi', 'iwagumi', 'Japanese stone garden style'),
('biotope', 'biotope', 'Natural habitat recreation'),
('maintenance', 'maintenance', 'Tank maintenance topics'),
('troubleshooting', 'troubleshooting', 'Problem-solving content'),
('seasonal', 'seasonal', 'Season-specific advice')
ON CONFLICT (name) DO NOTHING;

-- ===================
-- SAMPLE SCRAPED CONTENT
-- ===================

-- Sample raw content from scraping
INSERT INTO raw_content (source_url, source_domain, content_type, title, content, metadata, processed, word_count, language) VALUES
(
    'https://www.greenaqua.hu/en/article/beginner-aquascaping-guide',
    'greenaqua.hu',
    'article',
    'Complete Beginner''s Guide to Aquascaping',
    'Aquascaping is the art of creating beautiful underwater landscapes in aquariums. This comprehensive guide will walk you through the basics of getting started with your first aquascape. We''ll cover essential equipment, plant selection, and basic design principles that will help you create stunning underwater gardens.',
    '{"author": "Green Aqua Team", "publish_date": "2024-01-15", "tags": ["beginner", "guide", "basics"]}',
    true,
    156,
    'en'
),
(
    'https://tropica.com/en/plant-care/co2-systems-explained',
    'tropica.com',
    'guide',
    'CO2 Systems for Planted Aquariums Explained',
    'Carbon dioxide is essential for healthy aquatic plant growth. In this detailed guide, we explore different CO2 systems available for planted aquariums, from simple DIY setups to professional grade systems. Learn about injection methods, diffusion techniques, and how to achieve optimal CO2 levels.',
    '{"category": "equipment", "difficulty": "intermediate", "read_time": "8 minutes"}',
    true,
    287,
    'en'
),
(
    'https://www.adana.co.jp/en/aquajournal/the-art-of-nature-aquarium',
    'adana.co.jp',
    'article',
    'The Art of Nature Aquarium Design',
    'Nature Aquarium design philosophy emphasizes creating natural underwater landscapes that evoke feelings of serenity and wonder. This article explores the principles developed by Takashi Amano and how modern aquascapers can apply these concepts to create breathtaking aquatic displays.',
    '{"style": "nature-aquarium", "author": "ADA Team", "featured_plants": ["Glossostigma", "Riccia"]}',
    true,
    342,
    'en'
)
ON CONFLICT (content_hash) DO NOTHING;

-- ===================
-- SAMPLE GENERATED CONTENT
-- ===================

-- Sample newsletter articles
INSERT INTO generated_content (
    content_type, title, content, summary, excerpt, template_used, 
    quality_score, readability_score, seo_score, status, tags, categories, 
    target_audience, tone, word_count, estimated_reading_time
) VALUES
(
    'newsletter_article',
    'Setting Up Your First Planted Aquarium: A Step-by-Step Guide',
    'Creating your first planted aquarium is an exciting journey into the world of aquascaping. This comprehensive guide will walk you through every step, from selecting the right tank size to choosing your first aquatic plants.

**Step 1: Choose the Right Tank Size**
For beginners, we recommend starting with a 20-40 gallon tank. This size provides enough space for creativity while being manageable for maintenance.

**Step 2: Select Your Substrate**
A good substrate is crucial for plant health. Consider aqua soil or a nutrient-rich substrate designed for planted tanks.

**Step 3: Plan Your Layout**
Sketch your design before adding water. Use the rule of thirds to create visual balance and natural flow.

**Step 4: Choose Beginner-Friendly Plants**
Start with easy plants like Java Fern, Anubias, and Amazon Sword. These species are forgiving and don''t require CO2 injection.

**Step 5: Set Up Proper Lighting**
LED lights designed for planted aquariums provide the right spectrum for photosynthesis while being energy-efficient.

Remember, patience is key in aquascaping. Your underwater garden will evolve and mature over time, becoming more beautiful with each passing month.',
    'Complete beginner''s guide to setting up your first planted aquarium with step-by-step instructions.',
    'Learn how to create your first planted aquarium with this comprehensive guide covering tank selection, substrate, plants, and lighting.',
    'how_to_guide',
    0.89,
    75,
    0.82,
    'published',
    ARRAY['beginner-friendly', 'low-tech', 'maintenance'],
    ARRAY['Aquascaping Basics', 'Plant Care'],
    'beginners',
    'educational_friendly',
    298,
    2,
    NOW() - INTERVAL '5 days'
),
(
    'instagram_caption',
    'Stunning Iwagumi Layout Inspiration',
    '🪨 The beauty of simplicity in this Iwagumi layout ✨

This minimalist aquascape demonstrates the power of negative space and careful stone placement. The Glossostigma carpet creates a perfect foreground, while the three carefully positioned stones follow the golden ratio principle.

Key elements that make this design work:
🔸 Odd number of stones (creates natural balance)
🔸 Varying stone sizes and heights
🔸 Clean carpeting plant for foreground
🔸 Ample negative space for visual breathing room

The Iwagumi style teaches us that sometimes less truly is more. What''s your favorite aquascaping style?

#aquascape #iwagumi #plantedtank #aquascaping #natureaquarium #minimalism #aquariumdesign #plantedaquarium #aquaticplants #underwaterart',
    'Instagram post featuring a beautiful Iwagumi-style aquascape with educational content about design principles.',
    'Discover the beauty of Iwagumi aquascaping with this stunning minimalist layout.',
    'instagram_post',
    0.91,
    68,
    0.75,
    'published',
    ARRAY['iwagumi', 'nature-style', 'beginner-friendly'],
    ARRAY['Tank Showcases', 'Aquascaping Basics'],
    'enthusiasts',
    'inspiring_educational',
    147,
    1,
    NOW() - INTERVAL '2 days'
),
(
    'newsletter_article',
    'Top 5 Low-Maintenance Aquatic Plants for Busy Aquascapers',
    'Not everyone has time for high-maintenance planted tanks, but that doesn''t mean you have to sacrifice beauty. These five aquatic plants are perfect for busy aquascapers who want gorgeous results with minimal effort.

**1. Java Fern (Microsorum pteropus)**
This hardy epiphyte thrives in low to moderate lighting and doesn''t require substrate planting. Simply attach it to driftwood or rocks, and it will grow slowly but steadily.

**2. Anubias (Anubias barteri)**
Another excellent epiphyte, Anubias is virtually indestructible. Its broad leaves add tropical appeal, and it tolerates a wide range of water conditions.

**3. Amazon Sword (Echinodorus amazonicus)**
This classic aquarium plant creates dramatic focal points with its large, sword-shaped leaves. Plant it in nutrient-rich substrate and provide moderate lighting.

**4. Java Moss (Taxiphyllum barbieri)**
Perfect for covering hardscape or creating natural carpets, Java Moss requires minimal care and helps improve water quality by absorbing excess nutrients.

**5. Cryptocoryne (Cryptocoryne wendtii)**
These rosette plants come in various colors and adapt well to different lighting conditions. Once established, they''re extremely low-maintenance.

**Pro Tips for Low-Maintenance Success:**
- Use liquid fertilizers for easier nutrient management
- Choose LED lights with built-in timers
- Perform regular water changes to prevent algae
- Start with fewer plants and add more as you gain experience

Remember, a successful low-maintenance tank is still a planned tank. Choose plants that complement each other and fit your available time commitment.',
    'Discover five low-maintenance aquatic plants perfect for busy aquascapers who want beautiful results with minimal effort.',
    'Learn about the best low-maintenance aquatic plants that thrive with minimal care while creating stunning underwater landscapes.',
    'article',
    0.87,
    72,
    0.84,
    'published',
    ARRAY['beginner-friendly', 'low-tech', 'maintenance'],
    ARRAY['Plant Care', 'Aquascaping Basics'],
    'beginners',
    'educational_friendly',
    312,
    2,
    NOW() - INTERVAL '1 week'
)
ON CONFLICT DO NOTHING;

-- ===================
-- SAMPLE SUBSCRIBERS
-- ===================

-- Sample subscriber data
INSERT INTO subscribers (email, first_name, last_name, country, source, status, tags) VALUES
('john.doe@email.com', 'John', 'Doe', 'United States', 'website_signup', 'active', ARRAY['beginner', 'newsletter']),
('sarah.smith@email.com', 'Sarah', 'Smith', 'Canada', 'instagram', 'active', ARRAY['advanced', 'plants']),
('mike.johnson@email.com', 'Mike', 'Johnson', 'United Kingdom', 'referral', 'active', ARRAY['equipment', 'diy']),
('emma.wilson@email.com', 'Emma', 'Wilson', 'Australia', 'website_signup', 'active', ARRAY['nano_tanks', 'beginner']),
('alex.brown@email.com', 'Alex', 'Brown', 'Germany', 'social_media', 'active', ARRAY['competition', 'advanced']),
('lisa.davis@email.com', 'Lisa', 'Davis', 'France', 'website_signup', 'confirmed', ARRAY['maintenance', 'troubleshooting']),
('tom.anderson@email.com', 'Tom', 'Anderson', 'Netherlands', 'referral', 'active', ARRAY['dutch_style', 'advanced']),
('maria.garcia@email.com', 'Maria', 'Garcia', 'Spain', 'instagram', 'active', ARRAY['nature_style', 'plants'])
ON CONFLICT (email) DO NOTHING;

-- Create subscription preferences for sample subscribers
INSERT INTO subscription_preferences (subscriber_id, newsletter_frequency, content_types, marketing_consent, analytics_consent)
SELECT 
    s.id,
    CASE 
        WHEN 'advanced' = ANY(s.tags) THEN 'weekly'
        WHEN 'beginner' = ANY(s.tags) THEN 'bi_weekly'
        ELSE 'weekly'
    END,
    CASE 
        WHEN 'plants' = ANY(s.tags) THEN ARRAY['plant_care', 'species_profiles']
        WHEN 'equipment' = ANY(s.tags) THEN ARRAY['equipment_reviews', 'diy_projects']
        WHEN 'beginner' = ANY(s.tags) THEN ARRAY['basics', 'how_to_guides']
        ELSE ARRAY['all']
    END,
    true,
    true
FROM subscribers s
WHERE NOT EXISTS (
    SELECT 1 FROM subscription_preferences sp WHERE sp.subscriber_id = s.id
);

-- ===================
-- SAMPLE NEWSLETTER CAMPAIGNS
-- ===================

-- Sample newsletter issues
INSERT INTO newsletter_issues (
    issue_number, template_type, subject_line, preview_text, 
    content_ids, status, recipient_count, sent_at
) VALUES
(
    1,
    'digest',
    'Your Weekly Aquascaping Digest #1',
    'This week: beginner plant selection, CO2 systems explained, and stunning Iwagumi inspiration',
    (SELECT ARRAY_AGG(id) FROM generated_content WHERE content_type IN ('newsletter_article', 'instagram_caption') LIMIT 3),
    'sent',
    250,
    NOW() - INTERVAL '3 days'
),
(
    2,
    'educational',
    'Master Low-Maintenance Planted Tanks',
    'Discover 5 aquatic plants that thrive with minimal care - perfect for busy aquascapers',
    (SELECT ARRAY_AGG(id) FROM generated_content WHERE title LIKE '%Low-Maintenance%' LIMIT 1),
    'sent',
    267,
    NOW() - INTERVAL '1 week'
);

-- Sample newsletter metrics
INSERT INTO newsletter_metrics (
    issue_id, sent_count, delivered_count, open_count, click_count, 
    unique_opens, unique_clicks, open_rate, click_rate, unsubscribe_count
) VALUES
(
    (SELECT id FROM newsletter_issues WHERE issue_number = 1),
    250, 248, 89, 23, 87, 21, 0.3589, 0.0927, 2
),
(
    (SELECT id FROM newsletter_issues WHERE issue_number = 2),
    267, 265, 112, 34, 108, 31, 0.4075, 0.1283, 1
);

-- ===================
-- SAMPLE INSTAGRAM POSTS
-- ===================

-- Sample Instagram posts
INSERT INTO instagram_posts (
    content_id, post_type, caption, hashtags, status, posted_at,
    instagram_post_id, metrics
) VALUES
(
    (SELECT id FROM generated_content WHERE content_type = 'instagram_caption' LIMIT 1),
    'feed',
    'The beauty of simplicity in this Iwagumi layout ✨ This minimalist aquascape demonstrates the power of negative space...',
    ARRAY['aquascape', 'iwagumi', 'plantedtank', 'aquascaping', 'natureaquarium', 'minimalism'],
    'posted',
    NOW() - INTERVAL '2 days',
    'IG_POST_12345',
    '{"likes": 342, "comments": 28, "shares": 15, "saves": 67, "reach": 1250, "impressions": 2100}'
);

-- ===================
-- SAMPLE CONTENT METRICS
-- ===================

-- Sample content performance metrics
INSERT INTO content_metrics (content_id, metric_type, metric_name, metric_value, metric_data) 
SELECT 
    gc.id,
    'engagement',
    'page_views',
    FLOOR(RANDOM() * 1000 + 100)::INT,
    '{"source": "organic_search", "bounce_rate": 0.35}'
FROM generated_content gc 
WHERE gc.status = 'published';

INSERT INTO content_metrics (content_id, metric_type, metric_name, metric_value, metric_data)
SELECT 
    gc.id,
    'social',
    'social_shares',
    FLOOR(RANDOM() * 50 + 5)::INT,
    '{"platforms": {"facebook": 12, "twitter": 8, "pinterest": 15}}'
FROM generated_content gc 
WHERE gc.status = 'published';

-- ===================
-- SAMPLE SCRAPING DATA
-- ===================

-- Update scraper targets with recent activity
UPDATE scraper_targets 
SET 
    last_scraped_at = NOW() - INTERVAL '1 hour',
    next_scrape_at = NOW() + INTERVAL '1 day',
    success_count = FLOOR(RANDOM() * 50 + 10)::INT,
    error_count = FLOOR(RANDOM() * 3)::INT;

-- Sample scraping jobs
INSERT INTO scraping_jobs (target_id, status, started_at, completed_at, pages_scraped, content_found)
SELECT 
    st.id,
    'completed',
    NOW() - INTERVAL '2 hours',
    NOW() - INTERVAL '1 hour',
    FLOOR(RANDOM() * 20 + 5)::INT,
    FLOOR(RANDOM() * 10 + 2)::INT
FROM scraper_targets st;

-- ===================
-- SAMPLE SYSTEM EVENTS
-- ===================

-- Sample system events
INSERT INTO system_events (event_type, event_name, event_data, severity, service_name, occurred_at) VALUES
('scraping', 'scraping_job_completed', '{"target": "Green Aqua", "pages_scraped": 15, "content_found": 8}', 'info', 'web-scraper', NOW() - INTERVAL '1 hour'),
('content', 'content_published', '{"content_id": "uuid", "type": "newsletter_article", "title": "Setting Up Your First Planted Aquarium"}', 'info', 'content-manager', NOW() - INTERVAL '3 hours'),
('newsletter', 'campaign_sent', '{"issue_id": "uuid", "recipients": 250, "template": "digest"}', 'info', 'distributor', NOW() - INTERVAL '6 hours'),
('system', 'backup_completed', '{"backup_size_mb": 125, "duration_seconds": 45, "status": "success"}', 'info', 'backup-service', NOW() - INTERVAL '12 hours'),
('ai', 'content_generation_batch', '{"generated_count": 5, "average_quality": 0.87, "processing_time": 120}', 'info', 'ai-processor', NOW() - INTERVAL '30 minutes');

-- ===================
-- SAMPLE SYSTEM METRICS
-- ===================

-- Sample system performance metrics
INSERT INTO system_metrics (service_name, metric_name, metric_value, metric_unit, tags, recorded_at) VALUES
('content-manager', 'response_time_ms', 145.7, 'milliseconds', '{"endpoint": "/api/content", "method": "GET"}', NOW() - INTERVAL '5 minutes'),
('ai-processor', 'content_generation_time', 45.2, 'seconds', '{"model": "gpt-4", "type": "newsletter_article"}', NOW() - INTERVAL '10 minutes'),
('postgres', 'active_connections', 12, 'connections', '{"database": "content_engine"}', NOW() - INTERVAL '1 minute'),
('redis', 'memory_usage_mb', 256, 'megabytes', '{"instance": "primary"}', NOW() - INTERVAL '2 minutes'),
('web-scraper', 'pages_per_minute', 2.3, 'pages', '{"target": "greenaqua.hu"}', NOW() - INTERVAL '15 minutes');

-- ===================
-- UPDATE STATISTICS
-- ===================

-- Update table statistics for better query planning
ANALYZE raw_content;
ANALYZE generated_content;
ANALYZE subscribers;
ANALYZE newsletter_issues;
ANALYZE content_metrics;
ANALYZE system_metrics;

-- ===================
-- SUCCESS MESSAGE
-- ===================

RAISE NOTICE 'Test data creation completed successfully!';
RAISE NOTICE 'Created:';
RAISE NOTICE '- % raw content records', (SELECT COUNT(*) FROM raw_content);
RAISE NOTICE '- % generated content records', (SELECT COUNT(*) FROM generated_content WHERE content_type IN ('newsletter_article', 'instagram_caption'));
RAISE NOTICE '- % subscribers', (SELECT COUNT(*) FROM subscribers);
RAISE NOTICE '- % newsletter issues', (SELECT COUNT(*) FROM newsletter_issues);
RAISE NOTICE '- % content metrics records', (SELECT COUNT(*) FROM content_metrics);
RAISE NOTICE '- % system events', (SELECT COUNT(*) FROM system_events);
RAISE NOTICE '';
RAISE NOTICE 'Sample admin user credentials:';
RAISE NOTICE 'Username: admin';
RAISE NOTICE 'Email: admin@aquascene.com';
RAISE NOTICE 'Password: admin123 (CHANGE THIS IN PRODUCTION!)';
RAISE NOTICE '';
RAISE NOTICE 'Development environment is ready for testing!';