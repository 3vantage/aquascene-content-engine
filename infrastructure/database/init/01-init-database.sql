-- AquaScene Content Engine - Database Initialization Script
-- This script creates the complete database schema for all environments
-- Version: 1.0

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Set timezone
SET timezone = 'UTC';

-- ===================
-- CORE CONTENT TABLES
-- ===================

-- Raw scraped content storage
CREATE TABLE IF NOT EXISTS raw_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT NOT NULL,
    source_domain VARCHAR(255) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    title TEXT,
    content TEXT,
    html_content TEXT,
    images JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    scraped_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(20) DEFAULT 'pending',
    processing_error TEXT,
    content_hash VARCHAR(64),
    language VARCHAR(10) DEFAULT 'en',
    word_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(content_hash)
);

-- Generated content from AI processing
CREATE TABLE IF NOT EXISTS generated_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    excerpt TEXT,
    template_used VARCHAR(100),
    source_materials JSONB DEFAULT '[]',
    quality_score DECIMAL(3,2),
    readability_score INTEGER,
    seo_score DECIMAL(3,2),
    engagement_prediction DECIMAL(3,2),
    status VARCHAR(20) DEFAULT 'draft',
    tags TEXT[],
    categories TEXT[],
    target_audience VARCHAR(50),
    tone VARCHAR(30),
    word_count INTEGER,
    estimated_reading_time INTEGER,
    scheduled_for TIMESTAMP,
    published_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID,
    approved_by UUID,
    approved_at TIMESTAMP
);

-- Content categories and taxonomy
CREATE TABLE IF NOT EXISTS content_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id INTEGER REFERENCES content_categories(id),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Content tags for flexible categorization
CREATE TABLE IF NOT EXISTS content_tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Content assets (images, videos, documents)
CREATE TABLE IF NOT EXISTS content_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_path TEXT NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    file_type VARCHAR(20),
    width INTEGER,
    height INTEGER,
    alt_text TEXT,
    caption TEXT,
    metadata JSONB DEFAULT '{}',
    uploaded_at TIMESTAMP DEFAULT NOW(),
    uploaded_by UUID,
    is_active BOOLEAN DEFAULT TRUE
);

-- Link content to assets
CREATE TABLE IF NOT EXISTS content_asset_relations (
    content_id UUID REFERENCES generated_content(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES content_assets(id) ON DELETE CASCADE,
    relation_type VARCHAR(30) DEFAULT 'attachment',
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (content_id, asset_id)
);

-- ===================
-- NEWSLETTER SYSTEM
-- ===================

-- Newsletter issues/campaigns
CREATE TABLE IF NOT EXISTS newsletter_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_number INTEGER,
    template_type VARCHAR(50) NOT NULL,
    subject_line TEXT NOT NULL,
    preview_text TEXT,
    content_ids UUID[] NOT NULL,
    personalization_data JSONB DEFAULT '{}',
    design_template VARCHAR(100),
    scheduled_for TIMESTAMP,
    sent_at TIMESTAMP NULL,
    status VARCHAR(20) DEFAULT 'draft',
    recipient_count INTEGER DEFAULT 0,
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID
);

-- Newsletter templates
CREATE TABLE IF NOT EXISTS newsletter_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    template_type VARCHAR(50) NOT NULL,
    html_template TEXT NOT NULL,
    text_template TEXT,
    default_subject VARCHAR(255),
    variables JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ===================
-- SUBSCRIBER MANAGEMENT
-- ===================

-- Subscriber information
CREATE TABLE IF NOT EXISTS subscribers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(200),
    phone VARCHAR(50),
    country VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    source VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    subscription_date TIMESTAMP DEFAULT NOW(),
    confirmed_at TIMESTAMP,
    unsubscribed_at TIMESTAMP,
    bounce_count INTEGER DEFAULT 0,
    complaint_count INTEGER DEFAULT 0,
    last_activity_at TIMESTAMP DEFAULT NOW(),
    preferences JSONB DEFAULT '{}',
    custom_fields JSONB DEFAULT '{}',
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Subscriber segments for targeted campaigns
CREATE TABLE IF NOT EXISTS subscriber_segments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    segment_type VARCHAR(30) DEFAULT 'manual',
    filter_criteria JSONB DEFAULT '{}',
    subscriber_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Link subscribers to segments
CREATE TABLE IF NOT EXISTS subscriber_segment_memberships (
    subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
    segment_id INTEGER REFERENCES subscriber_segments(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT NOW(),
    added_by UUID,
    
    PRIMARY KEY (subscriber_id, segment_id)
);

-- Subscription preferences and consent
CREATE TABLE IF NOT EXISTS subscription_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE UNIQUE,
    newsletter_frequency VARCHAR(20) DEFAULT 'weekly',
    content_types TEXT[] DEFAULT ARRAY['all'],
    preferred_send_time TIME DEFAULT '09:00:00',
    preferred_send_days INTEGER[] DEFAULT ARRAY[1,2,3,4,5],
    email_format VARCHAR(10) DEFAULT 'html',
    double_opt_in BOOLEAN DEFAULT TRUE,
    marketing_consent BOOLEAN DEFAULT FALSE,
    analytics_consent BOOLEAN DEFAULT FALSE,
    third_party_sharing BOOLEAN DEFAULT FALSE,
    gdpr_consent BOOLEAN DEFAULT FALSE,
    gdpr_consent_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ===================
-- SOCIAL MEDIA INTEGRATION
-- ===================

-- Instagram posts and scheduling
CREATE TABLE IF NOT EXISTS instagram_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES generated_content(id),
    post_type VARCHAR(20) DEFAULT 'feed',
    caption TEXT,
    hashtags TEXT[],
    media_urls TEXT[],
    instagram_media_ids TEXT[],
    scheduled_for TIMESTAMP,
    posted_at TIMESTAMP,
    instagram_post_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'scheduled',
    metrics JSONB DEFAULT '{}',
    engagement_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Social media accounts configuration
CREATE TABLE IF NOT EXISTS social_accounts (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(30) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    account_id VARCHAR(100),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(platform, account_id)
);

-- ===================
-- WEB SCRAPING SYSTEM
-- ===================

-- Scraping targets configuration
CREATE TABLE IF NOT EXISTS scraper_targets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    domains TEXT[] NOT NULL,
    categories TEXT[],
    scraping_rules JSONB NOT NULL,
    rate_limit_delay INTEGER DEFAULT 2,
    max_pages INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    last_scraped_at TIMESTAMP,
    next_scrape_at TIMESTAMP,
    scrape_frequency INTERVAL DEFAULT '1 day',
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Scraping jobs and status
CREATE TABLE IF NOT EXISTS scraping_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_id INTEGER REFERENCES scraper_targets(id),
    job_type VARCHAR(30) DEFAULT 'scheduled',
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    pages_scraped INTEGER DEFAULT 0,
    content_found INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    error_details JSONB DEFAULT '[]',
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ===================
-- ANALYTICS AND METRICS
-- ===================

-- Content performance metrics
CREATE TABLE IF NOT EXISTS content_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES generated_content(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4),
    metric_data JSONB DEFAULT '{}',
    recorded_at TIMESTAMP DEFAULT NOW(),
    date_bucket DATE DEFAULT CURRENT_DATE,
    
    UNIQUE(content_id, metric_type, metric_name, date_bucket)
);

-- Newsletter campaign metrics
CREATE TABLE IF NOT EXISTS newsletter_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID REFERENCES newsletter_issues(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL,
    sent_count INTEGER DEFAULT 0,
    delivered_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    unsubscribe_count INTEGER DEFAULT 0,
    bounce_count INTEGER DEFAULT 0,
    complaint_count INTEGER DEFAULT 0,
    unique_opens INTEGER DEFAULT 0,
    unique_clicks INTEGER DEFAULT 0,
    open_rate DECIMAL(5,4),
    click_rate DECIMAL(5,4),
    unsubscribe_rate DECIMAL(5,4),
    bounce_rate DECIMAL(5,4),
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- System analytics for monitoring
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4),
    metric_unit VARCHAR(20),
    tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMP DEFAULT NOW(),
    date_bucket TIMESTAMP DEFAULT DATE_TRUNC('minute', NOW())
);

-- ===================
-- USER MANAGEMENT
-- ===================

-- Admin users for the system
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(30) DEFAULT 'editor',
    permissions JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    password_changed_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Admin user sessions
CREATE TABLE IF NOT EXISTS admin_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES admin_users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ===================
-- AUDIT AND LOGGING
-- ===================

-- Audit log for tracking changes
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(100) NOT NULL,
    action VARCHAR(20) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    changed_by UUID,
    changed_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- System event log
CREATE TABLE IF NOT EXISTS system_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    severity VARCHAR(20) DEFAULT 'info',
    service_name VARCHAR(50),
    occurred_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ===================
-- INDEXES FOR PERFORMANCE
-- ===================

-- Raw content indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_raw_content_source_domain ON raw_content(source_domain);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_raw_content_processed ON raw_content(processed, scraped_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_raw_content_content_type ON raw_content(content_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_raw_content_hash ON raw_content(content_hash);

-- Generated content indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_generated_content_status ON generated_content(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_generated_content_type ON generated_content(content_type, status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_generated_content_published ON generated_content(published_at DESC) WHERE published_at IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_generated_content_scheduled ON generated_content(scheduled_for) WHERE scheduled_for IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_generated_content_tags ON generated_content USING GIN(tags);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_generated_content_categories ON generated_content USING GIN(categories);

-- Full text search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_generated_content_search ON generated_content USING gin(to_tsvector('english', title || ' ' || content));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_raw_content_search ON raw_content USING gin(to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(content, '')));

-- Subscriber indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscribers_email ON subscribers(email);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscribers_status ON subscribers(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscribers_source ON subscribers(source);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscribers_tags ON subscribers USING GIN(tags);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_subscribers_subscription_date ON subscribers(subscription_date DESC);

-- Newsletter indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_newsletter_issues_status ON newsletter_issues(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_newsletter_issues_scheduled ON newsletter_issues(scheduled_for) WHERE scheduled_for IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_newsletter_issues_sent ON newsletter_issues(sent_at DESC) WHERE sent_at IS NOT NULL;

-- Instagram posts indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_instagram_posts_status ON instagram_posts(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_instagram_posts_scheduled ON instagram_posts(scheduled_for) WHERE scheduled_for IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_instagram_posts_posted ON instagram_posts(posted_at DESC) WHERE posted_at IS NOT NULL;

-- Scraping indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraper_targets_active ON scraper_targets(is_active);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraper_targets_next_scrape ON scraper_targets(next_scrape_at) WHERE is_active = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraping_jobs_status ON scraping_jobs(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scraping_jobs_target ON scraping_jobs(target_id, created_at DESC);

-- Metrics indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_metrics_content_date ON content_metrics(content_id, date_bucket);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_metrics_type ON content_metrics(metric_type, date_bucket);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_newsletter_metrics_issue ON newsletter_metrics(issue_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_metrics_service_date ON system_metrics(service_name, date_bucket);

-- Audit log indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_log_changed_by ON audit_log(changed_by);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_log_changed_at ON audit_log(changed_at DESC);

-- System events indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_events_type ON system_events(event_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_events_occurred ON system_events(occurred_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_events_severity ON system_events(severity, occurred_at DESC);

-- ===================
-- TRIGGERS FOR AUTOMATION
-- ===================

-- Function to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_raw_content_updated_at BEFORE UPDATE ON raw_content FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_generated_content_updated_at BEFORE UPDATE ON generated_content FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_content_categories_updated_at BEFORE UPDATE ON content_categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_content_tags_updated_at BEFORE UPDATE ON content_tags FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_newsletter_issues_updated_at BEFORE UPDATE ON newsletter_issues FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_newsletter_templates_updated_at BEFORE UPDATE ON newsletter_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscribers_updated_at BEFORE UPDATE ON subscribers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscriber_segments_updated_at BEFORE UPDATE ON subscriber_segments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subscription_preferences_updated_at BEFORE UPDATE ON subscription_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_instagram_posts_updated_at BEFORE UPDATE ON instagram_posts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_social_accounts_updated_at BEFORE UPDATE ON social_accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_scraper_targets_updated_at BEFORE UPDATE ON scraper_targets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_scraping_jobs_updated_at BEFORE UPDATE ON scraping_jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_admin_users_updated_at BEFORE UPDATE ON admin_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update segment subscriber counts
CREATE OR REPLACE FUNCTION update_segment_subscriber_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE subscriber_segments 
        SET subscriber_count = subscriber_count + 1 
        WHERE id = NEW.segment_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE subscriber_segments 
        SET subscriber_count = subscriber_count - 1 
        WHERE id = OLD.segment_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply segment count trigger
CREATE TRIGGER update_segment_count_on_membership_change
    AFTER INSERT OR DELETE ON subscriber_segment_memberships
    FOR EACH ROW EXECUTE FUNCTION update_segment_subscriber_count();

-- Function to update tag usage counts
CREATE OR REPLACE FUNCTION update_tag_usage_count()
RETURNS TRIGGER AS $$
BEGIN
    -- This is a simplified version - in production you'd want more sophisticated logic
    UPDATE content_tags SET usage_count = (
        SELECT COUNT(*) FROM generated_content 
        WHERE content_tags.name = ANY(generated_content.tags)
    );
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply tag usage trigger
CREATE TRIGGER update_tag_usage_on_content_change
    AFTER INSERT OR UPDATE OF tags ON generated_content
    FOR EACH STATEMENT EXECUTE FUNCTION update_tag_usage_count();

-- ===================
-- INITIAL DATA SETUP
-- ===================

-- Insert default content categories
INSERT INTO content_categories (name, slug, description) VALUES
('Aquascaping Basics', 'aquascaping-basics', 'Fundamental concepts and beginner guides'),
('Plant Care', 'plant-care', 'Aquatic plant cultivation and maintenance'),
('Equipment Reviews', 'equipment-reviews', 'Reviews and comparisons of aquascaping equipment'),
('Tank Showcases', 'tank-showcases', 'Beautiful aquascape galleries and inspiration'),
('Maintenance Tips', 'maintenance-tips', 'Tank maintenance and troubleshooting guides'),
('Species Profiles', 'species-profiles', 'Fish and plant species information'),
('DIY Projects', 'diy-projects', 'Do-it-yourself aquascaping projects'),
('News & Trends', 'news-trends', 'Latest aquascaping news and industry trends')
ON CONFLICT (name) DO NOTHING;

-- Insert default newsletter templates
INSERT INTO newsletter_templates (name, description, template_type, html_template, text_template, default_subject) VALUES
('Weekly Digest', 'Weekly roundup of aquascaping content', 'digest', '<html><!-- Weekly digest template --></html>', 'Weekly Digest Text Version', 'Your Weekly AquaScape Digest'),
('Product Announcement', 'New product or service announcements', 'announcement', '<html><!-- Announcement template --></html>', 'Announcement Text Version', 'Exciting News from AquaScene!'),
('How-To Guide', 'Step-by-step educational content', 'educational', '<html><!-- How-to template --></html>', 'How-to Guide Text Version', 'Master This Aquascaping Technique'),
('Community Showcase', 'Featuring community aquascapes', 'showcase', '<html><!-- Showcase template --></html>', 'Community Showcase Text Version', 'Amazing Aquascapes from Our Community')
ON CONFLICT (name) DO NOTHING;

-- Insert default subscriber segments
INSERT INTO subscriber_segments (name, description, segment_type) VALUES
('New Subscribers', 'Subscribers who joined in the last 30 days', 'automatic'),
('Engaged Users', 'High engagement subscribers', 'automatic'),
('Plant Enthusiasts', 'Subscribers interested in plant content', 'manual'),
('Equipment Buyers', 'Subscribers who click on equipment links', 'behavioral'),
('Beginners', 'New to aquascaping', 'manual'),
('Advanced Aquascapers', 'Experienced hobbyists', 'manual')
ON CONFLICT (name) DO NOTHING;

-- Insert default scraper targets
INSERT INTO scraper_targets (name, base_url, domains, categories, scraping_rules) VALUES
('Green Aqua', 'https://www.greenaqua.hu', ARRAY['greenaqua.hu'], ARRAY['plants', 'equipment', 'guides'], '{"selectors": {"title": "h1", "content": ".content"}, "rate_limit": 3}'),
('Aqua Design Amano', 'https://www.adana.co.jp', ARRAY['adana.co.jp'], ARRAY['layouts', 'products'], '{"selectors": {"title": "h1", "content": ".article-content"}, "rate_limit": 5}'),
('Tropica Aquarium Plants', 'https://tropica.com', ARRAY['tropica.com'], ARRAY['plants', 'guides'], '{"selectors": {"title": "h1", "content": ".main-content"}, "rate_limit": 2}')
ON CONFLICT (name) DO NOTHING;

-- Create default admin user (password should be changed after first login)
-- Default password: 'admin123' (hashed with bcrypt)
INSERT INTO admin_users (username, email, password_hash, first_name, last_name, role, is_superuser) VALUES
('admin', 'admin@aquascene.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewKHbpyW7uLhLgZa', 'Admin', 'User', 'admin', true)
ON CONFLICT (username) DO NOTHING;

-- ===================
-- VIEWS FOR COMMON QUERIES
-- ===================

-- View for published content with metrics
CREATE OR REPLACE VIEW published_content_with_metrics AS
SELECT 
    gc.*,
    cm_views.view_count,
    cm_shares.share_count,
    cm_clicks.click_count
FROM generated_content gc
LEFT JOIN (
    SELECT content_id, SUM(metric_value) as view_count 
    FROM content_metrics 
    WHERE metric_name = 'page_views' 
    GROUP BY content_id
) cm_views ON gc.id = cm_views.content_id
LEFT JOIN (
    SELECT content_id, SUM(metric_value) as share_count 
    FROM content_metrics 
    WHERE metric_name = 'social_shares' 
    GROUP BY content_id
) cm_shares ON gc.id = cm_shares.content_id
LEFT JOIN (
    SELECT content_id, SUM(metric_value) as click_count 
    FROM content_metrics 
    WHERE metric_name = 'link_clicks' 
    GROUP BY content_id
) cm_clicks ON gc.id = cm_clicks.content_id
WHERE gc.status = 'published';

-- View for active subscribers with preferences
CREATE OR REPLACE VIEW active_subscribers_with_preferences AS
SELECT 
    s.*,
    sp.newsletter_frequency,
    sp.content_types,
    sp.preferred_send_time,
    sp.email_format
FROM subscribers s
LEFT JOIN subscription_preferences sp ON s.id = sp.subscriber_id
WHERE s.status = 'active';

-- View for newsletter performance summary
CREATE OR REPLACE VIEW newsletter_performance_summary AS
SELECT 
    ni.*,
    nm.sent_count,
    nm.open_count,
    nm.click_count,
    nm.open_rate,
    nm.click_rate,
    nm.unsubscribe_count
FROM newsletter_issues ni
LEFT JOIN newsletter_metrics nm ON ni.id = nm.issue_id
WHERE ni.status = 'sent';

-- ===================
-- FUNCTIONS FOR COMMON OPERATIONS
-- ===================

-- Function to get content recommendations based on user engagement
CREATE OR REPLACE FUNCTION get_content_recommendations(subscriber_email VARCHAR, content_limit INTEGER DEFAULT 10)
RETURNS TABLE (
    content_id UUID,
    title TEXT,
    content_type VARCHAR(50),
    quality_score DECIMAL(3,2),
    published_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        gc.id,
        gc.title,
        gc.content_type,
        gc.quality_score,
        gc.published_at
    FROM generated_content gc
    WHERE gc.status = 'published'
    AND gc.quality_score >= 0.7
    ORDER BY gc.published_at DESC, gc.quality_score DESC
    LIMIT content_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate content engagement score
CREATE OR REPLACE FUNCTION calculate_content_engagement_score(content_id_param UUID)
RETURNS DECIMAL(5,4) AS $$
DECLARE
    engagement_score DECIMAL(5,4) := 0;
    view_count INTEGER := 0;
    share_count INTEGER := 0;
    click_count INTEGER := 0;
BEGIN
    -- Get metrics
    SELECT COALESCE(SUM(CASE WHEN metric_name = 'page_views' THEN metric_value ELSE 0 END), 0),
           COALESCE(SUM(CASE WHEN metric_name = 'social_shares' THEN metric_value ELSE 0 END), 0),
           COALESCE(SUM(CASE WHEN metric_name = 'link_clicks' THEN metric_value ELSE 0 END), 0)
    INTO view_count, share_count, click_count
    FROM content_metrics
    WHERE content_id = content_id_param;
    
    -- Calculate engagement score (weighted formula)
    engagement_score := (view_count * 0.1 + share_count * 2.0 + click_count * 1.5) / 100.0;
    
    -- Cap at 1.0
    IF engagement_score > 1.0 THEN
        engagement_score := 1.0;
    END IF;
    
    RETURN engagement_score;
END;
$$ LANGUAGE plpgsql;

COMMIT;