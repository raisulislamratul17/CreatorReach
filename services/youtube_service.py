import os
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dateutil import parser as date_parser


class YouTubeService:
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError('YOUTUBE_API_KEY environment variable is required')
        
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
    
    def search_channels(self, keyword, max_results=50):
        """Search for videos and extract unique channel data"""
        # Search for videos
        search_response = self.youtube.search().list(
            q=keyword,
            part='id,snippet',
            type='video',
            maxResults=max_results,
            order='relevance'
        ).execute()
        
        # Extract unique channel IDs
        channel_ids = set()
        video_channel_map = {}
        
        for item in search_response.get('items', []):
            channel_id = item['snippet']['channelId']
            channel_ids.add(channel_id)
            video_channel_map[item['id']['videoId']] = channel_id
        
        if not channel_ids:
            return []
        
        # Fetch channel details
        channels_data = []
        channel_ids_list = list(channel_ids)
        
        # YouTube API allows max 50 ids per request
        for i in range(0, len(channel_ids_list), 50):
            batch_ids = channel_ids_list[i:i+50]
            
            channels_response = self.youtube.channels().list(
                part='snippet,statistics,contentDetails',
                id=','.join(batch_ids)
            ).execute()
            
            for channel in channels_response.get('items', []):
                channel_data = self._process_channel(channel)
                if channel_data:
                    # Get recent uploads
                    recent_videos = self._get_recent_videos(channel['id'])
                    channel_data['recent_videos'] = recent_videos
                    channels_data.append(channel_data)
        
        return channels_data
    
    def _process_channel(self, channel):
        """Process raw channel data into structured format"""
        snippet = channel.get('snippet', {})
        statistics = channel.get('statistics', {})
        
        subscriber_count = int(statistics.get('subscriberCount', 0))
        video_count = int(statistics.get('videoCount', 0))
        
        return {
            'channel_id': channel['id'],
            'channel_name': snippet.get('title', ''),
            'channel_url': f"https://www.youtube.com/channel/{channel['id']}",
            'subscriber_count': subscriber_count,
            'total_videos': video_count,
            'description': snippet.get('description', ''),
            'published_at': snippet.get('publishedAt', ''),
            'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', '')
        }
    
    def _get_recent_videos(self, channel_id, max_results=5):
        """Get recent uploads from a channel"""
        # Get upload playlist ID
        channel_response = self.youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()
        
        if not channel_response.get('items'):
            return []
        
        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get recent videos from uploads playlist
        playlist_response = self.youtube.playlistItems().list(
            part='snippet,contentDetails',
            playlistId=uploads_playlist_id,
            maxResults=max_results
        ).execute()
        
        videos = []
        video_ids = []
        
        for item in playlist_response.get('items', []):
            video_ids.append(item['contentDetails']['videoId'])
            videos.append({
                'video_id': item['contentDetails']['videoId'],
                'title': item['snippet']['title'],
                'published_at': item['snippet']['publishedAt']
            })
        
        if not video_ids:
            return []
        
        # Get video statistics
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            
            video_response = self.youtube.videos().list(
                part='statistics',
                id=','.join(batch_ids)
            ).execute()
            
            for video in video_response.get('items', []):
                for v in videos:
                    if v['video_id'] == video['id']:
                        v['view_count'] = int(video['statistics'].get('viewCount', 0))
                        v['like_count'] = int(video['statistics'].get('likeCount', 0))
                        v['comment_count'] = int(video['statistics'].get('commentCount', 0))
        
        return videos
    
    def get_channel_details(self, channel_id):
        """Get detailed information about a specific channel"""
        response = self.youtube.channels().list(
            part='snippet,statistics,contentDetails,brandingSettings',
            id=channel_id
        ).execute()
        
        if not response.get('items'):
            return None
        
        return self._process_channel(response['items'][0])
