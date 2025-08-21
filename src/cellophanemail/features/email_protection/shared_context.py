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
                raise ValueError("No LLM analyzer available. Real LLM required for language-agnostic analysis.")
            
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
        Phase 3: Enhanced hybrid analysis of non-factual content.
        Uses LLM + pattern matching for sophisticated psychological analysis.
        """
        # Remove facts from content to get residual
        residual_content = self.current_email_content
        for fact in self.current_email_facts:
            residual_content = residual_content.replace(fact, "[FACT_REMOVED]")
        
        # Hybrid analysis approach
        if self.llm_analyzer and len(residual_content.strip()) > 10:
            hybrid_analysis = self._hybrid_analyze_residual_content(residual_content)
        else:
            hybrid_analysis = self._pattern_analyze_residual_content(residual_content)
        
        self.non_factual_patterns.append(hybrid_analysis)
        
        phase_result = PhaseResult(
            phase="non_factual_analysis",
            iteration=self.iteration,
            timestamp=datetime.now(),
            data=hybrid_analysis
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
                "social_pressure": implicit_analysis.get("social_weapons", []),
                "analysis_method": implicit_analysis.get("analysis_method", "unknown"),
                "confidence": implicit_analysis.get("confidence", 0.0),
                "reasoning": implicit_analysis.get("reasoning", ""),
                "fallback_reason": implicit_analysis.get("fallback_reason", "")
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
                # logger.warning(f"LLM fact extraction failed: {e}. Using fallback.")
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
                # logger.error(f"LLM fact extraction failed: {e}")
                raise
        
        else:
            raise ValueError("No LLM analyzer available. Real LLM required for language-agnostic fact extraction.")
        
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
        
    def _hybrid_analyze_residual_content(self, residual: str) -> Dict[str, Any]:
        """
        Hybrid approach: LLM analysis enhanced with pattern validation.
        Provides sophisticated psychological analysis with cultural context.
        """
        try:
            # Primary LLM analysis
            llm_analysis = self._llm_analyze_residual_content(residual)
            
            # Pattern analysis for cross-validation
            pattern_analysis = self._pattern_analyze_residual_content(residual)
            
            # Hybrid scoring and validation
            hybrid_result = self._validate_and_merge_analysis(llm_analysis, pattern_analysis, residual)
            
            hybrid_result["analysis_method"] = "hybrid_llm_pattern"
            return hybrid_result
            
        except Exception as e:
            # Fallback to pattern analysis
            fallback_result = self._pattern_analyze_residual_content(residual)
            fallback_result["analysis_method"] = "pattern_fallback"
            fallback_result["llm_fallback_reason"] = str(e)
            return fallback_result
    
    def _llm_analyze_residual_content(self, residual: str) -> Dict[str, Any]:
        """Use LLM for sophisticated psychological analysis of non-factual content."""
        
        prompt = f"""
        Analyze the non-factual content in this email for psychological manipulation patterns.
        
        RESIDUAL CONTENT (after facts removed):
        {residual}
        
        ORIGINAL EMAIL CONTEXT:
        {self.current_email_content}
        
        Analyze for these psychological patterns:
        
        1. PERSONAL ATTACKS:
        - Character assassination
        - Identity attacks  
        - Capability/competence attacks
        - Appearance/physical attacks
        
        2. EMOTIONAL MANIPULATION:
        - Guilt induction
        - Shame tactics
        - Fear mongering
        - Emotional blackmail
        
        3. GASLIGHTING PATTERNS:
        - Reality distortion
        - Memory questioning  
        - Self-doubt induction
        - Sanity questioning
        
        4. SOCIAL MANIPULATION:
        - Isolation tactics
        - Reputation threats
        - False consensus ("everyone thinks")
        - Authority claims
        
        5. CONTROL TACTICS:
        - Ultimatums
        - Conditional threats
        - Punishment threats
        - Withdrawal threats
        
        Consider cultural context - different cultures express aggression differently.
        
        Respond in JSON format:
        {{
            "personal_attacks": ["specific attacks found"],
            "emotional_manipulation": ["guilt/shame/fear tactics"],
            "gaslighting_patterns": ["reality distortion examples"],
            "social_manipulation": ["isolation/reputation threats"],
            "control_tactics": ["ultimatums/threats"],
            "cultural_context": "cultural interpretation notes",
            "severity_score": 0.0-1.0,
            "manipulation_sophistication": "low|medium|high",
            "primary_tactic": "main manipulation strategy detected",
            "confidence": 0.0-1.0
        }}
        """
        
        if hasattr(self.llm_analyzer, 'provider'):
            # Real LLM providers
            if self.llm_analyzer.provider == "anthropic":
                response = self.llm_analyzer.client.messages.create(
                    model=self.llm_analyzer.model_name,
                    max_tokens=400,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text.strip()
                
            elif self.llm_analyzer.provider == "openai":
                response = self.llm_analyzer.client.chat.completions.create(
                    model=self.llm_analyzer.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400,
                    temperature=0.1
                )
                result = response.choices[0].message.content.strip()
            else:
                raise ValueError(f"Unsupported provider: {self.llm_analyzer.provider}")
        else:
            raise ValueError("No LLM analyzer available. Real LLM required for language-agnostic psychological analysis.")
        
        import json
        return json.loads(result)
    
    def _pattern_analyze_residual_content(self, residual: str) -> Dict[str, Any]:
        """Enhanced pattern analysis with multilingual support."""
        analysis = {
            "personal_attacks": [],
            "emotional_manipulation": [],
            "gaslighting_patterns": [],
            "social_manipulation": [],
            "control_tactics": [],
            "cultural_context": "",
            "severity_score": 0.0,
            "manipulation_sophistication": "low",
            "primary_tactic": "none",
            "confidence": 0.7,
            "analysis_method": "enhanced_patterns"
        }
        
        residual_lower = residual.lower()
        words = residual_lower.split()
        
        # Enhanced multilingual patterns
        patterns = {
            "personal_attacks": {
                "english": ["stupid", "idiot", "selfish", "lazy", "worthless", "terrible", "awful", "loser", "pathetic"],
                "korean": ["바보", "멍청이", "한심", "쓸모없", "형편없"],
                "spanish": ["estúpido", "idiota", "inútil", "patético", "terrible"],
                "universal": ["🤬", "💩"]  # Emojis are universal
            },
            "emotional_manipulation": {
                "english": ["disappointed", "hurt", "betrayed", "expected better", "thought you were"],
                "korean": ["실망", "상처", "배신", "기대했는데"],
                "spanish": ["decepcionado", "herido", "traicionado"],
                "patterns": ["if you loved", "after everything", "how could you"]
            },
            "gaslighting": {
                "english": ["you're imagining", "that never happened", "you're being dramatic", "you're too sensitive"],
                "patterns": ["you always", "you never", "that's not what happened"]
            },
            "social_manipulation": {
                "english": ["everyone knows", "people are talking", "others think", "everyone thinks"],
                "korean": ["모든 사람이", "다들 알고", "사람들이 말하길"],
                "patterns": ["tell everyone", "reputation", "embarrass you"]
            },
            "control_tactics": {
                "english": ["or else", "you'll regret", "last chance", "final warning"],
                "patterns": ["if you don't", "unless you", "you have to", "no choice"]
            }
        }
        
        severity_points = 0
        
        # Pattern matching with scoring
        for category, lang_patterns in patterns.items():
            found_items = []
            
            for lang, terms in lang_patterns.items():
                if lang == "patterns":
                    continue
                    
                for term in terms:
                    if term in residual_lower:
                        found_items.append(term)
                        severity_points += 2 if lang == "english" else 3  # Non-English gets higher score
            
            # Pattern matching for complex phrases
            if "patterns" in lang_patterns:
                for pattern in lang_patterns["patterns"]:
                    if pattern in residual_lower:
                        found_items.append(pattern)
                        severity_points += 3
            
            analysis[category] = found_items
        
        # Calculate severity and sophistication
        analysis["severity_score"] = min(1.0, severity_points / 20)
        
        if severity_points > 15:
            analysis["manipulation_sophistication"] = "high"
        elif severity_points > 8:
            analysis["manipulation_sophistication"] = "medium"
        else:
            analysis["manipulation_sophistication"] = "low"
        
        # Determine primary tactic
        max_category = max(patterns.keys(), key=lambda k: len(analysis[k]))
        if analysis[max_category]:
            analysis["primary_tactic"] = max_category
        
        # Cultural context hints
        korean_detected = any(term in residual_lower for term in patterns["personal_attacks"]["korean"] + patterns["emotional_manipulation"]["korean"] + patterns["social_manipulation"]["korean"])
        spanish_detected = any(term in residual_lower for term in patterns["personal_attacks"]["spanish"] + patterns["emotional_manipulation"]["spanish"])
        
        if korean_detected:
            analysis["cultural_context"] = "Korean language patterns detected - indirect confrontation style"
        elif spanish_detected:
            analysis["cultural_context"] = "Spanish language patterns detected - emotional emphasis style"
        else:
            analysis["cultural_context"] = "Western direct confrontation patterns"
        
        return analysis
    
    def _validate_and_merge_analysis(self, llm_result: Dict, pattern_result: Dict, residual: str) -> Dict[str, Any]:
        """Cross-validate LLM and pattern analysis, merge results."""
        
        merged = {
            "personal_attacks": list(set(llm_result.get("personal_attacks", []) + pattern_result.get("personal_attacks", []))),
            "emotional_manipulation": list(set(llm_result.get("emotional_manipulation", []) + pattern_result.get("emotional_manipulation", []))),
            "gaslighting_patterns": llm_result.get("gaslighting_patterns", []),
            "social_manipulation": llm_result.get("social_manipulation", []),
            "control_tactics": llm_result.get("control_tactics", []),
            "cultural_context": llm_result.get("cultural_context", pattern_result.get("cultural_context", "")),
            "primary_tactic": llm_result.get("primary_tactic", pattern_result.get("primary_tactic")),
            "manipulation_sophistication": llm_result.get("manipulation_sophistication", pattern_result.get("manipulation_sophistication")),
            "residual_content": residual,
            "residual_word_count": len(residual.split()),
            
            # Hybrid scoring (weighted average)
            "severity_score": (llm_result.get("severity_score", 0) * 0.7 + pattern_result.get("severity_score", 0) * 0.3),
            "confidence": (llm_result.get("confidence", 0) * 0.8 + pattern_result.get("confidence", 0) * 0.2),
            
            # Cross-validation metrics
            "llm_pattern_agreement": self._calculate_agreement(llm_result, pattern_result),
            "validation_flags": self._generate_validation_flags(llm_result, pattern_result)
        }
        
        return merged
    
    def _calculate_agreement(self, llm_result: Dict, pattern_result: Dict) -> float:
        """Calculate agreement score between LLM and pattern analysis."""
        agreements = 0
        total_checks = 0
        
        # Compare severity scores
        llm_severity = llm_result.get("severity_score", 0)
        pattern_severity = pattern_result.get("severity_score", 0)
        severity_agreement = 1.0 - abs(llm_severity - pattern_severity)
        agreements += severity_agreement
        total_checks += 1
        
        # Compare primary tactics
        if llm_result.get("primary_tactic") == pattern_result.get("primary_tactic"):
            agreements += 1
        total_checks += 1
        
        # Compare attack detection overlap
        llm_attacks = set(llm_result.get("personal_attacks", []))
        pattern_attacks = set(pattern_result.get("personal_attacks", []))
        if llm_attacks or pattern_attacks:
            overlap = len(llm_attacks & pattern_attacks)
            total_unique = len(llm_attacks | pattern_attacks)
            attack_agreement = overlap / total_unique if total_unique > 0 else 1.0
            agreements += attack_agreement
            total_checks += 1
        
        return agreements / total_checks if total_checks > 0 else 1.0
    
    def _generate_validation_flags(self, llm_result: Dict, pattern_result: Dict) -> List[str]:
        """Generate flags for validation discrepancies."""
        flags = []
        
        # Severity mismatch
        llm_severity = llm_result.get("severity_score", 0)
        pattern_severity = pattern_result.get("severity_score", 0)
        if abs(llm_severity - pattern_severity) > 0.3:
            flags.append("severity_mismatch")
        
        # Primary tactic disagreement
        if llm_result.get("primary_tactic") != pattern_result.get("primary_tactic"):
            flags.append("tactic_disagreement")
        
        # High confidence with low agreement
        agreement = self._calculate_agreement(llm_result, pattern_result)
        if llm_result.get("confidence", 0) > 0.8 and agreement < 0.6:
            flags.append("high_confidence_low_agreement")
        
        return flags
        
    def _analyze_implicit_messages(self) -> Dict[str, List[str]]:
        """Analyze implicit/unspoken communication using LLM when available."""
        
        if self.llm_analyzer:
            try:
                return self._llm_analyze_implicit_messages()
            except Exception as e:
                # Fallback to pattern detection
                return self._pattern_analyze_implicit_messages(error=str(e))
        else:
            return self._pattern_analyze_implicit_messages()
    
    def _llm_analyze_implicit_messages(self) -> Dict[str, List[str]]:
        """Use LLM to detect sophisticated implicit communication patterns."""
        
        prompt = f"""
        Analyze this email for implicit/unspoken messages and subtle communication patterns.
        
        EMAIL CONTENT:
        {self.current_email_content}
        
        SENDER: {self.current_sender}
        
        Look for these IMPLICIT patterns (things not directly stated):
        
        1. IMPLICIT THREATS: Veiled threats, consequences implied but not stated
        2. POWER DYNAMICS: Attempts to establish dominance or control
        3. EMOTIONAL MANIPULATION: Subtle guilt, shame, or fear induction
        4. SOCIAL PRESSURE: Implied social consequences, reputation threats
        
        Focus on SUBTEXT and IMPLICATIONS, not direct statements.
        
        Respond in JSON format:
        {{
            "threats": ["list of implicit threats found"],
            "power_plays": ["dominance or control tactics"],
            "emotional_hooks": ["subtle emotional manipulation"],
            "social_weapons": ["social pressure or reputation threats"],
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation of detected patterns"
        }}
        
        If no implicit patterns found, return empty arrays.
        """
        
        if hasattr(self.llm_analyzer, 'provider'):
            # Real LLM providers
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
            raise ValueError("No LLM analyzer available. Real LLM required for language-agnostic implicit message analysis.")
        
        import json
        llm_result = json.loads(result)
        
        # Convert to expected format
        return {
            "threats": llm_result.get("threats", []),
            "power_plays": llm_result.get("power_plays", []),
            "emotional_hooks": llm_result.get("emotional_hooks", []),
            "social_weapons": llm_result.get("social_weapons", []),
            "analysis_method": "llm_enhanced",
            "confidence": llm_result.get("confidence", 0.7),
            "reasoning": llm_result.get("reasoning", "")
        }
    
    def _pattern_analyze_implicit_messages(self, error: str = None) -> Dict[str, List[str]]:
        """Fallback pattern-based implicit message detection."""
        
        implicit = {
            "threats": [],
            "power_plays": [],
            "emotional_hooks": [],
            "social_weapons": [],
            "analysis_method": "pattern_fallback",
            "confidence": 0.5
        }
        
        if error:
            implicit["fallback_reason"] = f"LLM analysis failed: {error}"
        
        content_lower = self.current_email_content.lower()
        
        # Implicit threat patterns
        threat_patterns = ["or else", "if you don't", "you'll regret", "consequences", "last chance"]
        for pattern in threat_patterns:
            if pattern in content_lower:
                implicit["threats"].append("conditional_threat")
                break
                
        # Power play patterns  
        power_patterns = ["you have to", "you must", "no choice", "demand", "require"]
        for pattern in power_patterns:
            if pattern in content_lower:
                implicit["power_plays"].append("authority_assertion")
                break
        
        # Emotional manipulation patterns
        emotion_patterns = ["disappointed", "expected better", "thought you were", "after everything"]
        for pattern in emotion_patterns:
            if pattern in content_lower:
                implicit["emotional_hooks"].append("guilt_induction")
                break
                
        # Social pressure patterns  
        social_patterns = ["everyone knows", "people are saying", "others think", "tell everyone"]
        for pattern in social_patterns:
            if pattern in content_lower:
                implicit["social_weapons"].append("false_consensus")
                break
        
        return implicit
        
    def _detect_escalation_pattern(self) -> bool:
        """Detect if communication is escalating over iterations."""
        if len(self.fact_ratios) < 2:
            return False
            
        # Simple escalation detection - decreasing fact ratios over time
        recent_ratios = self.fact_ratios[-3:]
        return len(recent_ratios) >= 2 and recent_ratios[-1] < recent_ratios[0]