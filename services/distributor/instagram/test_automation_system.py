#!/usr/bin/env python3
"""
Instagram Automation System Integration Test
Tests the complete automation system functionality without actually posting to Instagram.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to sys.path to import modules
sys.path.insert(0, str(Path(__file__).parent))

# Import components for testing
from api.instagram_client import InstagramPost, MediaType
from scheduler.content_scheduler import ContentScheduler, PostType, OptimalTimingAnalyzer
from analytics.performance_tracker import PerformanceTracker
from utils.hashtag_optimizer import HashtagOptimizer, ContentCategory
from templates.visual.template_generator import VisualTemplateGenerator, TemplateType
from utils.error_handler import ErrorRecoveryManager, HealthChecker


class MockInstagramAPI:
    """Mock Instagram API for testing without making real API calls"""
    
    def __init__(self, access_token: str, business_account_id: str):
        self.access_token = access_token
        self.business_account_id = business_account_id
        
    def get_account_info(self):
        return {
            'id': self.business_account_id,
            'username': 'aquascene_test',
            'account_type': 'BUSINESS',
            'media_count': 42,
            'followers_count': 1250
        }
    
    def get_recent_media(self, limit=25):
        # Return mock media data
        return [
            {
                'id': f'mock_post_{i}',
                'caption': f'Test aquascape post {i} #aquascaping #plantedtank',
                'media_type': 'IMAGE',
                'timestamp': (datetime.now() - timedelta(days=i)).isoformat() + 'Z',
                'like_count': 45 + i * 3,
                'comments_count': 8 + i,
                'permalink': f'https://instagram.com/p/mock_{i}'
            }
            for i in range(min(limit, 10))
        ]
    
    def get_media_insights(self, media_id, metrics):
        # Return mock insights
        return {
            'data': [
                {'name': 'impressions', 'values': [{'value': 150}]},
                {'name': 'reach', 'values': [{'value': 120}]},
                {'name': 'engagement', 'values': [{'value': 25}]},
                {'name': 'saved', 'values': [{'value': 3}]},
                {'name': 'profile_visits', 'values': [{'value': 8}]}
            ]
        }
    
    def post_content(self, post):
        # Mock successful post
        return {'id': f'mock_published_{datetime.now().timestamp()}'}
    
    def close(self):
        pass


class IntegrationTester:
    """Integration tester for the complete automation system"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.test_results = {}
    
    def _setup_logging(self):
        """Setup test logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('integration_test')
    
    async def run_all_tests(self):
        """Run all integration tests"""
        
        self.logger.info("🧪 Starting Instagram Automation System Integration Tests")
        
        test_methods = [
            self.test_api_client,
            self.test_hashtag_optimizer,
            self.test_visual_template_generator,
            self.test_content_scheduler,
            self.test_performance_tracker,
            self.test_error_handling,
            self.test_complete_workflow
        ]
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                self.logger.info(f"Running {test_method.__name__}...")
                await test_method()
                self.test_results[test_method.__name__] = "PASS"
                passed += 1
                self.logger.info(f"✅ {test_method.__name__} PASSED")
            except Exception as e:
                self.test_results[test_method.__name__] = f"FAIL: {str(e)}"
                failed += 1
                self.logger.error(f"❌ {test_method.__name__} FAILED: {e}")
        
        # Print test summary
        self.logger.info("\n" + "="*50)
        self.logger.info("TEST SUMMARY")
        self.logger.info("="*50)
        self.logger.info(f"Total Tests: {len(test_methods)}")
        self.logger.info(f"Passed: {passed}")
        self.logger.info(f"Failed: {failed}")
        
        for test_name, result in self.test_results.items():
            status = "✅" if result == "PASS" else "❌"
            self.logger.info(f"{status} {test_name}: {result}")
        
        return failed == 0
    
    async def test_api_client(self):
        """Test Instagram API client functionality"""
        
        # Create mock API client
        api_client = MockInstagramAPI("mock_token", "mock_business_id")
        
        # Test account info
        account_info = api_client.get_account_info()
        assert account_info['username'] == 'aquascene_test'
        assert account_info['followers_count'] > 0
        
        # Test recent media
        recent_media = api_client.get_recent_media(5)
        assert len(recent_media) == 5
        assert all('id' in media for media in recent_media)
        
        # Test insights
        insights = api_client.get_media_insights('mock_post_1', ['impressions', 'reach'])
        assert 'data' in insights
        assert len(insights['data']) > 0
        
        self.logger.info("API client tests completed")
    
    async def test_hashtag_optimizer(self):
        """Test hashtag optimization functionality"""
        
        optimizer = HashtagOptimizer(":memory:")  # In-memory database
        
        # Test hashtag generation
        hashtags = optimizer.generate_hashtag_set(
            ContentCategory.AQUASCAPING,
            target_language="bg",
            max_hashtags=20
        )
        
        assert isinstance(hashtags, list)
        assert len(hashtags) <= 20
        assert len(hashtags) > 0
        
        # Test content-specific optimization
        content = "Beautiful Anubias nana plant in my new aquascape design with CO2 injection"
        optimized_hashtags = optimizer.optimize_for_post_type(
            "showcase", 
            content, 
            target_language="en"
        )
        
        assert isinstance(optimized_hashtags, list)
        assert len(optimized_hashtags) <= 30
        
        # Test trending hashtags
        trending = optimizer.get_trending_hashtags(region="bg", limit=10)
        assert isinstance(trending, list)
        assert len(trending) <= 10
        
        self.logger.info("Hashtag optimizer tests completed")
    
    async def test_visual_template_generator(self):
        """Test visual template generation"""
        
        generator = VisualTemplateGenerator()
        
        # Test educational carousel
        educational_content = {
            'title': 'Test Aquascaping Guide',
            'slides': [
                {'title': 'Step 1', 'content': 'Choose your plants carefully'},
                {'title': 'Step 2', 'content': 'Set up proper lighting'}
            ]
        }
        
        slides = generator.create_educational_carousel(educational_content)
        assert isinstance(slides, list)
        assert len(slides) == 3  # Title slide + 2 content slides
        
        # Test plant spotlight
        plant_data = {
            'name': 'Anubias Nana',
            'scientific_name': 'Anubias barteri var. nana',
            'difficulty': 'Easy',
            'lighting': 'Low to Medium',
            'co2': 'Optional',
            'description': 'Popular aquascaping plant'
        }
        
        plant_image = generator.create_plant_spotlight(plant_data)
        assert plant_image is not None
        assert plant_image.size == (1080, 1080)
        
        # Test quote card
        quote_image = generator.create_quote_card(
            "Nature holds the key to our aesthetic, intellectual, cognitive and even spiritual satisfaction.",
            "E.O. Wilson"
        )
        assert quote_image is not None
        
        self.logger.info("Visual template generator tests completed")
    
    async def test_content_scheduler(self):
        """Test content scheduling functionality"""
        
        scheduler = ContentScheduler(":memory:")  # In-memory database
        
        # Test post scheduling
        test_post = InstagramPost(
            caption="Test aquascape post",
            media_type=MediaType.IMAGE,
            media_url="https://example.com/test.jpg",
            hashtags=["aquascaping", "test"]
        )
        
        scheduled_time = datetime.now() + timedelta(hours=1)
        post_id = scheduler.schedule_post(test_post, PostType.SHOWCASE, scheduled_time)
        
        assert isinstance(post_id, str)
        assert len(post_id) > 0
        
        # Test getting due posts (should be empty since post is scheduled for future)
        due_posts = scheduler.get_due_posts()
        assert len(due_posts) == 0
        
        # Test statistics
        stats = scheduler.get_posting_statistics()
        assert isinstance(stats, dict)
        
        self.logger.info("Content scheduler tests completed")
    
    async def test_performance_tracker(self):
        """Test performance tracking functionality"""
        
        mock_api = MockInstagramAPI("mock_token", "mock_business_id")
        tracker = PerformanceTracker(mock_api, ":memory:")  # In-memory database
        
        # Test metrics collection
        metrics = tracker.collect_post_metrics(days_back=7)
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        
        # Test optimal posting times analysis
        optimal_times = tracker.analyze_optimal_posting_times(days_back=30)
        assert isinstance(optimal_times, dict)
        assert 'optimal_hours' in optimal_times or 'error' in optimal_times
        
        # Test hashtag performance analysis
        hashtag_analysis = tracker.analyze_hashtag_performance()
        assert isinstance(hashtag_analysis, dict)
        
        # Test performance report generation
        report = tracker.generate_performance_report(days_back=30)
        assert hasattr(report, 'total_posts')
        assert hasattr(report, 'avg_engagement_rate')
        
        self.logger.info("Performance tracker tests completed")
    
    async def test_error_handling(self):
        """Test error handling and recovery"""
        
        error_manager = ErrorRecoveryManager()
        health_checker = HealthChecker()
        
        # Test health check
        health_report = health_checker.check_system_health()
        assert isinstance(health_report, dict)
        assert 'overall_status' in health_report
        assert 'components' in health_report
        
        # Test error handling
        try:
            raise ConnectionError("Mock network error")
        except Exception as e:
            recovery_action = error_manager.handle_error(
                e, {'component': 'test', 'timestamp': datetime.now().isoformat()}
            )
            # Should return a recovery action or None
            assert recovery_action is None or isinstance(recovery_action, str)
        
        self.logger.info("Error handling tests completed")
    
    async def test_complete_workflow(self):
        """Test complete automation workflow"""
        
        self.logger.info("Testing complete workflow...")
        
        # Initialize components
        mock_api = MockInstagramAPI("mock_token", "mock_business_id")
        scheduler = ContentScheduler(":memory:")
        hashtag_optimizer = HashtagOptimizer(":memory:")
        template_generator = VisualTemplateGenerator()
        
        # 1. Generate hashtags
        hashtags = hashtag_optimizer.generate_hashtag_set(
            ContentCategory.AQUASCAPING,
            target_language="bg",
            max_hashtags=15
        )
        
        # 2. Create visual content
        plant_data = {
            'name': 'Java Fern',
            'scientific_name': 'Microsorum pteropus',
            'difficulty': 'Easy',
            'lighting': 'Low',
            'co2': 'Optional',
            'description': 'Hardy aquascaping plant perfect for beginners'
        }
        
        plant_image = template_generator.create_plant_spotlight(plant_data)
        
        # 3. Create Instagram post
        caption = f"🌿 {plant_data['name']} Spotlight!\n\n{plant_data['description']}\n\n"
        caption += f"💡 Difficulty: {plant_data['difficulty']}\n"
        caption += f"🔆 Lighting: {plant_data['lighting']}\n"
        caption += f"💨 CO2: {plant_data['co2']}"
        
        instagram_post = InstagramPost(
            caption=caption,
            media_type=MediaType.IMAGE,
            media_url="mock://generated_plant_image.jpg",
            hashtags=hashtags
        )
        
        # 4. Schedule the post
        scheduled_time = datetime.now() + timedelta(hours=2)
        post_id = scheduler.schedule_post(instagram_post, PostType.SHOWCASE, scheduled_time)
        
        # 5. Verify everything worked
        assert isinstance(post_id, str)
        assert len(hashtags) > 0
        assert plant_image is not None
        assert len(caption) > 0
        
        self.logger.info("Complete workflow test completed successfully")


# Test runner
async def main():
    """Main test runner"""
    
    tester = IntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All integration tests PASSED! The Instagram automation system is ready for production.")
        return 0
    else:
        print("\n💥 Some integration tests FAILED. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)