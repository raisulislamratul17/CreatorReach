import re
from urllib.parse import urlparse


class SocialScraper:
    """Extract social media links and contact information from text"""
    
    # Regex patterns
    EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        re.IGNORECASE
    )
    
    INSTAGRAM_PATTERN = re.compile(
        r'(?:https?://)?(?:www\.)?(?:instagram\.com|instagr\.am)/([a-zA-Z0-9_.]+)',
        re.IGNORECASE
    )
    
    TWITTER_PATTERN = re.compile(
        r'(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)',
        re.IGNORECASE
    )
    
    LINKEDIN_PATTERN = re.compile(
        r'(?:https?://)?(?:www\.)?(?:linkedin\.com)/(?:in|company)/([a-zA-Z0-9-]+)',
        re.IGNORECASE
    )
    
    WEBSITE_PATTERN = re.compile(
        r'https?://(?:www\.)?([a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]\.[a-zA-Z]{2,})',
        re.IGNORECASE
    )
    
    YOUTUBE_PATTERN = re.compile(
        r'(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)',
        re.IGNORECASE
    )
    
    # Common false positives for email
    EMAIL_BLACKLIST = [
        'example.com',
        'test.com',
        'domain.com',
        'email.com',
        'yourdomain.com',
        'sample.com',
        'demo.com'
    ]
    
    def extract_social_links(self, text):
        """Extract all social media links and email from text"""
        if not text:
            return {
                'email': None,
                'instagram': None,
                'twitter': None,
                'linkedin': None,
                'website': None
            }
        
        return {
            'email': self._extract_email(text),
            'instagram': self._extract_instagram(text),
            'twitter': self._extract_twitter(text),
            'linkedin': self._extract_linkedin(text),
            'website': self._extract_website(text)
        }
    
    def _extract_email(self, text):
        """Extract email addresses from text"""
        matches = self.EMAIL_PATTERN.findall(text)
        
        for email in matches:
            # Skip blacklisted domains
            domain = email.split('@')[1].lower()
            if any(bl in domain for bl in self.EMAIL_BLACKLIST):
                continue
            
            # Skip obvious fake emails
            if len(email) < 5 or 'example' in email.lower():
                continue
            
            return email
        
        return None
    
    def _extract_instagram(self, text):
        """Extract Instagram handle or URL"""
        match = self.INSTAGRAM_PATTERN.search(text)
        if match:
            username = match.group(1)
            # Filter out common false positives
            if username.lower() in ['p', 'privacy', 'about', 'help', 'developer']:
                return None
            return f"https://instagram.com/{username}"
        
        # Also check for @username format
        at_pattern = re.compile(r'@([a-zA-Z0-9_.]{3,30})', re.IGNORECASE)
        words = text.split()
        for word in words:
            if word.startswith('@'):
                match = at_pattern.match(word)
                if match:
                    username = match.group(1)
                    if username.lower() not in ['here', 'youtube', 'channel', 'video']:
                        return f"https://instagram.com/{username}"
        
        return None
    
    def _extract_twitter(self, text):
        """Extract Twitter/X handle or URL"""
        match = self.TWITTER_PATTERN.search(text)
        if match:
            username = match.group(1)
            if username.lower() not in ['home', 'explore', 'notifications', 'messages']:
                return f"https://twitter.com/{username}"
        
        # Check for @username format
        at_pattern = re.compile(r'@([a-zA-Z0-9_]{3,15})', re.IGNORECASE)
        matches = at_pattern.findall(text)
        for username in matches:
            if username.lower() not in ['here', 'youtube', 'channel', 'everyone']:
                # Verify it's not an Instagram mention by checking context
                return f"https://twitter.com/{username}"
        
        return None
    
    def _extract_linkedin(self, text):
        """Extract LinkedIn URL"""
        match = self.LINKEDIN_PATTERN.search(text)
        if match:
            profile_id = match.group(1)
            return f"https://linkedin.com/in/{profile_id}"
        return None
    
    def _extract_website(self, text):
        """Extract personal website URL"""
        matches = self.WEBSITE_PATTERN.findall(text)
        
        # Common domains to exclude (social media platforms)
        excluded_domains = [
            'youtube.com', 'youtu.be', 'google.com', 'facebook.com',
            'instagram.com', 'twitter.com', 'x.com', 'linkedin.com',
            'tiktok.com', 'snapchat.com', 'pinterest.com', 'reddit.com'
        ]
        
        for match in matches:
            domain = match.lower()
            
            # Skip excluded domains
            if any(excluded in domain for excluded in excluded_domains):
                continue
            
            # Skip common placeholder domains
            if any(bl in domain for bl in self.EMAIL_BLACKLIST):
                continue
            
            # Reconstruct the full URL from the original text
            url_match = re.search(
                rf'https?://(?:www\.)?{re.escape(domain)}[^\s\)\]\"\'<>]*',
                text,
                re.IGNORECASE
            )
            
            if url_match:
                url = url_match.group(0)
                # Clean trailing punctuation
                url = url.rstrip('.,;:!?)\'\"')
                return url
        
        return None
    
    def extract_all_links(self, text):
        """Extract all URLs from text"""
        url_pattern = re.compile(
            r'https?://[^\s\)\]\"\'<>]+',
            re.IGNORECASE
        )
        
        matches = url_pattern.findall(text)
        
        # Clean and filter
        cleaned = []
        for url in matches:
            # Clean trailing punctuation
            url = url.rstrip('.,;:!?)\'\"')
            
            try:
                parsed = urlparse(url)
                if parsed.scheme and parsed.netloc:
                    cleaned.append(url)
            except Exception:
                continue
        
        return cleaned
