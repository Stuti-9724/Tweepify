import os
import json
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "default_key"))
    
    def generate_tweet_content(self, keywords: str = "", hashtags: str = "", 
                             target_audience: str = "", trending_hashtags: Optional[List[str]] = None) -> str:
        """Generate AI-powered tweet content based on campaign parameters"""
        try:
            # Prepare context
            context_parts = []
            if keywords:
                context_parts.append(f"Keywords: {keywords}")
            if hashtags:
                context_parts.append(f"Campaign hashtags: {hashtags}")
            if target_audience:
                context_parts.append(f"Target audience: {target_audience}")
            if trending_hashtags:
                context_parts.append(f"Trending hashtags: {', '.join(trending_hashtags[:5])}")
            
            context = "\n".join(context_parts) if context_parts else "General social media content"
            
            prompt = f"""Create an engaging tweet (max 280 characters) based on the following context:
            
{context}

Requirements:
- Keep it under 280 characters
- Make it engaging and authentic
- Include relevant hashtags naturally
- Avoid spam-like language
- Make it suitable for social media engagement
- Focus on value or entertainment for the audience

Generate only the tweet content, no additional text or quotes."""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            content = response.text.strip() if response.text else ""
            
            # Ensure content is within Twitter's character limit
            if len(content) > 280:
                content = content[:277] + "..."
            
            return content
            
        except Exception as e:
            logging.error(f"AI content generation error: {e}")
            raise Exception(f"Failed to generate content: {str(e)}")
    
    def check_spam_content(self, content: str) -> bool:
        """Check if content appears to be spam using AI analysis"""
        try:
            prompt = f"""Analyze the following tweet content for spam characteristics:

Content: "{content}"

Check for:
- Excessive promotional language
- Repetitive text patterns
- Suspicious links or mentions
- Overly aggressive sales language
- Bot-like behavior patterns

Respond with JSON format:
{{"is_spam": boolean, "confidence": float, "reasons": ["reason1", "reason2"]}}"""

            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            
            if response.text:
                result = json.loads(response.text)
                return result.get('is_spam', False)
            
            return False
            
        except Exception as e:
            logging.error(f"Spam check error: {e}")
            # Conservative approach: if we can't check, assume it's not spam
            return False
    
    def generate_campaign_suggestions(self, industry: str = "", goals: str = "") -> List[Dict[str, Any]]:
        """Generate campaign suggestions based on industry and goals"""
        try:
            prompt = f"""Generate 3 social media campaign ideas for:
Industry: {industry or "General business"}
Goals: {goals or "Increase engagement and brand awareness"}

For each campaign, provide:
- Campaign name
- Description (2-3 sentences)
- Suggested keywords (5-7 keywords)
- Recommended hashtags (3-5 hashtags)
- Target audience description
- Expected tweet frequency per day

Respond in JSON format:
{{
  "campaigns": [
    {{
      "name": "Campaign Name",
      "description": "Campaign description",
      "keywords": ["keyword1", "keyword2"],
      "hashtags": ["#hashtag1", "#hashtag2"],
      "target_audience": "Audience description",
      "tweet_frequency": 2
    }}
  ]
}}"""

            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            
            if response.text:
                result = json.loads(response.text)
                return result.get('campaigns', [])
            
            return []
            
        except Exception as e:
            logging.error(f"Campaign suggestions error: {e}")
            return []
    
    def analyze_content_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment of tweet content"""
        try:
            prompt = f"""Analyze the sentiment of this tweet content:

Content: "{content}"

Provide analysis including:
- Overall sentiment (positive, negative, neutral)
- Emotion detected (joy, anger, sadness, fear, surprise, etc.)
- Confidence score (0-1)
- Engagement potential (low, medium, high)

Respond in JSON format:
{{
  "sentiment": "positive/negative/neutral",
  "emotion": "detected emotion",
  "confidence": 0.85,
  "engagement_potential": "high/medium/low",
  "summary": "Brief analysis summary"
}}"""

            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            
            if response.text:
                return json.loads(response.text)
            
            return {"sentiment": "neutral", "confidence": 0.5, "engagement_potential": "medium"}
            
        except Exception as e:
            logging.error(f"Sentiment analysis error: {e}")
            return {"sentiment": "neutral", "confidence": 0.5, "engagement_potential": "medium"}
