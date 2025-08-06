"""
Instagram Business API Client
Compliant implementation for automated posting with rate limiting and error handling.
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import os


class MediaType(Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    CAROUSEL_ALBUM = "CAROUSEL_ALBUM"


@dataclass
class InstagramPost:
    """Data class for Instagram post content"""
    caption: str
    media_type: MediaType
    media_url: str = None
    media_urls: List[str] = None  # For carousel posts
    hashtags: List[str] = None
    scheduled_time: datetime = None
    

class InstagramAPIError(Exception):
    """Custom exception for Instagram API errors"""
    pass


class InstagramBusinessAPI:
    """
    Instagram Business API client with proper rate limiting and compliance.
    Handles authentication, content publishing, and analytics.
    """
    
    def __init__(self, access_token: str, business_account_id: str):
        self.access_token = access_token
        self.business_account_id = business_account_id
        self.base_url = "https://graph.facebook.com/v18.0"
        
        # Rate limiting configuration
        self.requests_per_hour = 200  # Instagram API limit
        self.requests_per_day = 4800
        self.request_timestamps = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Initialize session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AquaScene Content Engine/1.0'
        })
    
    def _check_rate_limit(self) -> bool:
        """
        Enforce rate limiting to stay within API limits.
        Returns True if request can proceed, False if rate limited.
        """
        now = datetime.now()
        
        # Remove timestamps older than 1 hour
        one_hour_ago = now - timedelta(hours=1)
        self.request_timestamps = [
            timestamp for timestamp in self.request_timestamps 
            if timestamp > one_hour_ago
        ]
        
        # Check hourly limit
        if len(self.request_timestamps) >= self.requests_per_hour:
            self.logger.warning("Hourly rate limit reached. Waiting...")
            return False
        
        # Check daily limit (simple check)
        one_day_ago = now - timedelta(days=1)
        daily_requests = [
            timestamp for timestamp in self.request_timestamps 
            if timestamp > one_day_ago
        ]
        
        if len(daily_requests) >= self.requests_per_day:
            self.logger.warning("Daily rate limit reached.")
            return False
        
        self.request_timestamps.append(now)
        return True
    
    def _make_request(self, endpoint: str, method: str = 'GET', 
                     params: Dict = None, data: Dict = None, 
                     files: Dict = None) -> Optional[Dict]:
        """
        Make API request with error handling and rate limiting.
        """
        if not self._check_rate_limit():
            raise InstagramAPIError("Rate limit exceeded")
        
        url = f"{self.base_url}/{endpoint}"
        
        # Add access token to parameters
        if params is None:
            params = {}
        params['access_token'] = self.access_token
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                files=files,
                timeout=30
            )
            
            # Check for API errors
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                self.logger.error(f"API Error {response.status_code}: {error_msg}")
                raise InstagramAPIError(f"API Error {response.status_code}: {error_msg}")
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise InstagramAPIError(f"Request failed: {e}")
    
    def get_account_info(self) -> Dict:
        """Get basic account information"""
        endpoint = f"{self.business_account_id}"
        params = {
            'fields': 'id,username,account_type,media_count,followers_count'
        }
        return self._make_request(endpoint, params=params)
    
    def create_media_object(self, post: InstagramPost) -> str:
        """
        Create a media object for posting.
        Returns the media object ID.
        """
        endpoint = f"{self.business_account_id}/media"
        
        # Prepare caption with hashtags
        caption = post.caption
        if post.hashtags:
            hashtag_string = ' '.join([f'#{tag}' for tag in post.hashtags])
            caption = f"{caption}\n\n{hashtag_string}"
        
        # Validate caption length
        if len(caption) > 2200:
            raise InstagramAPIError("Caption exceeds 2200 character limit")
        
        data = {
            'caption': caption,
            'media_type': post.media_type.value
        }
        
        # Handle different media types
        if post.media_type == MediaType.IMAGE:
            if not post.media_url:
                raise InstagramAPIError("Image URL required for IMAGE posts")
            data['image_url'] = post.media_url
            
        elif post.media_type == MediaType.VIDEO:
            if not post.media_url:
                raise InstagramAPIError("Video URL required for VIDEO posts")
            data['video_url'] = post.media_url
            
        elif post.media_type == MediaType.CAROUSEL_ALBUM:
            if not post.media_urls or len(post.media_urls) < 2:
                raise InstagramAPIError("At least 2 media URLs required for carousel")
            
            # Create individual media objects for carousel
            media_ids = []
            for media_url in post.media_urls:
                child_data = {
                    'image_url': media_url,
                    'is_carousel_item': True
                }
                child_response = self._make_request(endpoint, method='POST', data=child_data)
                media_ids.append(child_response['id'])
            
            data = {
                'caption': caption,
                'media_type': 'CAROUSEL_ALBUM',
                'children': ','.join(media_ids)
            }
        
        response = self._make_request(endpoint, method='POST', data=data)
        return response['id']
    
    def publish_media(self, media_id: str) -> Dict:
        """
        Publish a created media object.
        """
        endpoint = f"{self.business_account_id}/media_publish"
        data = {'creation_id': media_id}
        
        return self._make_request(endpoint, method='POST', data=data)
    
    def post_content(self, post: InstagramPost) -> Dict:
        """
        Complete workflow to post content to Instagram.
        """
        try:
            # Validate content
            self._validate_content(post)
            
            # Create media object
            self.logger.info("Creating media object...")
            media_id = self.create_media_object(post)
            
            # Wait a moment for processing
            time.sleep(2)
            
            # Publish the media
            self.logger.info(f"Publishing media {media_id}...")
            result = self.publish_media(media_id)
            
            self.logger.info(f"Successfully published post: {result.get('id')}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to post content: {e}")
            raise
    
    def _validate_content(self, post: InstagramPost) -> None:
        """
        Validate post content against Instagram policies and limits.
        """
        # Check caption length
        caption_length = len(post.caption)
        if post.hashtags:
            caption_length += sum(len(tag) + 1 for tag in post.hashtags) + 2  # +2 for newlines
        
        if caption_length > 2200:
            raise InstagramAPIError("Total caption exceeds 2200 character limit")
        
        # Check hashtag limits
        if post.hashtags and len(post.hashtags) > 30:
            raise InstagramAPIError("Maximum 30 hashtags allowed")
        
        # Check media requirements
        if post.media_type == MediaType.IMAGE and not post.media_url:
            raise InstagramAPIError("Image URL required for image posts")
        
        if post.media_type == MediaType.VIDEO and not post.media_url:
            raise InstagramAPIError("Video URL required for video posts")
        
        if post.media_type == MediaType.CAROUSEL_ALBUM:
            if not post.media_urls or len(post.media_urls) < 2:
                raise InstagramAPIError("Carousel requires at least 2 media items")
            if len(post.media_urls) > 10:
                raise InstagramAPIError("Carousel limited to 10 media items")
    
    def get_media_insights(self, media_id: str, metrics: List[str] = None) -> Dict:
        """
        Get insights for a specific media post.
        """
        if metrics is None:
            metrics = ['impressions', 'reach', 'engagement', 'saved', 'profile_visits']
        
        endpoint = f"{media_id}/insights"
        params = {
            'metric': ','.join(metrics)
        }
        
        return self._make_request(endpoint, params=params)
    
    def get_account_insights(self, metrics: List[str] = None, 
                           period: str = 'day', since: str = None, 
                           until: str = None) -> Dict:
        """
        Get account-level insights.
        """
        if metrics is None:
            metrics = ['impressions', 'reach', 'profile_views', 'follower_count']
        
        endpoint = f"{self.business_account_id}/insights"
        params = {
            'metric': ','.join(metrics),
            'period': period
        }
        
        if since:
            params['since'] = since
        if until:
            params['until'] = until
        
        return self._make_request(endpoint, params=params)
    
    def get_hashtag_insights(self, hashtag: str) -> Dict:
        """
        Get insights for a specific hashtag (requires approval).
        """
        endpoint = "ig_hashtag_search"
        params = {
            'user_id': self.business_account_id,
            'q': hashtag
        }
        
        search_result = self._make_request(endpoint, params=params)
        
        if search_result and search_result.get('data'):
            hashtag_id = search_result['data'][0]['id']
            
            # Get hashtag insights
            endpoint = f"{hashtag_id}/top_media"
            params = {
                'user_id': self.business_account_id,
                'fields': 'id,caption,media_type,like_count,comments_count'
            }
            
            return self._make_request(endpoint, params=params)
        
        return {}
    
    def get_recent_media(self, limit: int = 25) -> List[Dict]:
        """
        Get recent media from the account.
        """
        endpoint = f"{self.business_account_id}/media"
        params = {
            'fields': 'id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count',
            'limit': limit
        }
        
        response = self._make_request(endpoint, params=params)
        return response.get('data', [])
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'session'):
            self.session.close()


# Example usage and testing
if __name__ == "__main__":
    # Configuration (normally loaded from environment)
    ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    BUSINESS_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    
    if not ACCESS_TOKEN or not BUSINESS_ACCOUNT_ID:
        print("Please set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID environment variables")
        exit(1)
    
    # Initialize client
    client = InstagramBusinessAPI(ACCESS_TOKEN, BUSINESS_ACCOUNT_ID)
    
    try:
        # Test account info
        account_info = client.get_account_info()
        print(f"Account: {account_info.get('username')}")
        print(f"Followers: {account_info.get('followers_count')}")
        
        # Test recent media
        recent_media = client.get_recent_media(limit=5)
        print(f"Recent posts: {len(recent_media)}")
        
    except InstagramAPIError as e:
        print(f"Instagram API Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        client.close()