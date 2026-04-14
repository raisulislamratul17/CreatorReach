from datetime import datetime, timedelta
from dateutil import parser as date_parser


class LeadAnalyzer:
    """Analyze YouTube channels and filter based on criteria"""
    
    # Filter criteria
    MIN_SUBSCRIBERS = 500
    MAX_SUBSCRIBERS = 50000
    MIN_VIDEOS = 5
    MIN_ENGAGEMENT_RATIO = 0.1
    RECENT_UPLOAD_DAYS = 14
    
    def analyze_channel(self, channel_data):
        """Analyze a channel and return enriched data or None if filtered out"""
        # Basic filtering
        subscriber_count = channel_data.get('subscriber_count', 0)
        total_videos = channel_data.get('total_videos', 0)
        
        if not self._passes_basic_filters(subscriber_count, total_videos):
            return None
        
        recent_videos = channel_data.get('recent_videos', [])
        
        # Check recent upload activity
        if not self._has_recent_uploads(recent_videos):
            return None
        
        # Calculate metrics
        avg_views = self._calculate_avg_views(recent_videos)
        engagement_ratio = avg_views / subscriber_count if subscriber_count > 0 else 0
        
        if engagement_ratio < self.MIN_ENGAGEMENT_RATIO:
            return None
        
        # Calculate scores
        upload_frequency_score = self._calculate_upload_frequency_score(recent_videos)
        engagement_score = self._calculate_engagement_score(recent_videos, subscriber_count)
        growth_signal = self._calculate_growth_signal(recent_videos)
        activity_score = self._calculate_activity_score(
            upload_frequency_score, engagement_score, growth_signal
        )
        
        return {
            'avg_views': avg_views,
            'engagement_ratio': round(engagement_ratio, 3),
            'upload_frequency_score': round(upload_frequency_score, 2),
            'engagement_score': round(engagement_score, 2),
            'growth_signal': round(growth_signal, 2),
            'activity_score': round(activity_score, 2),
            'passes_filter': True
        }
    
    def _passes_basic_filters(self, subscriber_count, total_videos):
        """Check if channel passes basic subscriber and video count filters"""
        return (
            self.MIN_SUBSCRIBERS <= subscriber_count <= self.MAX_SUBSCRIBERS and
            total_videos >= self.MIN_VIDEOS
        )
    
    def _has_recent_uploads(self, recent_videos):
        """Check if channel has uploaded within the last N days"""
        if not recent_videos:
            return False
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.RECENT_UPLOAD_DAYS)
        
        for video in recent_videos:
            try:
                published_at = date_parser.parse(video['published_at'])
                if published_at.replace(tzinfo=None) >= cutoff_date:
                    return True
            except (KeyError, ValueError):
                continue
        
        return False
    
    def _calculate_avg_views(self, recent_videos):
        """Calculate average views from recent videos"""
        if not recent_videos:
            return 0
        
        total_views = sum(v.get('view_count', 0) for v in recent_videos)
        return total_views // len(recent_videos)
    
    def _calculate_upload_frequency_score(self, recent_videos):
        """Calculate upload frequency score (0-100)"""
        if not recent_videos or len(recent_videos) < 2:
            return 0
        
        try:
            dates = [date_parser.parse(v['published_at']) for v in recent_videos]
            dates.sort(reverse=True)
            
            # Calculate average days between uploads
            days_between = []
            for i in range(len(dates) - 1):
                delta = (dates[i] - dates[i + 1]).days
                days_between.append(delta)
            
            avg_days = sum(days_between) / len(days_between) if days_between else 30
            
            # Score: More frequent uploads = higher score
            # Daily uploads = 100, Weekly = 70, Bi-weekly = 40, Monthly = 20
            if avg_days <= 1:
                return 100
            elif avg_days <= 3:
                return 90
            elif avg_days <= 7:
                return 70
            elif avg_days <= 14:
                return 40
            elif avg_days <= 30:
                return 20
            else:
                return 10
        except (KeyError, ValueError):
            return 0
    
    def _calculate_engagement_score(self, recent_videos, subscriber_count):
        """Calculate engagement score based on views, likes, and comments"""
        if not recent_videos or subscriber_count == 0:
            return 0
        
        total_score = 0
        
        for video in recent_videos:
            view_count = video.get('view_count', 0)
            like_count = video.get('like_count', 0)
            comment_count = video.get('comment_count', 0)
            
            # View ratio (views / subscribers)
            view_ratio = view_count / subscriber_count
            
            # Engagement rate (likes + comments) / views
            engagement_rate = (like_count + comment_count) / view_count if view_count > 0 else 0
            
            # Combined score for this video
            video_score = (view_ratio * 50) + (engagement_rate * 50)
            total_score += min(video_score, 100)
        
        return min(total_score / len(recent_videos), 100)
    
    def _calculate_growth_signal(self, recent_videos):
        """Calculate growth signal based on recent vs older video performance"""
        if not recent_videos or len(recent_videos) < 2:
            return 0
        
        try:
            # Sort by published date
            sorted_videos = sorted(
                recent_videos,
                key=lambda x: date_parser.parse(x['published_at']),
                reverse=True
            )
            
            # Split into recent and older
            mid = len(sorted_videos) // 2
            recent = sorted_videos[:mid]
            older = sorted_videos[mid:]
            
            if not recent or not older:
                return 50
            
            recent_avg_views = sum(v.get('view_count', 0) for v in recent) / len(recent)
            older_avg_views = sum(v.get('view_count', 0) for v in older) / len(older)
            
            if older_avg_views == 0:
                return 100 if recent_avg_views > 0 else 0
            
            growth_rate = (recent_avg_views - older_avg_views) / older_avg_views
            
            # Normalize to 0-100 scale
            # Growth rate > 100% = 100, 0% = 50, -50% = 0
            if growth_rate > 1.0:
                return 100
            elif growth_rate > 0:
                return 50 + int(growth_rate * 50)
            else:
                return max(0, 50 + int(growth_rate * 100))
        
        except (KeyError, ValueError):
            return 0
    
    def _calculate_activity_score(self, upload_score, engagement_score, growth_signal):
        """Calculate overall activity score (0-100)"""
        weights = {
            'upload': 0.3,
            'engagement': 0.4,
            'growth': 0.3
        }
        
        score = (
            upload_score * weights['upload'] +
            engagement_score * weights['engagement'] +
            growth_signal * weights['growth']
        )
        
        return min(max(score, 0), 100)
