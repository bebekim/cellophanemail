"""Content analyzer using Anthropic API directly with caching optimization."""

import json
import os
import logging
from typing import Dict, Any
import anthropic
from ..services.analysis_cache import get_analysis_cache

logger = logging.getLogger(__name__)


class ContentAnalysisService:
    """AI-powered content analysis service using Anthropic Claude directly."""
    
    def __init__(self):
        """Initialize the content analyzer with Anthropic API and caching."""
        self._client = None
        self.model = "claude-3-5-sonnet-20241022"
        self._cache = get_analysis_cache()
    
    @property
    def client(self):
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            try:
                self._client = anthropic.Anthropic(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                raise Exception("LLM service unavailable")
        return self._client
    
    def analyze_content(self, content: str, sender: str = "", use_hybrid: bool = True) -> Dict:
        """
        Analyze content for abuse patterns using hybrid AI approach.
        
        Args:
            content: The text content to analyze
            sender: The sender identifier (email, username, etc.)
            use_hybrid: If True, use local analysis first, AI only for suspicious content
            
        Returns:
            Dict with keys: classification, confidence, abuse_score, reasoning, patterns
        """
        # Ensure content is never None
        if content is None:
            content = ""
        if sender is None:
            sender = ""
        
        if use_hybrid:
            # Step 0: Check cache first
            cached_result = self._cache.get_cached_analysis(content, sender)
            if cached_result:
                return cached_result
            
            # Step 1: Fast local analysis
            local_result = self._fallback_analysis(content)
            
            # Step 2: Only use expensive AI for suspicious content
            if local_result['classification'] in ['SAFE'] and len(local_result['horsemen_detected']) == 0:
                # Content appears safe, return local analysis to save AI costs
                local_result['reasoning'] = 'Local analysis - content appears safe'
                local_result['cost_optimization'] = 'hybrid_local_only'
                
                # Cache the safe result for future use
                self._cache.cache_analysis(content, sender, local_result)
                return local_result
            else:
                # Content is suspicious, use AI for detailed analysis
                try:
                    ai_result = self._call_ai_service(content, sender)
                    ai_result['cost_optimization'] = 'hybrid_ai_used'
                    
                    # Cache the AI result
                    self._cache.cache_analysis(content, sender, ai_result)
                    return ai_result
                except Exception as e:
                    logger.error(f"AI analysis failed for suspicious content: {str(e)}")
                    local_result['reasoning'] += ' (AI unavailable, using local analysis)'
                    local_result['cost_optimization'] = 'hybrid_fallback'
                    
                    # Cache the fallback result briefly
                    self._cache.cache_analysis(content, sender, local_result)
                    return local_result
        else:
            # Traditional approach - check cache then use AI
            cached_result = self._cache.get_cached_analysis(content, sender)
            if cached_result:
                cached_result['cost_optimization'] = 'traditional_cached'
                return cached_result
            
            try:
                result = self._call_ai_service(content, sender)
                result['cost_optimization'] = 'traditional_ai'
                self._cache.cache_analysis(content, sender, result)
                return result
            except Exception as e:
                logger.error(f"AI analysis failed: {str(e)}")
                fallback = self._fallback_analysis(content)
                fallback['cost_optimization'] = 'traditional_fallback'
                self._cache.cache_analysis(content, sender, fallback)
                return fallback
    
    def _call_ai_service(self, content: str, sender: str) -> Dict:
        """Make API call using Anthropic directly."""
        logger.info(f"🤖 [ContentAnalyzer] Preparing AI analysis")
        logger.info(f"🤖 [ContentAnalyzer] Content to analyze length: {len(content)}")
        logger.info(f"🤖 [ContentAnalyzer] Content preview: {content[:100] if content else 'EMPTY'}")
        logger.info(f"🤖 [ContentAnalyzer] Sender: {sender}")
        
        analysis_prompt = f"""You are an expert judge evaluating communication for emotional harm using the Four Horsemen framework.

The Four Horsemen of Toxic Communication (Gottman):

1. CRITICISM: Attacks on someone's character/personality rather than specific behavior
   - "You always..." "You never..." "You're so selfish/lazy/stupid"
   - Character assassination, global statements about personality flaws

2. CONTEMPT: Expressions of superiority, disrespect, disgust, or mockery
   - Sarcasm, eye-rolling language, name-calling, hostile humor
   - "You're pathetic" "I'm so much better than you" 
   - Most destructive - predictor of relationship failure

3. DEFENSIVENESS: Playing victim, counter-attacking, making excuses
   - "It's not my fault, you made me do it"
   - Deflecting responsibility, righteous indignation

4. STONEWALLING: Emotional withdrawal, shutting down communication
   - Silent treatment, "I'm done talking", refusing to engage
   - Passive-aggressive withdrawal

Judge the content and classify as:
- SAFE: No horsemen present, constructive communication
- WARNING: Mild presence of one horseman, not severely harmful
- HARMFUL: Clear presence of 1-2 horsemen, emotionally damaging
- ABUSIVE: Strong presence of multiple horsemen, especially contempt

Analyze this content:

From: {sender}
Content: {content}

Provide your judgment in valid JSON format:
{{
    "classification": "SAFE|WARNING|HARMFUL|ABUSIVE",
    "horsemen_detected": ["criticism", "contempt", "defensiveness", "stonewalling"],
    "reasoning": "Explain which horsemen are present and why",
    "specific_examples": ["direct quote from the content", "another quote without annotations"]
}}

IMPORTANT: 
- Respond ONLY with valid JSON
- In specific_examples array, include ONLY the quoted text, no explanations
- Ensure all quotes are properly escaped for JSON"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ]
            )
            
            # Extract content from response
            content_text = response.content[0].text
            logger.info(f"Raw AI response: {content_text}")
            
            # Parse JSON response from AI
            try:
                parsed_result = json.loads(content_text)
                return {
                    'classification': parsed_result.get('classification', 'SAFE'),
                    'horsemen_detected': parsed_result.get('horsemen_detected', []),
                    'reasoning': parsed_result.get('reasoning', ''),
                    'specific_examples': parsed_result.get('specific_examples', [])
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}. Raw content: {content_text}")
                # Try to extract key information from malformed JSON using regex
                import re
                
                classification_match = re.search(r'"classification":\s*"(SAFE|WARNING|HARMFUL|ABUSIVE)"', content_text)
                horsemen_match = re.findall(r'"(criticism|contempt|defensiveness|stonewalling)"', content_text)
                reasoning_match = re.search(r'"reasoning":\s*"([^"]+)"', content_text)
                
                # Use extracted values or conservative defaults
                classification = classification_match.group(1) if classification_match else 'HARMFUL'
                horsemen = list(set(horsemen_match)) if horsemen_match else []
                reasoning = reasoning_match.group(1) if reasoning_match else 'AI response contained toxic patterns but had formatting issues'
                
                logger.info(f"Recovered from malformed JSON - Classification: {classification}, Horsemen: {horsemen}")
                
                return {
                    'classification': classification,
                    'horsemen_detected': horsemen,
                    'reasoning': reasoning,
                    'specific_examples': []
                }
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during AI analysis: {e}")
            raise
    
    def _fallback_analysis(self, content: str) -> Dict:
        """Enhanced local Four Horsemen analysis for cost optimization."""
        content_lower = content.lower().strip()
        
        # First check for obviously safe patterns (newsletters, receipts, automated emails)
        safe_patterns = [
            'unsubscribe', 'newsletter', 'receipt', 'order confirmation', 'invoice',
            'thank you for', 'welcome to', 'password reset', 'verification code',
            'delivery notification', 'account statement', 'appointment reminder'
        ]
        
        business_domains = ['@amazon.', '@google.', '@microsoft.', '@apple.', '@paypal.', 
                           '@stripe.', '@github.', '@linkedin.', '@twitter.', '@facebook.']
        
        # Quick safe classification for business emails
        for pattern in safe_patterns:
            if pattern in content_lower:
                return {
                    'classification': 'SAFE',
                    'horsemen_detected': [],
                    'reasoning': f'Business/automated email pattern detected: {pattern}',
                    'specific_examples': []
                }
        
        # Enhanced Four Horsemen keyword patterns
        horsemen_patterns = {
            'criticism': [
                'you always', 'you never', 'you are so', 'stupid', 'selfish', 'lazy', 'worthless',
                'you can\'t', 'you won\'t', 'typical of you', 'you\'re such a', 'you\'re so',
                'what\'s wrong with you', 'you have no', 'you lack'
            ],
            'contempt': [
                'pathetic', 'disgusting', 'loser', 'idiot', 'better than you', 'superior',
                'moron', 'fool', 'imbecile', 'waste of space', 'piece of trash',
                'scum', 'lowlife', 'beneath me'
            ],
            'defensiveness': [
                'not my fault', 'you made me', 'i had to', 'you started',
                'you\'re the one', 'if you hadn\'t', 'you forced me',
                'i wouldn\'t have if', 'you\'re blaming me'
            ],
            'stonewalling': [
                'done talking', 'whatever', 'silent treatment', 'ignore you',
                'not discussing', 'end of conversation', 'i\'m done',
                'talk to the hand', 'blocked'
            ]
        }
        
        detected_horsemen = []
        specific_examples = []
        
        for horseman, keywords in horsemen_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    if horseman not in detected_horsemen:
                        detected_horsemen.append(horseman)
                    # Find actual text snippet for context
                    start_idx = content_lower.find(keyword)
                    if start_idx != -1:
                        end_idx = min(start_idx + len(keyword) + 20, len(content))
                        snippet = content[max(0, start_idx-10):end_idx]
                        specific_examples.append(snippet.strip())
        
        # Apply Four Horsemen-based classification logic
        # Multiple horsemen or contempt (most destructive) = ABUSIVE
        if len(detected_horsemen) >= 2 or 'contempt' in detected_horsemen:
            classification = 'ABUSIVE'
        # Single horseman detected = HARMFUL
        elif len(detected_horsemen) == 1:
            classification = 'HARMFUL'
        # Some concerning patterns but no clear horsemen = WARNING
        elif specific_examples:
            classification = 'WARNING'
        # No concerning patterns detected = SAFE
        else:
            classification = 'SAFE'
        
        return {
            'classification': classification,
            'horsemen_detected': detected_horsemen,
            'reasoning': f'Local Four Horsemen analysis - {len(detected_horsemen)} horsemen detected',
            'specific_examples': specific_examples[:3]  # Limit to first 3 examples
        }


# Backwards compatibility alias for EmailProcessor and other legacy code
# Maintains API compatibility while using the new ContentAnalysisService class
ContentAnalyzer = ContentAnalysisService