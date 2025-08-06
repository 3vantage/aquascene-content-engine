"""
Instagram Automation System - Main Orchestrator
Coordinates all components of the Instagram automation system for aquascaping content.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# Import all system components
from .config.config_manager import ConfigManager, SystemConfig
from .api.instagram_client import InstagramBusinessAPI, InstagramPost
from .scheduler.content_scheduler import ContentScheduler, AutomatedPublisher, PostType
from .queue.content_queue import ContentQueueManager, QueueStatus, ContentSource
from .analytics.performance_tracker import PerformanceTracker
from .utils.hashtag_optimizer import HashtagOptimizer, ContentCategory
from .utils.error_handler import ErrorRecoveryManager, HealthChecker
from .templates.content_templates import AquascapingContentTemplates, Language
from .templates.visual.template_generator import VisualTemplateGenerator


class InstagramAutomationSystem:
    """
    Main orchestrator for the Instagram automation system.
    Coordinates all components and manages the automation workflow.
    """
    
    def __init__(self, config_dir: str = None):
        # Initialize configuration
        self.config_manager = ConfigManager(config_dir)
        self.config: SystemConfig = None
        
        # Initialize logging
        self.logger = None
        
        # System components
        self.instagram_api: Optional[InstagramBusinessAPI] = None
        self.scheduler: Optional[ContentScheduler] = None
        self.queue_manager: Optional[ContentQueueManager] = None
        self.performance_tracker: Optional[PerformanceTracker] = None
        self.hashtag_optimizer: Optional[HashtagOptimizer] = None
        self.error_manager: Optional[ErrorRecoveryManager] = None
        self.health_checker: Optional[HealthChecker] = None
        self.content_templates: Optional[AquascapingContentTemplates] = None
        self.visual_generator: Optional[VisualTemplateGenerator] = None
        self.publisher: Optional[AutomatedPublisher] = None
        
        # System state
        self.is_running = False
        self.startup_time: Optional[datetime] = None
        
    def initialize(self, config_file: str = None) -> bool:
        """
        Initialize the automation system with configuration.
        """
        try:
            # Load configuration
            self.config = self.config_manager.load_config(config_file)
            
            # Setup logging
            self._setup_logging()
            
            self.logger.info("Initializing Instagram Automation System...")
            
            # Initialize core components
            self._initialize_api_client()
            self._initialize_storage_components()
            self._initialize_processing_components()
            self._initialize_automation_components()
            
            self.logger.info("Instagram Automation System initialized successfully")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to initialize system: {e}")
            else:
                print(f"Failed to initialize system: {e}")
            return False
    
    def _setup_logging(self):
        """Setup logging configuration"""
        
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('instagram_automation.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
        if self.config.debug_mode:
            self.logger.setLevel(logging.DEBUG)
    
    def _initialize_api_client(self):
        """Initialize Instagram API client"""
        
        self.instagram_api = InstagramBusinessAPI(
            access_token=self.config.instagram_api.access_token,
            business_account_id=self.config.instagram_api.business_account_id
        )
        
        # Test API connection
        try:
            account_info = self.instagram_api.get_account_info()
            self.logger.info(f"Connected to Instagram account: {account_info.get('username')}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Instagram API: {e}")
            raise
    
    def _initialize_storage_components(self):
        """Initialize database and storage components"""
        
        # Content scheduler with database
        self.scheduler = ContentScheduler(self.config.database.scheduler_db_path)
        
        # Content queue manager
        self.queue_manager = ContentQueueManager(self.config.database.queue_db_path)
        
        # Performance tracker
        self.performance_tracker = PerformanceTracker(
            self.instagram_api, 
            self.config.database.analytics_db_path
        )
        
        # Hashtag optimizer
        self.hashtag_optimizer = HashtagOptimizer(self.config.database.hashtag_db_path)
        
        self.logger.info("Storage components initialized")
    
    def _initialize_processing_components(self):
        """Initialize content processing components"""
        
        # Error handling and recovery
        self.error_manager = ErrorRecoveryManager()
        self.health_checker = HealthChecker()
        
        # Content templates
        self.content_templates = AquascapingContentTemplates()
        
        # Visual template generator
        self.visual_generator = VisualTemplateGenerator()
        
        self.logger.info("Processing components initialized")
    
    def _initialize_automation_components(self):
        """Initialize automation components"""
        
        # Automated publisher
        self.publisher = AutomatedPublisher(self.instagram_api, self.scheduler)
        
        self.logger.info("Automation components initialized")
    
    async def start(self):
        """Start the automation system"""
        
        if not self.config:
            raise RuntimeError("System not initialized. Call initialize() first.")
        
        self.is_running = True
        self.startup_time = datetime.now()
        
        self.logger.info("Starting Instagram Automation System...")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Start background tasks
        tasks = [
            self._start_publisher(),
            self._start_analytics_collection(),
            self._start_health_monitoring(),
            self._start_maintenance_tasks()
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            self.logger.info("System shutdown requested")
        except Exception as e:
            self.logger.error(f"System error: {e}")
            self.error_manager.handle_error(e, {"component": "main_system"})
        finally:
            await self._shutdown()
    
    async def _start_publisher(self):
        """Start the automated publisher"""
        
        if self.config.scheduling.default_posts_per_day > 0:
            self.logger.info("Starting automated publisher...")
            check_interval = 300  # 5 minutes
            await self.publisher.start_publishing_loop(check_interval)
        else:
            self.logger.info("Automated publishing disabled")
    
    async def _start_analytics_collection(self):
        """Start analytics collection"""
        
        if not self.config.analytics.collection_enabled:
            return
        
        self.logger.info("Starting analytics collection...")
        
        while self.is_running:
            try:
                # Collect metrics every collection_interval_hours
                await asyncio.sleep(self.config.analytics.collection_interval_hours * 3600)
                
                if self.is_running:
                    self.logger.debug("Collecting performance metrics...")
                    await asyncio.get_event_loop().run_in_executor(
                        None, 
                        self.performance_tracker.collect_post_metrics, 
                        7  # Last 7 days
                    )
                    
            except Exception as e:
                self.logger.error(f"Analytics collection error: {e}")
                self.error_manager.handle_error(e, {"component": "analytics"})
                await asyncio.sleep(3600)  # Wait 1 hour before retry
    
    async def _start_health_monitoring(self):
        """Start health monitoring"""
        
        self.logger.info("Starting health monitoring...")
        
        while self.is_running:
            try:
                await asyncio.sleep(self.config.analytics.health_check_interval_minutes * 60)
                
                if self.is_running:
                    health_report = self.health_checker.check_system_health()
                    
                    if health_report['overall_status'] != 'healthy':
                        self.logger.warning(f"System health: {health_report['overall_status']}")
                        
                        # Send notifications if configured
                        if self.config.notifications.enabled:
                            await self._send_health_notification(health_report)
                    
                    self.logger.debug(f"Health check completed: {health_report['overall_status']}")
                    
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(1800)  # Wait 30 minutes before retry
    
    async def _start_maintenance_tasks(self):
        """Start periodic maintenance tasks"""
        
        self.logger.info("Starting maintenance tasks...")
        
        while self.is_running:
            try:
                # Run maintenance every 24 hours
                await asyncio.sleep(24 * 3600)
                
                if self.is_running:
                    await self._run_maintenance()
                    
            except Exception as e:
                self.logger.error(f"Maintenance task error: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry
    
    async def _run_maintenance(self):
        """Run periodic maintenance tasks"""
        
        self.logger.info("Running maintenance tasks...")
        
        try:
            # Clean old data based on retention policy
            retention_cutoff = datetime.now() - timedelta(days=self.config.analytics.retention_days)
            
            # Database cleanup would go here
            # self._cleanup_old_data(retention_cutoff)
            
            # Generate performance reports
            if self.config.analytics.collection_enabled:
                report = self.performance_tracker.generate_performance_report(30)
                self.logger.info(f"Monthly report: {report.total_posts} posts, {report.avg_engagement_rate:.2f}% avg engagement")
            
            # Update hashtag performance
            # This would analyze recent post performance and update hashtag scores
            
            self.logger.info("Maintenance tasks completed")
            
        except Exception as e:
            self.logger.error(f"Maintenance error: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}")
        self.is_running = False
    
    async def _shutdown(self):
        """Graceful shutdown"""
        
        self.logger.info("Shutting down Instagram Automation System...")
        
        # Stop publisher
        if self.publisher:
            self.publisher.stop()
        
        # Close API client
        if self.instagram_api:
            self.instagram_api.close()
        
        uptime = datetime.now() - self.startup_time if self.startup_time else timedelta(0)
        self.logger.info(f"System shutdown complete. Uptime: {uptime}")
    
    async def _send_health_notification(self, health_report: Dict):
        """Send health notification"""
        
        # Implementation would depend on configured notification channels
        # For now, just log
        self.logger.warning(f"Health alert: {health_report}")
    
    # Public API methods for manual operations
    
    def add_content_to_queue(self, title: str, caption: str, media_url: str,
                           post_type: PostType = PostType.SHOWCASE,
                           hashtags: List[str] = None,
                           language: str = None) -> str:
        """Add content to the queue manually"""
        
        if not hashtags:
            # Auto-generate hashtags
            content_category = self._map_post_type_to_category(post_type)
            language = language or self.config.content.default_language
            hashtags = self.hashtag_optimizer.generate_hashtag_set(
                content_category, 
                target_language=language,
                max_hashtags=self.config.content.max_hashtags
            )
        
        # Create Instagram post
        instagram_post = InstagramPost(
            caption=caption,
            media_type="IMAGE",
            media_url=media_url,
            hashtags=hashtags
        )
        
        # Add to queue
        content_id = self.queue_manager.add_content(
            title=title,
            content=instagram_post,
            post_type=post_type,
            content_source=ContentSource.MANUAL,
            created_by="manual_user"
        )
        
        self.logger.info(f"Content added to queue: {content_id}")
        return content_id
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        
        if not self.is_running:
            return {"status": "stopped"}
        
        # Get queue statistics
        queue_stats = self.queue_manager.get_queue_statistics()
        
        # Get recent performance
        uptime = datetime.now() - self.startup_time if self.startup_time else timedelta(0)
        
        return {
            "status": "running",
            "uptime_seconds": uptime.total_seconds(),
            "queue_stats": queue_stats,
            "config": {
                "environment": self.config.environment.value,
                "posts_per_day": self.config.scheduling.default_posts_per_day,
                "language": self.config.content.default_language
            }
        }
    
    def _map_post_type_to_category(self, post_type: PostType) -> ContentCategory:
        """Map post type to content category"""
        
        mapping = {
            PostType.EDUCATIONAL: ContentCategory.TUTORIAL,
            PostType.SHOWCASE: ContentCategory.AQUASCAPING,
            PostType.TUTORIAL: ContentCategory.TUTORIAL,
            PostType.COMMUNITY: ContentCategory.COMMUNITY,
            PostType.BEHIND_SCENES: ContentCategory.AQUASCAPING,
            PostType.PARTNERSHIP: ContentCategory.COMMUNITY
        }
        
        return mapping.get(post_type, ContentCategory.AQUASCAPING)


# Main entry point
async def main(config_file: str = None):
    """Main entry point for the automation system"""
    
    # Create and initialize system
    system = InstagramAutomationSystem()
    
    if not system.initialize(config_file):
        print("Failed to initialize system")
        sys.exit(1)
    
    # Start the system
    try:
        await system.start()
    except KeyboardInterrupt:
        print("Shutdown requested")
    except Exception as e:
        print(f"System error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Instagram Automation System")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--create-config", action="store_true", help="Create sample configuration")
    
    args = parser.parse_args()
    
    if args.create_config:
        # Create sample configuration
        config_manager = ConfigManager()
        sample_config = config_manager.create_sample_config()
        config_manager.save_config(sample_config)
        print("Sample configuration created in config/config.yaml")
        print("Please update the configuration with your Instagram API credentials")
        sys.exit(0)
    
    # Run the system
    asyncio.run(main(args.config))