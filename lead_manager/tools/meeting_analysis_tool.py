"""
AI-powered meeting analysis tools for Lead Manager.
"""

import os
import logging
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from config.cerebras_client import CerebrasConfig
from lead_manager.config import LeadManagerConfig

logger = logging.getLogger(__name__)


class MeetingRequestAnalysis(BaseModel):
    is_meeting_request: bool = Field(..., description="Whether email contains a meeting request")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    request_type: str = Field(default="none", description="Type of meeting request")
    urgency: str = Field(default="normal", description="Urgency level")
    extracted_dates: List[str] = Field(default_factory=list, description="Mentioned dates/times")
    extracted_topics: List[str] = Field(default_factory=list, description="Meeting topics")


class HotLeadAnalysis(BaseModel):
    is_hot_lead: bool = Field(..., description="Whether email sender is a hot lead")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    lead_score: int = Field(default=0, description="Lead qualification score (0-100)")
    lead_source: str = Field(default="unknown", description="Detected lead source")
    interest_signals: List[str] = Field(default_factory=list, description="Signals of interest")
    business_context: str = Field(default="unknown", description="Detected business context")


class MeetingAnalysisTool(BaseTool):
    """Tool to analyze emails for meeting requests using AI."""
    
    name: str = "meeting_analysis_tool"
    description: str = "Analyze email content for meeting requests using Cerebras LLM"
    
    def _run(self, email_body: str, sender_email: str, subject: str = "") -> Dict[str, Any]:
        """
        Analyze email content for meeting requests.
        
        Args:
            email_body: Email content
            sender_email: Email sender address
            subject: Email subject (optional)
            
        Returns:
            Dictionary with meeting request analysis
        """
        try:
            logger.info(f"Analyzing email from {sender_email} for meeting requests")
            
            # Prepare analysis prompt
            analysis_prompt = self._build_meeting_analysis_prompt(email_body, sender_email, subject)
            
            # Get LLM response
            response = self._get_llm_response(analysis_prompt)
            
            # Parse response
            analysis_result = self._parse_llm_response(response)
            
            logger.info(f"Meeting analysis completed: {analysis_result.confidence:.2f} confidence")
            
            return {
                "success": True,
                "analysis": analysis_result.dict(),
                "llm_response": response
            }
            
        except Exception as e:
            logger.error(f"Error analyzing meeting request: {str(e)}")
            
            # Fallback keyword analysis
            fallback_result = self._fallback_keyword_analysis(email_body, subject)
            
            return {
                "success": False,
                "error": str(e),
                "analysis": fallback_result.dict(),
                "fallback_used": True
            }
    
    def _build_meeting_analysis_prompt(self, email_body: str, sender_email: str, subject: str = "") -> str:
        """Build prompt for meeting request analysis."""
        return f"""
You are an expert email analyst specializing in identifying meeting requests in business emails.

Email Details:
- From: {sender_email}
- Subject: {subject}
- Body: {email_body[:1000]}...

Analyze this email and determine:

1. Does this email contain a meeting request (explicit or implicit)?
2. What is your confidence level (0.0-1.0)?
3. What type of meeting request is it?
4. What is the urgency level?
5. Are there any specific dates/times mentioned?
6. What topics would be discussed?

Respond ONLY in valid JSON format:
{{
    "is_meeting_request": bool,
    "confidence": 0.0-1.0,
    "request_type": "explicit|implicit|none",
    "urgency": "urgent|high|normal|low",
    "extracted_dates": ["mentioned dates/times"],
    "extracted_topics": ["topics to discuss"]
}}

Meeting request indicators include:
- Direct requests: "Let's meet", "Schedule a call", "Set up a meeting"
- Implicit requests: "When are you available?", "Discuss this further", "Chat about"
- Calendar phrases: "Schedule time", "Book a slot", "Arrange meeting"
        """
    
    def _get_llm_response(self, prompt: str) -> str:
        """Get response from Cerebras LLM using CrewAI LLM."""
        try:
            from leads_finder.llm_config import LLMConfig
            
            llm = LLMConfig.get_cerebras_llm(
                model=LeadManagerConfig.DEFAULT_MODEL,
                temperature=0.3,
                max_completion_tokens=500
            )
            
            response = llm.call(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Cerebras API error: {e}")
            raise
    
    def _parse_llm_response(self, response: str) -> MeetingRequestAnalysis:
        """Parse LLM response into structured analysis."""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                return MeetingRequestAnalysis(
                    is_meeting_request=data.get("is_meeting_request", False),
                    confidence=data.get("confidence", 0.0),
                    request_type=data.get("request_type", "none"),
                    urgency=data.get("urgency", " normal"),
                    extracted_dates=data.get("extracted_dates", []),
                    extracted_topics=data.get("extracted_topics", [])
                )
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
        
        # Fallback to default
        return MeetingRequestAnalysis(
            is_meeting_request=False,
            confidence=0.0,
            request_type="none",
            urgency="normal"
        )
    
    def _fallback_keyword_analysis(self, email_body: str, subject: str) -> MeetingRequestAnalysis:
        """Fallback keyword-based analysis."""
        combined_text = f"{subject} {email_body}".lower()
        
        meeting_keywords = [
            "meet", "meeting", "schedule", "call", "appointment", "session",
            "discuss", "talk", "chat", "conversation", "demo", "presentation"
        ]
        
        urgency_keywords = [
            "urgent", "asap", "immediately", "soon", "quick", "rapid"
        ]
        
        keyword_count = sum(1 for keyword in meeting_keywords if keyword in combined_text)
        urgency_count = sum(1 for keyword in urgency_keywords if keyword in combined_text)
        
        is_request = keyword_count >= 2
        confidence = min(keyword_count * 0.3, 1.0)
        
        return MeetingRequestAnalysis(
            is_meeting_request=is_request,
            confidence=confidence,
            request_type="implicit" if is_request else "none",
            urgency="urgent" if urgency_count > 0 else "normal"
        )


class HotLeadAnalysisTool(BaseTool):
    """Tool to analyze emails for hot lead signals using AI."""
    
    name: str = "hot_lead_analysis_tool"
    description: str = "Analyze email content to detect hot leads based on interest patterns"
    
    def _run(self, email_body: str, sender_email: str, subject: str = "") -> Dict[str, Any]:
        """
        Analyze email content for hot lead indicators.
        
        Args:
            email_body: Email content
            sender_email: Email sender address
            subject: Email subject (optional)
            
        Returns:
            Dictionary with hot lead analysis
        """
        try:
            logger.info(f"Analyzing email from {sender_email} for hot lead signals")
            
            # Prepare analysis prompt
            analysis_prompt = self._build_hot_lead_analysis_prompt(email_body, sender_email, subject)
            
            # Get LLM response
            response = self._get_llm_response(analysis_prompt)
            
            # Parse response
            analysis_result = self._parse_hot_lead_response(response)
            
            # Apply thresholds
            if analysis_result.confidence >= LeadManagerConfig.HOT_LEAD_THRESHOLD:
                analysis_result.is_hot_lead = True
            
            logger.info(f"Hot lead analysis completed: {analysis_result.confidence:.2f} confidence, hot lead({analysis_result.is_hot_lead})")
            
            return {
                "success": True,
                "analysis": analysis_result.dict(),
                "llm_response": response
            }
            
        except Exception as e:
            logger.error(f"Error analyzing hot lead: {str(e)}")
            
            # Fallback keyword analysis
            fallback_result = self._fallback_hot_lead_analysis(email_body, subject)
            
            return {
                "success": False,
                "error": str(e),
                "analysis": fallback_result.dict(),
                "fallback_used": True
            }
    
    def _build_hot_lead_analysis_prompt(self, email_body: str, sender_email: str, subject: str = "") -> str:
        """Build prompt for hot lead analysis."""
        return f"""
You are an expert sales analyst specializing in identifying hot leads from email communications.

Email Details:
- From: {sender_email}
- Subject: {subject}
- Body: {email_body[:1000]}...

Analyze this email and determine:

1. Is this email sender a potentially hot lead (showing genuine interest)?
2. What is your confidence score (0.0-1.0)?
3. What lead qualification score would you give (0-100)?
4. What is the likely lead source?
5. What specific signals indicate interest?
6. What is the business context?

Respond ONLY in valid JSON format:
{{
    "is_hot_lead": bool,
    "confidence": 0.0-1.0,
    "lead_score": 0-100,
    "lead_source": "prospect|referral|inbound|outbound|unknown",
    "interest_signals": ["list of interest indicators"],
    "business_context": "brief description of business interest"
}}

Hot lead indicators include:
- Expressing genuine interest in services/products
- Asking specific questions about offerings
- Mentioning budget, timelines, or decision-making process
- Requesting demos, pricing, or proposals
- Professional email addresses from business domains
- Specific business pain points mentioned
- Mentions of partnerships or collaboration

Avoid identifying automated emails, spam, or promotional content as hot leads.
        """
    
    def _get_llm_response(self, prompt: str) -> str:
        """Get response from Cerebras LLM using CrewAI LLM."""
        try:
            from leads_finder.llm_config import LLMConfig
            
            llm = LLMConfig.get_cerebras_llm(
                model=LeadManagerConfig.DEFAULT_MODEL,
                temperature=0.3,
                max_completion_tokens=500
            )
            
            response = llm.call(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Cerebras API error: {e}")
            raise
    
    def _parse_hot_lead_response(self, response: str) -> HotLeadAnalysis:
        """Parse LLM response into structured hot lead analysis."""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                return HotLeadAnalysis(
                    is_hot_lead=data.get("is_hot_lead", False),
                    confidence=data.get("confidence", 0.0),
                    lead_score=data.get("lead_score", 0),
                    lead_source=data.get("lead_source", "unknown"),
                    interest_signals=data.get("interest_signals", []),
                    business_context=data.get("business_context", "unknown")
                )
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse hot lead response: {e}")
        
        # Fallback to default
        return HotLeadAnalysis(
            is_hot_lead=False,
            confidence=0.0,
            lead_score=0,
            lead_source="unknown"
        )
    
    def _fallback_hot_lead_analysis(self, email_body: str, subject: str) -> HotLeadAnalysis:
        """Fallback keyword-based hot lead analysis."""
        combined_text = f"{subject} {email_body}".lower()
        
        # Count hot lead keywords
        hot_lead_score = 0
        signals = []
        
        for keyword in LeadManagerConfig.HOT_LEAD_KEYWORDS:
            if keyword in combined_text:
                hot_lead_score += 2
                signals.append(f"mentions '{keyword}'")
        
        # Count urgency keywords
        urgency_signals = []
        for keyword in LeadManagerConfig.HOT_LEAD_URGENCY_KEYWORDS:
            if keyword in combined_text:
                hot_lead_score += 3
                urgency_signals.append(f"urgency: {keyword}")
        
        signals.extend(urgency_signals)
        
        # Check email domain quality
        email_domain = combined_text.split('@')[-1] if '@' in combined_text else ""
        if not any(personal_domain in email_domain for personal_domain in ["gmail", "yahoo", "hotmail"]):
            hot_lead_score += 5
            signals.append("professional email domain")
        
        is_hot_lead = hot_lead_score >= 10  # Threshold for fallback
        confidence = min(hot_lead_score / 20.0, 1.0)  # Normalize to 0-1
        
        return HotLeadAnalysis(
            is_hot_lead=is_hot_lead,
            confidence=confidence,
            lead_score=min(hot_lead_score * 4, 100),  # Scale to 0-100
            lead_source="email_content_analysis",
            interest_signals=signals,
            business_context="keyword-based analysis"
        )


# Tool instances for easy import
meeting_analysis_tool_instance = MeetingAnalysisTool()
hot_lead_analysis_tool_instance = HotLeadAnalysisTool()