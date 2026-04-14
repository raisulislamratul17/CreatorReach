import os
import re
from typing import List, Dict, Any


class AIEnrichment:
    """Enrich channel data using AI classification and tagging"""
    
    # Common niche keywords for classification
    NICHE_KEYWORDS = {
        'gaming': ['game', 'gaming', 'gameplay', 'playthrough', 'walkthrough', 'lets play', 
                   'minecraft', 'fortnite', 'call of duty', 'gta', 'valorant', 'roblox',
                   'streamer', 'twitch', 'esports', 'competitive'],
        
        'education': ['tutorial', 'learn', 'course', 'education', 'how to', 'lesson',
                      'study', 'academic', 'university', 'college', 'school', 'lecture',
                      'explained', 'guide', 'tips', 'tricks', 'beginner', 'advanced'],
        
        'vlog': ['vlog', 'day in the life', 'daily', 'routine', 'morning', 'night routine',
                 'lifestyle', 'haul', 'unboxing', 'review', 'get ready with me', 'grwm'],
        
        'tech': ['tech', 'technology', 'review', 'unboxing', 'gadget', 'phone', 'laptop',
                 'computer', 'software', 'app', 'coding', 'programming', 'developer'],
        
        'fitness': ['fitness', 'workout', 'gym', 'exercise', 'health', 'diet', 'nutrition',
                    'bodybuilding', 'weight loss', 'yoga', 'training', 'cardio'],
        
        'food': ['food', 'cooking', 'recipe', 'chef', 'kitchen', 'baking', 'restaurant',
                 'review', 'mukbang', 'eating', 'taste test', 'foodie', 'cuisine'],
        
        'travel': ['travel', 'traveling', 'trip', 'vacation', 'adventure', 'explore',
                   'destination', 'hotel', 'airbnb', 'backpacking', 'wanderlust'],
        
        'fashion': ['fashion', 'style', 'outfit', 'clothing', 'streetwear', 'luxury',
                    'designer', 'brand', 'lookbook', 'ootd', 'shopping', 'haul'],
        
        'beauty': ['beauty', 'makeup', 'skincare', 'hair', 'cosmetics', 'tutorial',
                   'transformation', 'glam', 'review', 'routine'],
        
        'entertainment': ['comedy', 'funny', 'sketch', 'parody', 'reaction', 'meme',
                          'entertainment', 'show', 'series', 'prank', 'challenge'],
        
        'music': ['music', 'song', 'cover', 'remix', 'instrumental', 'guitar', 'piano',
                  'singing', 'vocals', 'band', 'artist', 'concert', 'performance'],
        
        'finance': ['finance', 'money', 'invest', 'stock', 'crypto', 'bitcoin', 'trading',
                    'wealth', 'rich', 'passive income', 'business', 'entrepreneur']
    }
    
    # Tag thresholds
    HIGH_POTENTIAL_THRESHOLD = 70  # Activity score threshold
    CONSISTENCY_THRESHOLD = 40     # Upload frequency threshold
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self._gemini_quota_exceeded = False  # Track if we hit rate limits
    
    def enrich_channel(self, description: str, recent_videos: List[Dict]) -> Dict[str, Any]:
        """Enrich channel data with AI-powered analysis - prefers Gemini (free tier)"""
        # Try AI APIs first (Gemini preferred for free tier)
        ai_result = None
        
        if self.gemini_api_key:
            ai_result = self._analyze_with_gemini(description, recent_videos)
        elif self.anthropic_api_key:
            ai_result = self._analyze_with_anthropic(description, recent_videos)
        elif self.openai_api_key:
            ai_result = self._analyze_with_openai(description, recent_videos)
        
        if ai_result:
            return ai_result
        
        # Fallback to local keyword analysis
        combined_text = description.lower()
        for video in recent_videos:
            combined_text += ' ' + video.get('title', '').lower()
        
        # Classify niche
        niche = self._classify_niche(combined_text)
        
        # Generate summary
        summary = self._generate_summary(description, recent_videos, niche)
        
        # Generate tags
        tags = self._generate_tags(description, recent_videos)
        
        return {
            'niche': niche,
            'summary': summary,
            'tags': tags
        }
    
    def _classify_niche(self, text: str) -> str:
        """Classify the channel niche based on keyword analysis"""
        scores = {}
        
        for niche, keywords in self.NICHE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            # Weight by number of matches
            scores[niche] = score
        
        if not scores or max(scores.values()) == 0:
            return 'General'
        
        # Get the niche with highest score
        best_niche = max(scores, key=scores.get)
        
        # If score is too low, mark as general
        if scores[best_niche] < 2:
            return 'General'
        
        return best_niche.title()
    
    def _generate_summary(self, description: str, recent_videos: List[Dict], niche: str) -> str:
        """Generate a short summary of the channel"""
        if not description and not recent_videos:
            return 'No information available'
        
        summary_parts = []
        
        # Extract main topic from description
        if description:
            # Get first 2-3 sentences
            sentences = description.split('.')[:3]
            desc_summary = '. '.join(s.strip() for s in sentences if s.strip())
            if desc_summary:
                summary_parts.append(desc_summary)
        
        # Add content type info from recent videos
        if recent_videos:
            video_titles = [v.get('title', '') for v in recent_videos[:3]]
            content_types = self._detect_content_types(video_titles)
            if content_types:
                summary_parts.append(f"Content focuses on: {', '.join(content_types)}")
        
        # Add niche info
        if niche and niche != 'General':
            summary_parts.append(f"Primarily a {niche.lower()} channel")
        
        return ' | '.join(summary_parts) if summary_parts else 'Content creator channel'
    
    def _detect_content_types(self, video_titles: List[str]) -> List[str]:
        """Detect content types from video titles"""
        types = set()
        
        patterns = {
            'tutorials': ['how to', 'tutorial', 'guide', 'learn', 'tips'],
            'reviews': ['review', 'unboxing', 'first look', 'hands on'],
            'vlogs': ['vlog', 'day in', 'morning', 'night routine', 'week in'],
            'gaming': ['gameplay', 'lets play', 'playing', 'live', 'stream'],
            'challenges': ['challenge', '24 hours', 'trying', 'attempt'],
            'reactions': ['reaction', 'reacting to', 'responds', 'responds to'],
            'transformations': ['transformation', 'before and after', 'makeover'],
            'qanda': ['q&a', 'questions', 'faq', 'answering'],
            'behind_the_scenes': ['behind the scenes', 'bts', 'making of', 'how i made']
        }
        
        for title in video_titles:
            title_lower = title.lower()
            for content_type, keywords in patterns.items():
                if any(keyword in title_lower for keyword in keywords):
                    types.add(content_type.replace('_', ' ').title())
        
        return list(types)[:3]  # Return top 3
    
    def _generate_tags(self, description: str, recent_videos: List[Dict]) -> List[str]:
        """Generate tags for the channel based on analysis"""
        tags = []
        
        # Calculate metrics from videos if available
        if recent_videos:
            avg_views = sum(v.get('view_count', 0) for v in recent_videos) / len(recent_videos)
            avg_likes = sum(v.get('like_count', 0) for v in recent_videos) / len(recent_videos)
            
            # High potential tag
            if avg_views > 10000:
                tags.append('high potential')
            
            # Check upload consistency
            from datetime import datetime
            from dateutil import parser as date_parser
            
            try:
                dates = [date_parser.parse(v['published_at']) for v in recent_videos if v.get('published_at')]
                if len(dates) >= 2:
                    dates.sort(reverse=True)
                    days_between = [(dates[i] - dates[i+1]).days for i in range(len(dates)-1)]
                    avg_days = sum(days_between) / len(days_between)
                    
                    # AI enrichment (optional) - prefer Gemini if available (free tier)
                    ai_data = None
                    try:
                        if self.gemini_api_key:
                            ai_data = self._analyze_with_gemini(
                                description,
                                recent_videos
                            )
                        elif self.anthropic_api_key:
                            ai_data = self._analyze_with_anthropic(
                                description,
                                recent_videos
                            )
                        elif self.openai_api_key:
                            ai_data = self._analyze_with_openai(
                                description,
                                recent_videos
                            )
                        
                        if not ai_data:
                            ai_data = self.enrich_channel(
                                description,
                                recent_videos
                            )
                    except Exception as e:
                        ai_data = {'niche': 'Unknown', 'summary': '', 'tags': []}      
                    
                    # Check editing quality indicators
                    if recent_videos:
                        titles = [v.get('title', '') for v in recent_videos]
                        has_professional_indicators = any(
                            indicator in ' '.join(titles).lower()
                            for indicator in ['cinematic', 'edited', 'production', 'professional', 'high quality']
                        )
                        has_basic_indicators = any(
                            indicator in ' '.join(titles).lower()
                            for indicator in ['raw', 'unedited', 'phone', 'quick', 'casual']
                        )
                        
                        if has_basic_indicators and not has_professional_indicators:
                            tags.append('low editing quality')
                        elif has_professional_indicators:
                            tags.append('high production value')
            except Exception:
                pass
            
            # Check consistency
            if avg_days > 14:
                tags.append('needs consistency')
            elif avg_days <= 3:
                tags.append('consistent uploader')
        
        return tags
    
    def _analyze_with_gemini(self, description: str, recent_videos: List[Dict]) -> Dict[str, Any]:
        """Use Google Gemini API for enrichment (free tier available)"""
        if not self.gemini_api_key or self._gemini_quota_exceeded:
            return None
        
        # Try multiple model names (Google changes these frequently)
        models_to_try = [
            'gemini-2.0-flash',
            'gemini-2.0-flash-lite',
            'gemini-1.5-flash',
            'gemini-1.5-flash-8b',
        ]
        
        import time
        import google.generativeai as genai
        genai.configure(api_key=self.gemini_api_key)
        
        video_titles = [v.get('title', '') for v in recent_videos[:5]]
        
        prompt = f"""Analyze this YouTube channel and provide:
1. Niche category (one word: Gaming, Education, Vlog, Tech, Fitness, Food, Travel, Fashion, Beauty, Entertainment, Music, Finance, or General)
2. One sentence summary
3. Tags (high potential, needs consistency, or low editing quality if applicable)

Channel Description: {description[:500]}
Recent Video Titles: {', '.join(video_titles)}

Respond ONLY in JSON format:
{{"niche": "...", "summary": "...", "tags": ["..."]}}"""
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                result = response.text
                
                # Extract JSON from response
                import json
                import re
                
                # Find JSON in the response
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                
                return json.loads(result)
            
            except Exception as e:
                error_msg = str(e)
                # Handle rate limiting (429) - mark as quota exceeded to skip future calls
                if "429" in error_msg or "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                    self._gemini_quota_exceeded = True
                    print(f"Gemini API quota exceeded. Switching to local analysis for remaining channels.")
                    return None
                # Handle 404 (model not found) - try next model
                if "404" in error_msg or "not found" in error_msg.lower():
                    time.sleep(0.5)  # Small delay between model attempts
                    continue
                # Other errors - continue trying
                time.sleep(0.5)
                continue
        
        return None
    
    def _analyze_with_openai(self, description: str, recent_videos: List[Dict]) -> Dict[str, Any]:
        """Use OpenAI API for enrichment (optional)"""
        if not self.openai_api_key:
            return None
        
        try:
            import openai
            openai.api_key = self.openai_api_key
            
            video_titles = [v.get('title', '') for v in recent_videos[:5]]
            
            prompt = f"""Analyze this YouTube channel and provide:
1. Niche category (one word: Gaming, Education, Vlog, Tech, Fitness, Food, Travel, Fashion, Beauty, Entertainment, Music, Finance, or General)
2. One sentence summary
3. Tags (high potential, needs consistency, or low editing quality if applicable)

Channel Description: {description[:500]}
Recent Video Titles: {', '.join(video_titles)}

Respond in JSON format:
{{"niche": "...", "summary": "...", "tags": ["..."]}}"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a YouTube channel analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            import json
            result = response.choices[0].message.content
            return json.loads(result)
        
        except Exception as e:
            print(f"OpenAI enrichment failed: {e}")
            return None
    
    def _analyze_with_anthropic(self, description: str, recent_videos: List[Dict]) -> Dict[str, Any]:
        """Use Anthropic Claude API for enrichment (optional)"""
        if not self.anthropic_api_key:
            return None
        
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            
            video_titles = [v.get('title', '') for v in recent_videos[:5]]
            
            prompt = f"""Analyze this YouTube channel and provide:
1. Niche category (one word: Gaming, Education, Vlog, Tech, Fitness, Food, Travel, Fashion, Beauty, Entertainment, Music, Finance, or General)
2. One sentence summary
3. Tags (high potential, needs consistency, or low editing quality if applicable)

Channel Description: {description[:500]}
Recent Video Titles: {', '.join(video_titles)}

Respond in JSON format:
{{"niche": "...", "summary": "...", "tags": ["..."]}}"""
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            import json
            result = response.content[0].text
            return json.loads(result)
        
        except Exception as e:
            print(f"Anthropic enrichment failed: {e}")
            return None
