"""
Privacy-preserving local Llama analyzer for email toxicity detection.
Uses llama-cpp-python to run models locally without external API calls.
"""

import json
import gc
import logging
from typing import Dict, Optional, Any
from pathlib import Path
from llama_cpp import Llama
from .contracts import LLMAnalyzerInterface

logger = logging.getLogger(__name__)


class LlamaAnalyzer(LLMAnalyzerInterface):
    """Local Llama model analyzer for privacy-preserving email analysis."""
    
    def __init__(
        self, 
        model_path: Optional[str] = None,
        n_ctx: int = 4096,
        n_threads: int = 8,
        n_gpu_layers: int = 0,  # Set > 0 if you have GPU
        temperature: float = 0.1,
        verbose: bool = False
    ):
        """
        Initialize Llama analyzer with local model.
        
        Args:
            model_path: Path to GGUF model file. If None, will look for default.
            n_ctx: Context window size
            n_threads: Number of CPU threads to use
            n_gpu_layers: Number of layers to offload to GPU (0 for CPU only)
            temperature: Lower = more deterministic (0.1 recommended for analysis)
            verbose: Whether to show model loading output
        """
        if model_path is None:
            # Look for model in common locations
            possible_paths = [
                "./models/llama-3.1-8b-instruct.gguf",
                "./models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
                "~/models/llama-3.1-8b-instruct.gguf",
            ]
            for path in possible_paths:
                expanded = Path(path).expanduser()
                if expanded.exists():
                    model_path = str(expanded)
                    break
            
            if model_path is None:
                raise ValueError(
                    "No model file found. Please download Llama 3.1 8B GGUF model "
                    "and place it in ./models/ directory"
                )
        
        logger.info(f"Loading Llama model from {model_path}")
        
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            verbose=verbose,
            # Disable logging for privacy
            logits_all=False,
        )
        
        self.temperature = temperature
        
    def analyze_toxicity(self, email_content: str) -> Dict[str, Any]:
        """
        Analyze email for toxicity and manipulation patterns.
        
        Args:
            email_content: The email text to analyze
            
        Returns:
            Dictionary with toxicity analysis results
        """
        try:
            # Build prompt for Llama 3.1 format
            prompt = self._build_analysis_prompt(email_content)
            
            # Generate response with strict JSON output
            response = self.llm(
                prompt,
                max_tokens=200,
                temperature=self.temperature,
                stop=["}}", "\n\n"],
                echo=False  # Don't include prompt in response
            )
            
            # Extract text from response
            if isinstance(response, dict) and 'choices' in response:
                response_text = response['choices'][0]['text']
            else:
                response_text = str(response)
            
            # Parse JSON response
            result = self._parse_response(response_text)
            
            # Immediately clear sensitive data from memory
            del email_content
            del prompt
            del response
            del response_text
            gc.collect()  # Force garbage collection
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing email: {e}")
            # Return safe default on error
            return {
                "toxicity_score": 0.0,
                "manipulation": False,
                "gaslighting": False,
                "stonewalling": False,
                "defensive": False,
                "action": "SAFE",
                "error": str(e)
            }
    
    def _build_analysis_prompt(self, email_content: str) -> str:
        """Build the analysis prompt for Llama 3.1."""
        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an email safety analyzer. Analyze emails for toxicity and manipulation tactics.
Respond with valid JSON only. No explanations.<|eot_id|>

<|start_header_id|>user<|end_header_id|>
Analyze this email for toxicity and psychological manipulation.

EMAIL:
{email_content}

Respond with this exact JSON structure:
{{
  "toxicity_score": 0.0,
  "manipulation": false,
  "gaslighting": false,  
  "stonewalling": false,
  "defensive": false,
  "action": "SAFE"
}}

Where:
- toxicity_score: 0.0 (safe) to 1.0 (highly toxic)
- manipulation: true if manipulative language detected
- gaslighting: true if reality-denying tactics present
- stonewalling: true if avoiding/withdrawing behavior
- defensive: true if overly defensive language
- action: "SAFE" or "TOXIC"<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>
{{"""
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the model's JSON response."""
        try:
            # Clean up response text
            response_text = response_text.strip()
            
            # Find JSON object in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx + 1]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON object found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse response as JSON: {e}")
            # Return safe defaults
            return {
                "toxicity_score": 0.0,
                "manipulation": False,
                "gaslighting": False,
                "stonewalling": False,
                "defensive": False,
                "action": "SAFE",
                "parse_error": True
            }
    
    def analyze_fact_manner(
        self,
        fact_text: str,
        full_email_content: str,
        sender_email: str
    ) -> str:
        """
        Analyze how a fact is presented (positive/neutral/negative).
        Compatible with existing interface.
        """
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
Analyze how facts are presented in emails. Respond with one word only.<|eot_id|>

<|start_header_id|>user<|end_header_id|>
Email from {sender_email}:
{full_email_content}

How is this fact presented: "{fact_text}"
- POSITIVE: Constructive, helpful, supportive
- NEUTRAL: Plain statement without emotion  
- NEGATIVE: Destructive, attacking, manipulative

Respond with only: POSITIVE, NEUTRAL, or NEGATIVE<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>"""
        
        try:
            response = self.llm(
                prompt,
                max_tokens=10,
                temperature=0.1,
                echo=False
            )
            
            if isinstance(response, dict) and 'choices' in response:
                result = response['choices'][0]['text'].strip().upper()
            else:
                result = str(response).strip().upper()
            
            # Clean up memory
            del prompt
            del response
            gc.collect()
            
            # Validate response
            if result in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
                return result.lower()
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"Error in fact manner analysis: {e}")
            return "neutral"
    
    def __del__(self):
        """Clean up model from memory when analyzer is destroyed."""
        if hasattr(self, 'llm'):
            del self.llm
            gc.collect()


class SimpleLlamaAnalyzer:
    """
    Simplified interface compatible with existing SimpleLLMAnalyzer.
    Drop-in replacement for external API calls.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize with local Llama model."""
        self.analyzer = LlamaAnalyzer(model_path=model_path)
        self.client = self  # Compatibility with existing code
        self.model_name = "llama-3.1-8b-local"
    
    def messages_create(self, messages, **kwargs):
        """Compatible interface with existing code."""
        # Extract content from messages format
        if messages and isinstance(messages, list):
            content = messages[-1].get("content", "")
        else:
            content = str(messages)
        
        # Analyze for toxicity
        result = self.analyzer.analyze_toxicity(content)
        
        # Format response like Claude/OpenAI would
        return {
            "content": [
                {"text": json.dumps(result)}
            ]
        }
    
    @property
    def messages(self):
        """Compatibility property."""
        return self
    
    def create(self, **kwargs):
        """Compatibility method."""
        messages = kwargs.get("messages", [])
        return self.messages_create(messages, **kwargs)