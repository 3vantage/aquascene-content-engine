# User Troubleshooting Guide - AquaScene Content Engine

**Version:** 1.0  
**Last Updated:** August 6, 2025  
**Target Audience:** All Users (Organized by User Type)

## Overview

This comprehensive troubleshooting guide addresses the most common issues users encounter with the AquaScene Content Engine. Solutions are organized by user type and problem category, with step-by-step resolution instructions.

## Quick Issue Identification

### 🚨 Critical Issues (Immediate Action Required)
- System completely inaccessible
- All content generation failing
- Data loss or corruption
- Security breaches

### ⚠️ High Priority Issues (Same Day Resolution)
- Single service offline
- Content quality severely degraded
- API integration failures
- Performance significantly degraded

### 📋 Medium Priority Issues (1-3 Days Resolution)
- Minor UI glitches
- Occasional generation failures
- Slow response times
- Non-critical feature issues

### 💡 Low Priority Issues (Next Update/Release)
- Enhancement requests
- Minor cosmetic issues
- Documentation updates
- Feature requests

## Content Creator Troubleshooting

### Issue 1: Content Generation Failures

#### Symptom: "Generation Failed" Error Message
**Error Messages You Might See:**
- "Failed to generate content. Please try again."
- "AI service unavailable. Please wait and retry."
- "Content generation timeout. Please check your request."
- "Invalid parameters provided. Please review your input."

**Immediate Solutions:**
1. **Check System Status First**
   ```
   Step 1: Go to Dashboard → Review service status cards
   Step 2: Look for red "Offline" indicators
   Step 3: If AI Processor shows offline, wait 5 minutes and try again
   ```

2. **Verify Your Input Parameters**
   ```
   ✅ Check Required Fields:
   - Topic field not empty
   - Content type selected
   - Target audience specified
   
   ✅ Validate Input Quality:
   - Topic is specific and clear
   - No special characters in unexpected places
   - Reasonable word count requested (100-3000)
   ```

3. **Try Different AI Provider** (Power Users)
   ```
   If using OpenAI: Switch to Claude or Ollama
   If using Claude: Switch to OpenAI or Ollama
   If using Ollama: Switch to OpenAI or Claude
   ```

4. **Simplify Your Request**
   ```
   Reduce complexity:
   - Shorter, simpler topic
   - Lower word count (500-800 words)
   - Basic content type (Newsletter Article)
   - Beginner audience level
   ```

**Advanced Solutions:**
1. **Check API Key Validity**
   ```
   Go to Settings → API Keys
   - Verify keys haven't expired
   - Test with simple generation request
   - Contact administrator if keys need updating
   ```

2. **Review Rate Limits**
   ```
   If you see "Rate limit exceeded":
   - Wait 60 seconds before retrying
   - Reduce concurrent batch operations
   - Switch to different AI provider temporarily
   ```

#### Symptom: Poor Quality Content Generated
**What You Might Notice:**
- Content doesn't match your brand voice
- Factual errors in aquascaping information
- Generic or irrelevant content
- Inconsistent tone or style

**Solutions:**
1. **Improve Input Specificity**
   ```
   Instead of: "Aquarium plants"
   Try: "Low-light aquatic plants for beginners with CO2-free setups"
   
   Instead of: "Fish care"
   Try: "Weekly maintenance routine for 20-gallon planted community tanks"
   ```

2. **Adjust Brand Voice Settings**
   ```
   Go to AI Processor → Content Parameters
   - Set specific brand voice (Educational, Friendly, Professional)
   - Add brand-specific keywords or phrases
   - Include style guidelines in topic description
   ```

3. **Use Better Keywords**
   ```
   Quality SEO Keywords:
   ✅ "beginner aquascaping", "planted tank setup"
   ✅ "aquarium plant care", "CO2 injection basics"
   ❌ "water", "fish", "tank" (too generic)
   ```

4. **Regenerate with Different Provider**
   ```
   For Creative Content: Try Anthropic Claude
   For Technical Accuracy: Try OpenAI GPT-4
   For Cost-Effective Volume: Try Ollama (if available)
   ```

### Issue 2: Slow Content Generation

#### Symptom: Generation Takes Longer Than Expected
**Normal Generation Times:**
- Newsletter Article: 60-90 seconds
- Instagram Caption: 20-30 seconds
- How-To Guide: 90-120 seconds
- Product Review: 120-150 seconds

**Solutions:**
1. **Check System Load**
   ```
   Dashboard → Service Status
   - Look for high CPU/memory usage indicators
   - Check if multiple users are generating content
   - Consider generating during off-peak hours
   ```

2. **Optimize Your Request**
   ```
   Reduce Generation Time:
   - Lower word count requirements
   - Simpler content types
   - Less complex topics
   - Fewer SEO keywords
   ```

3. **Try Different AI Provider**
   ```
   Speed Ranking (fastest to slowest):
   1. Ollama (local) - if available
   2. OpenAI GPT-3.5
   3. Anthropic Claude
   4. OpenAI GPT-4
   ```

### Issue 3: Batch Generation Problems

#### Symptom: Some Jobs in Batch Fail
**What You See:**
- Batch shows "3/5 completed"
- Some content pieces missing
- Error messages for specific requests

**Solutions:**
1. **Review Failed Jobs**
   ```
   Step 1: Go to batch results page
   Step 2: Identify which specific jobs failed
   Step 3: Check error messages for each failed job
   Step 4: Note any patterns in failures
   ```

2. **Retry Failed Jobs Individually**
   ```
   Step 1: Copy parameters from failed job
   Step 2: Try single generation with same parameters
   Step 3: Adjust parameters if single generation fails
   Step 4: Add successful job back to batch
   ```

3. **Reduce Batch Size**
   ```
   Instead of: 10 jobs concurrent
   Try: 3-5 jobs concurrent
   
   Instead of: All jobs at once
   Try: Multiple smaller batches
   ```

## System Administrator Troubleshooting

### Issue 1: Service Health Problems

#### Symptom: Services Showing Offline in Dashboard
**Immediate Diagnosis:**
1. **Check Docker Container Status**
   ```bash
   docker-compose ps
   
   Look for:
   - "Exit 1" or similar error codes
   - Services not listed
   - Restarting services
   ```

2. **Review Service Logs**
   ```bash
   # Check specific service logs
   docker-compose logs ai-processor
   docker-compose logs content-manager
   docker-compose logs web-scraper
   docker-compose logs distributor
   docker-compose logs subscriber-manager
   
   # Follow logs in real-time
   docker-compose logs -f [service-name]
   ```

**Common Solutions:**

1. **Port Conflicts**
   ```bash
   # Check if ports are in use
   netstat -tulpn | grep :8001
   netstat -tulpn | grep :8000
   
   # Solution: Stop conflicting services or change ports
   # Edit docker-compose.yml to use different ports
   ```

2. **Environment Configuration Issues**
   ```bash
   # Check .env file exists and has required variables
   ls -la services/ai-processor/.env
   
   # Verify API keys are set
   grep "OPENAI_API_KEY" services/ai-processor/.env
   grep "ANTHROPIC_API_KEY" services/ai-processor/.env
   ```

3. **Resource Exhaustion**
   ```bash
   # Check system resources
   docker stats
   
   # Check disk space
   df -h
   
   # Check memory usage
   free -m
   ```

4. **Dependency Issues**
   ```bash
   # Restart services in dependency order
   docker-compose stop
   docker-compose up -d postgres redis minio
   sleep 30
   docker-compose up -d
   ```

#### Symptom: Intermittent Service Failures
**Diagnosis Steps:**
1. **Monitor Resource Usage**
   ```bash
   # Set up continuous monitoring
   watch -n 5 'docker stats --no-stream'
   
   # Check for memory leaks
   docker exec ai-processor ps aux --sort=-%mem | head
   ```

2. **Review Error Patterns**
   ```bash
   # Check for patterns in logs
   docker-compose logs ai-processor | grep -i error | tail -20
   
   # Check for OOM (Out of Memory) kills
   dmesg | grep -i "killed process"
   ```

**Solutions:**
1. **Increase Resource Limits**
   ```yaml
   # In docker-compose.yml
   services:
     ai-processor:
       deploy:
         resources:
           limits:
             memory: 4G
             cpus: '2.0'
           reservations:
             memory: 2G
             cpus: '1.0'
   ```

2. **Configure Health Checks**
   ```yaml
   # Add to service definition
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
     interval: 30s
     timeout: 10s
     retries: 3
     start_period: 60s
   ```

3. **Set Up Service Restart Policies**
   ```yaml
   services:
     ai-processor:
       restart: unless-stopped
   ```

### Issue 2: Database Connection Problems

#### Symptom: "Database connection failed" errors
**Diagnosis:**
1. **Check PostgreSQL Status**
   ```bash
   docker-compose exec postgres pg_isready -U aquascene
   
   # Check database logs
   docker-compose logs postgres | tail -20
   ```

2. **Test Database Connectivity**
   ```bash
   # Connect to database
   docker-compose exec postgres psql -U aquascene -d content_engine
   
   # List tables
   \dt
   
   # Check connection count
   SELECT count(*) FROM pg_stat_activity;
   ```

**Solutions:**
1. **Reset Database Connection Pool**
   ```bash
   # Restart services that use database
   docker-compose restart content-manager subscriber-manager
   ```

2. **Check Database Configuration**
   ```bash
   # Verify environment variables
   docker-compose exec content-manager env | grep DATABASE
   
   # Check connection string format
   DATABASE_URL=postgresql://user:pass@postgres:5432/content_engine
   ```

3. **Database Recovery**
   ```bash
   # If database is corrupted
   docker-compose stop
   docker volume rm aquascene-content-engine_postgres_data
   docker-compose up -d postgres
   # Wait for initialization, then start other services
   docker-compose up -d
   ```

### Issue 3: Performance Degradation

#### Symptom: System Running Slowly
**Performance Analysis:**
1. **Resource Monitoring**
   ```bash
   # Check overall system performance
   htop
   iotop -o
   
   # Docker-specific monitoring
   docker stats --no-stream
   
   # Check for high I/O wait
   iostat -x 1
   ```

2. **Database Performance**
   ```bash
   # Check for slow queries
   docker-compose exec postgres psql -U aquascene -d content_engine \
     -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
   
   # Check for table bloat
   docker-compose exec postgres psql -U aquascene -d content_engine \
     -c "SELECT schemaname, tablename, n_dead_tup, n_live_tup FROM pg_stat_user_tables ORDER BY n_dead_tup DESC;"
   ```

**Optimization Solutions:**
1. **Database Optimization**
   ```bash
   # Run database maintenance
   docker-compose exec postgres psql -U aquascene -d content_engine \
     -c "VACUUM ANALYZE;"
   
   # Reindex if necessary
   docker-compose exec postgres psql -U aquascene -d content_engine \
     -c "REINDEX DATABASE content_engine;"
   ```

2. **Redis Cache Optimization**
   ```bash
   # Check Redis memory usage
   docker-compose exec redis redis-cli INFO memory
   
   # Clear cache if needed
   docker-compose exec redis redis-cli FLUSHALL
   ```

3. **Container Resource Adjustment**
   ```yaml
   # Increase resources for heavy services
   services:
     ai-processor:
       deploy:
         resources:
           limits:
             memory: 8G
             cpus: '4.0'
   ```

## Business User Troubleshooting

### Issue 1: Dashboard Not Showing Expected Data

#### Symptom: Metrics appear to be zero or outdated
**Quick Checks:**
1. **Verify Data Collection**
   ```
   Dashboard → Check "Last Updated" timestamp
   If older than 5 minutes:
   - Refresh the page
   - Check if services are online
   - Contact administrator if problem persists
   ```

2. **Check Service Integration**
   ```
   Go to each service section:
   - AI Processor: Try generating test content
   - Subscriber Manager: Check if subscriber data loads
   - Content Manager: Verify content library shows items
   ```

**Solutions:**
1. **Manual Data Refresh**
   ```
   Most dashboards auto-refresh every 30 seconds
   - Force refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
   - Check browser console for errors (F12)
   - Clear browser cache if needed
   ```

2. **Contact System Administrator**
   ```
   Provide this information:
   - Which metrics are missing/incorrect
   - When you first noticed the issue
   - Whether other users have the same problem
   - Screenshot of the dashboard
   ```

### Issue 2: Understanding ROI Calculations

#### Symptom: Cost savings numbers seem incorrect
**How to Verify ROI Calculations:**
1. **Manual Calculation Check**
   ```
   Previous Cost per Article: $200
   Current Cost per Article: $0.05
   Cost Reduction: (200 - 0.05) / 200 = 99.97%
   
   Monthly Savings (assuming 20 articles/month):
   Previous: 20 × $200 = $4,000
   Current: 20 × $0.05 = $1
   Monthly Savings: $3,999
   ```

2. **Volume Impact Calculation**
   ```
   Previous Volume: 5 articles/week = 20/month
   Current Volume: 50 articles/week = 200/month
   Volume Increase: 200/20 = 10x increase
   ```

**If Numbers Still Seem Wrong:**
1. **Check Calculation Assumptions**
   ```
   Verify these assumptions match your situation:
   - Previous manual cost: $200 per article
   - Current AI cost: ~$0.05 per article
   - Production time reduction: ~80%
   - Volume increase capability: ~10x
   ```

2. **Request Detailed Breakdown**
   ```
   Contact administrator for:
   - Detailed cost breakdown
   - Usage analytics report
   - Custom ROI calculation based on your specific costs
   ```

## Integration Troubleshooting

### Issue 1: Airtable Integration Problems

#### Symptom: "Connection failed" with Airtable
**Step-by-Step Diagnosis:**
1. **Verify Credentials**
   ```
   ✅ Check API Key Format:
   - Should start with "pat" (Personal Access Token)
   - Should be ~50+ characters long
   - No extra spaces or characters
   
   ✅ Check Base ID Format:
   - Should start with "app"
   - Should be exactly 17 characters
   - Get from URL: airtable.com/[BASE_ID]/[VIEW_ID]
   ```

2. **Test Outside System**
   ```bash
   # Test API key with curl
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        "https://api.airtable.com/v0/meta/bases"
   
   # Should return list of accessible bases
   ```

3. **Check Permissions**
   ```
   In Airtable Developer Hub:
   - Token should have data.records:read and data.records:write
   - Token should have schema.bases:read and schema.bases:write
   - Token should have access to your specific base
   ```

**Solutions:**
1. **Generate New API Key**
   ```
   Step 1: Go to airtable.com/create/tokens
   Step 2: Create new token with required scopes
   Step 3: Grant access to your specific base
   Step 4: Copy new token to AquaScene system
   ```

2. **Fix Base Access**
   ```
   If you're not the base owner:
   - Ask base owner to add you as collaborator
   - Ensure you have "Creator" or "Editor" permissions
   - Test access by creating a record manually in Airtable
   ```

#### Symptom: Analysis fails partway through
**Common Causes and Fixes:**

1. **Rate Limit Issues**
   ```
   Error: "Rate limit exceeded"
   Solution: Wait 60 seconds and retry
   
   Prevention: 
   - Reduce concurrent operations
   - Analyze smaller bases first
   - Schedule analysis during off-peak hours
   ```

2. **Large Base Issues**
   ```
   Error: "Timeout during analysis"
   Solutions:
   - Break analysis into smaller segments
   - Analyze specific tables only
   - Contact administrator to increase timeout limits
   ```

3. **Circular Reference Issues**
   ```
   Error: "Circular reference detected"
   Solution:
   - Check for self-referencing linked record fields
   - Remove circular relationships temporarily
   - Retry analysis
   ```

### Issue 2: Email Integration Problems

#### Symptom: Newsletters not sending
**Diagnosis Steps:**
1. **Check SendGrid Integration**
   ```
   Go to Distributor → Settings
   - Verify SendGrid API key is set
   - Check "From" email address is verified
   - Test with simple email send
   ```

2. **Review Email Content**
   ```
   Common issues:
   - Subject line too long (>50 characters)
   - Missing required content sections
   - Invalid HTML in email template
   - Subscriber list empty or invalid
   ```

**Solutions:**
1. **Fix SendGrid Configuration**
   ```
   Step 1: Log into SendGrid dashboard
   Step 2: Verify API key permissions include mail sending
   Step 3: Check domain authentication status
   Step 4: Verify sender identity
   ```

2. **Test Email Delivery**
   ```
   Step 1: Send test email to your own address
   Step 2: Check spam folder if not received
   Step 3: Verify email content renders correctly
   Step 4: Test with different email providers
   ```

## Emergency Procedures

### Complete System Recovery

#### When Everything is Down
**Priority Order:**
1. **Save Current Work**
   - Document what was being done when failure occurred
   - Note any error messages
   - Save any unsaved content

2. **Basic System Check**
   ```bash
   # Check if Docker is running
   docker --version
   docker-compose --version
   
   # Check if containers exist
   docker ps -a
   ```

3. **Emergency Restart**
   ```bash
   # Full system restart
   docker-compose down
   docker system prune -f
   docker-compose up -d
   
   # Wait 5 minutes for full startup
   sleep 300
   
   # Check status
   docker-compose ps
   ```

4. **Verify Critical Services**
   ```bash
   # Test each service
   curl http://localhost:8000/health  # Content Manager
   curl http://localhost:8001/health  # AI Processor
   curl http://localhost:5432         # Database (should refuse connection)
   ```

### Data Recovery

#### If Content is Lost
1. **Check Recent Backups**
   ```bash
   # Look for backup files
   ls -la infrastructure/backup/
   ls -la backup_data/
   ```

2. **Restore from Backup**
   ```bash
   # Stop services
   docker-compose down
   
   # Restore database
   docker-compose exec postgres pg_restore -U aquascene -d content_engine /backup/latest.sql
   
   # Restart services
   docker-compose up -d
   ```

3. **Contact Support**
   ```
   If data cannot be recovered:
   - Document what was lost
   - Provide timeline of when data was last seen
   - Include any error messages
   - Request professional data recovery assistance
   ```

## Prevention Best Practices

### For Content Creators
1. **Regular Backups**
   - Download important content immediately after generation
   - Keep local copies of critical content
   - Use batch operations for important content sets

2. **Input Validation**
   - Double-check topic spelling and grammar
   - Use specific, clear topics instead of vague ones
   - Test new content types with simple examples first

3. **Quality Monitoring**
   - Review content quality scores regularly
   - Report patterns in quality issues
   - Provide feedback on consistently poor results

### For System Administrators
1. **Regular Monitoring**
   - Set up automated health checks
   - Monitor resource usage trends
   - Plan for capacity upgrades before limits reached

2. **Backup Procedures**
   - Automated daily database backups
   - Configuration backup before changes
   - Test restoration procedures monthly

3. **Update Management**
   - Plan updates during low-usage periods
   - Test updates in staging environment
   - Have rollback procedures ready

4. **Documentation**
   - Keep configuration changes documented
   - Maintain current troubleshooting procedures
   - Document all custom modifications

### For Business Users
1. **Usage Tracking**
   - Monitor ROI calculations monthly
   - Track content performance trends
   - Plan for scaling based on growth patterns

2. **Stakeholder Communication**
   - Regular reports on system performance
   - Proactive communication about planned maintenance
   - Clear escalation procedures for critical issues

## When to Contact Support

### Immediate Support Required
- Complete system failure
- Data corruption or loss
- Security incidents
- Unable to generate any content for >4 hours

### Schedule Support
- Performance optimization requests
- Integration assistance
- Training for new users
- Custom feature requests

### Self-Service First
- Single content generation failures
- Minor UI issues
- Basic configuration questions
- Usage questions covered in documentation

---

## Summary

This troubleshooting guide provides solutions for the most common issues encountered by AquaScene Content Engine users. Remember:

- ✅ **Start Simple**: Check system status and try basic solutions first
- ✅ **Document Issues**: Keep track of error messages and steps taken
- ✅ **Follow Procedures**: Use systematic diagnosis before trying advanced solutions
- ✅ **Know When to Escalate**: Don't spend too long on complex issues
- ✅ **Learn from Issues**: Update procedures based on new problems encountered

Most issues can be resolved quickly by following the appropriate section of this guide. When in doubt, check the system status dashboard first and contact support with specific details about the problem.

---

**Document Status:** Complete ✅  
**Review Date:** August 6, 2025  
**Next Review:** September 6, 2025  
**Owner:** AquaScene Support Team  
**Emergency Contact:** [To be filled by administrator]