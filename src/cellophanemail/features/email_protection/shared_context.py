"""
Shared context system for iterative email analysis.
Builds understanding across phases of content analysis.
"""

import re
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class FactAnalysis:
    """Analysis result for a single fact."""
    fact_text: str
    manner: str  # positive, neutral, negative
    confidence: float
    surrounding_context: str
    analysis_method: str  # llm, fallback, etc.


@dataclass
class PhaseResult:
    """Result from a single analysis phase."""
    phase: str
    iteration: int
    timestamp: datetime
    data: Dict[str, Any]


class SharedContext:
    """
    Iteratively updated context for email analysis.
    Acts like an i++ iterator, building understanding with each email.
    """
    
    def __init__(self, llm_analyzer=None):
        """
        Initialize shared context with optional LLM analyzer.
        
        Args:
            llm_analyzer: External LLM service for sophisticated analysis
        """
        # Core iteration tracking
        self.iteration = 0
        self.phase_results: List[PhaseResult] = []
        
        # Phase-specific data
        self.fact_ratios: List[float] = []
        self.fact_analyses: List[FactAnalysis] = []
        self.non_factual_patterns: List[Dict] = []
        self.implicit_messages: List[Dict] = []
        
        # LLM analyzer is injected, not embedded
        self.llm_analyzer = llm_analyzer
        
        # Current email state
        self.current_email_facts: List[str] = []
        self.current_email_content = ""
        self.current_sender = ""
        
    def set_llm_analyzer(self, llm_analyzer):
        """Set or update the LLM analyzer after initialization."""
        self.llm_analyzer = llm_analyzer
        
    def start_new_email(self, email_content: str, sender: str):
        """Begin analysis of a new email."""
        self.iteration += 1
        self.current_email_content = email_content
        self.current_sender = sender
        self.current_email_facts = []
        
    def update_phase1_facts(self):
        """
        Phase 1: Extract facts and analyze their presentation manner.
        Updates fact_ratios and fact_analyses.
        """
        # Extract facts from email content
        facts = self._extract_facts(self.current_email_content)
        self.current_email_facts = facts
        
        # Calculate fact ratio
        total_words = len(self.current_email_content.split())
        fact_words = sum(len(fact.split()) for fact in facts)
        fact_ratio = fact_words / total_words if total_words > 0 else 0.0
        self.fact_ratios.append(fact_ratio)
        
        # Analyze each fact's manner
        fact_analyses = []
        for fact in facts:
            analysis = self._analyze_fact_manner(fact)
            fact_analyses.append(analysis)
            self.fact_analyses.append(analysis)
        
        # Store phase result
        phase_result = PhaseResult(
            phase="fact_extraction",
            iteration=self.iteration,
            timestamp=datetime.now(),
            data={
                "fact_ratio": fact_ratio,
                "total_facts": len(facts),
                "facts": facts,
                "fact_analyses": [
                    {"fact": fa.fact_text, "manner": fa.manner, "confidence": fa.confidence}
                    for fa in fact_analyses
                ]
            }
        )
        self.phase_results.append(phase_result)
        
        return phase_result
        
    def update_phase2_manner_summary(self):
        """
        Phase 2: Enhanced manner analysis using LLM for context-aware evaluation.
        Analyzes how facts are presented and provides detailed reasoning.
        """
        # Get facts from current iteration
        current_iteration_start = len(self.fact_analyses) - len(self.current_email_facts)
        current_facts = self.fact_analyses[current_iteration_start:]
        
        if not current_facts:
            return None
        
        # Enhanced analysis with LLM if available
        if self.llm_analyzer and len(current_facts) > 0:
            overall_analysis = self._llm_analyze_overall_manner(current_facts)
        else:
            overall_analysis = self._simple_manner_summary(current_facts)
            
        phase_result = PhaseResult(
            phase="manner_summary",
            iteration=self.iteration,
            timestamp=datetime.now(),
            data=overall_analysis
        )
        self.phase_results.append(phase_result)
        
        return phase_result
    
    def _llm_analyze_overall_manner(self, fact_analyses: List[FactAnalysis]) -> Dict[str, Any]:
        """Use LLM to analyze overall manner with cultural and linguistic context."""
        
        # Prepare facts and context for LLM analysis
        facts_with_context = []
        for fa in fact_analyses:
            facts_with_context.append({
                "fact": fa.fact_text,
                "individual_manner": fa.manner,
                "context": fa.surrounding_context
            })
        
        prompt = f"""
        Analyze the overall manner in which factual information is presented in this email.
        
        EMAIL CONTENT:
        {self.current_email_content}
        
        INDIVIDUAL FACTS AND THEIR CONTEXTS:
        {chr(10).join([f"FACT: {f['fact']} | CONTEXT: {f['context'][:100]}..." for f in facts_with_context])}
        
        Consider:
        1. How are facts woven into the overall message?
        2. What is the emotional tone surrounding factual statements?
        3. Are facts used to support, attack, manipulate, or inform?
        4. What cultural/linguistic patterns affect interpretation?
        5. Is there escalation or de-escalation in tone?
        
        Analyze the OVERALL MANNER across all facts:
        - PREDOMINANTLY_POSITIVE: Facts presented constructively, supportively
        - PREDOMINANTLY_NEGATIVE: Facts used aggressively, manipulatively  
        - MIXED: Some positive, some negative presentation
        - NEUTRAL: Plain factual presentation
        
        Respond in this JSON format:
        {{
            "overall_manner": "PREDOMINANTLY_POSITIVE|PREDOMINANTLY_NEGATIVE|MIXED|NEUTRAL",
            "reasoning": "Brief explanation of why you classified it this way",
            "cultural_context": "Any cultural/linguistic factors that influenced your analysis",
            "manipulation_detected": true/false,
            "emotional_loading": "high|medium|low"
        }}
        """
        
        try:
            if hasattr(self.llm_analyzer, 'provider'):
                if self.llm_analyzer.provider == "anthropic":
                    response = self.llm_analyzer.client.messages.create(
                        model=self.llm_analyzer.model_name,
                        max_tokens=300,
                        temperature=0.1,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    result = response.content[0].text.strip()
                    
                elif self.llm_analyzer.provider == "openai":
                    response = self.llm_analyzer.client.chat.completions.create(
                        model=self.llm_analyzer.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=300,
                        temperature=0.1
                    )
                    result = response.choices[0].message.content.strip()
                else:
                    raise ValueError(f"Unsupported provider: {self.llm_analyzer.provider}")
            else:
                # Mock LLM response for testing
                result = """{
                    "overall_manner": "PREDOMINANTLY_NEGATIVE",
                    "reasoning": "Facts are presented in accusatory context with emotional pressure",
                    "cultural_context": "Direct confrontational style typical in debt collection",
                    "manipulation_detected": true,
                    "emotional_loading": "high"
                }"""
            
            # Parse JSON response
            import json
            llm_analysis = json.loads(result)
            
            # Count individual manner classifications for compatibility
            manner_counts = {"positive": 0, "neutral": 0, "negative": 0}
            for fa in fact_analyses:
                manner_counts[fa.manner] += 1
                
            total_facts = len(fact_analyses)
            
            return {
                "overall_manner": llm_analysis.get("overall_manner", "MIXED").lower(),
                "llm_reasoning": llm_analysis.get("reasoning", ""),
                "cultural_context": llm_analysis.get("cultural_context", ""),
                "manipulation_detected": llm_analysis.get("manipulation_detected", False),
                "emotional_loading": llm_analysis.get("emotional_loading", "medium"),
                "manner_distribution": manner_counts,
                "negative_ratio": manner_counts["negative"] / total_facts,
                "positive_ratio": manner_counts["positive"] / total_facts,
                "total_facts_analyzed": total_facts,
                "analysis_method": "llm_enhanced"
            }
            
        except Exception as e:
            # Fallback to simple analysis if LLM fails
            return self._simple_manner_summary(fact_analyses, error=str(e))
    
    def _simple_manner_summary(self, fact_analyses: List[FactAnalysis], error: str = None) -> Dict[str, Any]:
        """Simple fallback manner summary when LLM unavailable."""
        
        # Count manner types
        manner_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for fact_analysis in fact_analyses:
            manner_counts[fact_analysis.manner] += 1
            
        # Determine overall manner
        total_facts = len(fact_analyses)
        negative_ratio = manner_counts["negative"] / total_facts
        positive_ratio = manner_counts["positive"] / total_facts
        
        if negative_ratio > 0.6:
            overall_manner = "predominantly_negative"
        elif positive_ratio > 0.6:
            overall_manner = "predominantly_positive"
        else:
            overall_manner = "mixed_or_neutral"
        
        result = {
            "overall_manner": overall_manner,
            "manner_distribution": manner_counts,
            "negative_ratio": negative_ratio,
            "positive_ratio": positive_ratio,
            "total_facts_analyzed": total_facts,
            "analysis_method": "simple_fallback"
        }
        
        if error:
            result["fallback_reason"] = f"LLM analysis failed: {error}"
            
        return result
        
    def update_phase3_non_factual(self):
        """
        Phase 3: Analyze non-factual content.
        What remains after facts are removed - personal attacks, emotions, etc.
        """
        # Remove facts from content to get residual
        residual_content = self.current_email_content
        for fact in self.current_email_facts:
            residual_content = residual_content.replace(fact, "[FACT_REMOVED]")
            
        # Analyze residual content
        residual_analysis = self._analyze_residual_content(residual_content)
        self.non_factual_patterns.append(residual_analysis)
        
        phase_result = PhaseResult(
            phase="non_factual_analysis",
            iteration=self.iteration,
            timestamp=datetime.now(),
            data={
                "residual_content": residual_content,
                "residual_word_count": len(residual_content.split()),
                "personal_attack_indicators": residual_analysis.get("personal_attacks", []),
                "emotional_indicators": residual_analysis.get("emotional_words", []),
                "manipulation_indicators": residual_analysis.get("manipulation_patterns", [])
            }
        )
        self.phase_results.append(phase_result)
        
        return phase_result
        
    def update_phase4_implicit(self):
        """
        Phase 4: Identify implicit/unspoken messages.
        What is implied but not directly stated.
        """
        implicit_analysis = self._analyze_implicit_messages()
        self.implicit_messages.append(implicit_analysis)
        
        phase_result = PhaseResult(
            phase="implicit_analysis", 
            iteration=self.iteration,
            timestamp=datetime.now(),
            data={
                "implicit_threats": implicit_analysis.get("threats", []),
                "power_dynamics": implicit_analysis.get("power_plays", []),
                "emotional_manipulation": implicit_analysis.get("emotional_hooks", []),
                "social_pressure": implicit_analysis.get("social_weapons", [])
            }
        )
        self.phase_results.append(phase_result)
        
        return phase_result
        
    def get_current_analysis_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of current email analysis."""
        current_phases = [pr for pr in self.phase_results 
                         if pr.iteration == self.iteration]
        
        summary = {
            "iteration": self.iteration,
            "sender": self.current_sender,
            "total_phases_completed": len(current_phases),
            "fact_ratio": self.fact_ratios[-1] if self.fact_ratios else 0.0,
            "phases": {phase.phase: phase.data for phase in current_phases}
        }
        
        # Add historical context
        if self.iteration > 1:
            summary["historical_context"] = {
                "previous_iterations": self.iteration - 1,
                "avg_fact_ratio": sum(self.fact_ratios) / len(self.fact_ratios),
                "escalation_detected": self._detect_escalation_pattern()
            }
            
        return summary
        
    def _extract_facts(self, content: str) -> List[str]:
        """
        Extract facts using LLM for language-agnostic detection.
        Falls back to simple regex if LLM unavailable.
        """
        if self.llm_analyzer:
            try:
                return self._llm_extract_facts(content)
            except Exception as e:
                logger.warning(f"LLM fact extraction failed: {e}. Using fallback.")
                return self._regex_extract_facts(content)
        else:
            return self._regex_extract_facts(content)
    
    def _llm_extract_facts(self, content: str) -> List[str]:
        """Use LLM to extract factual statements from email content."""
        
        # Create extraction prompt
        prompt = f"""
        Extract factual statements from this email content. A factual statement is something that can be verified as true or false, such as:
        - Monetary amounts ($500, 100 dollars, fifty euros)
        - Dates and times (last month, January 15, 2024, next Friday)
        - Quantities (3 times, 5 people, 2 hours)
        - Specific events (meeting at cafe, called yesterday)
        - Locations (downtown office, 123 Main St)
        - Names of people, places, or things
        
        EMAIL CONTENT:
        {content}
        
        Extract each factual statement as a separate line. Include the exact text from the email.
        Do not include:
        - Opinions ("you're selfish")
        - Emotions ("I'm angry")
        - Generalizations ("you always")
        - Threats ("or else")
        
        Output format:
        FACT: [exact text from email]
        FACT: [exact text from email]
        
        If no facts found, respond with: NO_FACTS_FOUND
        """
        
        # Use LLM for language-agnostic fact extraction
        from .llm_analyzer import analyze_fact_manner_with_llm
        
        if hasattr(self.llm_analyzer, 'provider'):
            # Real LLM providers
            try:
                if self.llm_analyzer.provider == "anthropic":
                    response = self.llm_analyzer.client.messages.create(
                        model=self.llm_analyzer.model_name,
                        max_tokens=500,
                        temperature=0.1,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    result = response.content[0].text.strip()
                
                elif self.llm_analyzer.provider == "openai":
                    response = self.llm_analyzer.client.chat.completions.create(
                        model=self.llm_analyzer.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=500,
                        temperature=0.1
                    )
                    result = response.choices[0].message.content.strip()
                else:
                    raise ValueError(f"Unsupported provider: {self.llm_analyzer.provider}")
                    
            except Exception as e:
                logger.error(f"LLM fact extraction failed: {e}")
                raise
        
        else:
            # Mock analyzer - simulate LLM response for testing
            result = f"""
            FACT: $500
            FACT: last year
            FACT: 3 months ago
            """
        
        # Parse LLM response
        facts = []
        if result and result != "NO_FACTS_FOUND":
            lines = result.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('FACT:'):
                    fact = line.replace('FACT:', '').strip()
                    if fact and len(fact) > 0:
                        facts.append(fact)
        
        # logger.debug(f"LLM extracted {len(facts)} facts from content")
        return facts
    
    def _regex_extract_facts(self, content: str) -> List[str]:
        """Fallback regex-based fact extraction (English-specific)."""
        facts = []
        
        # Money amounts
        money_pattern = r'\$[\d,]+\.?\d*|[\d,]+\.?\d*\s*(?:dollars?|euros?|pounds?|won|yen)'
        facts.extend(re.findall(money_pattern, content, re.IGNORECASE))
        
        # Dates
        date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        facts.extend(re.findall(date_pattern, content, re.IGNORECASE))
        
        # Time references
        time_pattern = r'\b(?:last|next)\s+(?:week|month|year|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b'
        facts.extend(re.findall(time_pattern, content, re.IGNORECASE))
        
        # Numbers with context
        number_pattern = r'\b\d+\s+(?:times|hours|days|weeks|months|years|people|dollars)\b'
        facts.extend(re.findall(number_pattern, content, re.IGNORECASE))
        
        # Korean money patterns (example for multilingual support)
        korean_money = r'\d+(?:만원|원|달러)'
        facts.extend(re.findall(korean_money, content))
        
        # logger.debug(f"Regex extracted {len(facts)} facts from content")
        return facts
        
    def _analyze_fact_manner(self, fact: str) -> FactAnalysis:
        """Analyze how a fact is presented using LLM or fallback."""
        if self.llm_analyzer:
            try:
                manner = self.llm_analyzer.analyze_fact_manner(
                    fact, self.current_email_content, self.current_sender
                )
                confidence = 0.8  # LLM analysis confidence
                method = f"llm_iter_{self.iteration}"
            except Exception as e:
                # Fallback if LLM fails
                manner, confidence = self._simple_manner_fallback(fact)
                method = f"fallback_iter_{self.iteration}"
        else:
            manner, confidence = self._simple_manner_fallback(fact)
            method = f"simple_iter_{self.iteration}"
            
        return FactAnalysis(
            fact_text=fact,
            manner=manner,
            confidence=confidence,
            surrounding_context=self._get_surrounding_context(fact),
            analysis_method=method
        )
        
    def _simple_manner_fallback(self, fact: str) -> tuple[str, float]:
        """Simple fallback manner analysis."""
        context = self._get_surrounding_context(fact).lower()
        
        negative_indicators = ["still", "never", "always", "supposed to", "should have", "owe"]
        positive_indicators = ["thank", "appreciate", "helpful", "working on", "together"]
        
        if any(indicator in context for indicator in negative_indicators):
            return "negative", 0.6
        elif any(indicator in context for indicator in positive_indicators):
            return "positive", 0.6
        else:
            return "neutral", 0.7
            
    def _get_surrounding_context(self, fact: str, window=20) -> str:
        """Get words around a fact for context analysis."""
        content_words = self.current_email_content.split()
        fact_words = fact.split()
        
        # Find fact position
        for i in range(len(content_words) - len(fact_words) + 1):
            if content_words[i:i+len(fact_words)] == fact_words:
                start = max(0, i - window)
                end = min(len(content_words), i + len(fact_words) + window)
                return " ".join(content_words[start:end])
                
        return fact  # Fallback if not found
        
    def _analyze_residual_content(self, residual: str) -> Dict[str, List[str]]:
        """Analyze non-factual content patterns."""
        analysis = {
            "personal_attacks": [],
            "emotional_words": [],
            "manipulation_patterns": []
        }
        
        # Simple pattern detection - can be enhanced
        words = residual.lower().split()
        
        attack_words = ["stupid", "selfish", "lazy", "worthless", "terrible", "awful"]
        emotional_words = ["hate", "love", "angry", "sad", "disappointed", "hurt"]
        manipulation_words = ["everyone", "always", "never", "should", "supposed to"]
        
        analysis["personal_attacks"] = [word for word in words if word in attack_words]
        analysis["emotional_words"] = [word for word in words if word in emotional_words]  
        analysis["manipulation_patterns"] = [word for word in words if word in manipulation_words]
        
        return analysis
        
    def _analyze_implicit_messages(self) -> Dict[str, List[str]]:
        """Analyze implicit/unspoken communication."""
        # This would benefit from LLM analysis
        # For now, simple pattern detection
        
        implicit = {
            "threats": [],
            "power_plays": [],
            "emotional_hooks": [],
            "social_weapons": []
        }
        
        content_lower = self.current_email_content.lower()
        
        # Threat patterns
        if any(phrase in content_lower for phrase in ["or else", "if you don't", "you'll regret"]):
            implicit["threats"].append("conditional_threat")
            
        # Social pressure patterns  
        if any(phrase in content_lower for phrase in ["everyone knows", "people are saying", "others think"]):
            implicit["social_weapons"].append("false_consensus")
            
        return implicit
        
    def _detect_escalation_pattern(self) -> bool:
        """Detect if communication is escalating over iterations."""
        if len(self.fact_ratios) < 2:
            return False
            
        # Simple escalation detection - decreasing fact ratios over time
        recent_ratios = self.fact_ratios[-3:]
        return len(recent_ratios) >= 2 and recent_ratios[-1] < recent_ratios[0]