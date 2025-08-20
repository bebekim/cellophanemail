"""Tests for SharedContext system - TDD implementation."""

import pytest
from typing import Dict, List, Any


def test_shared_context_initialization():
    """RED: Test that SharedContext can be initialized with empty state."""
    # This test will fail because SharedContext doesn't exist yet
    from src.cellophanemail.features.email_protection.shared_context import SharedContext
    
    context = SharedContext()
    
    # Shared context should start with empty phases
    assert context.get_phase_data(1) == {}
    assert context.get_phase_data(2) == {}
    assert context.get_phase_data(3) == {}
    assert context.get_phase_data(4) == {}


def test_phase1_fact_extraction():
    """RED: Test Phase 1 can extract facts from email content."""
    from src.cellophanemail.features.email_protection.shared_context import SharedContext
    
    context = SharedContext()
    email_content = "The meeting is scheduled for 3pm tomorrow. I think you're being unreasonable."
    
    # This will fail because extract_facts method doesn't exist yet
    facts = context.extract_facts(email_content)
    
    # Should extract factual statements
    assert "The meeting is scheduled for 3pm tomorrow" in facts
    assert len(facts) > 0


def test_phase1_fact_emotion_ratio():
    """RED: Test Phase 1 can calculate fact vs emotion ratio."""
    from src.cellophanemail.features.email_protection.shared_context import SharedContext
    
    context = SharedContext()
    
    # Test content with clear fact/emotion split
    mixed_content = "The report is due Friday. You never listen to me!"
    
    # This will fail because calculate_fact_emotion_ratio doesn't exist yet
    ratio = context.calculate_fact_emotion_ratio(mixed_content)
    
    # Ratio should be a dict with fact_percentage and emotion_percentage
    assert "fact_percentage" in ratio
    assert "emotion_percentage" in ratio
    assert ratio["fact_percentage"] + ratio["emotion_percentage"] == 100.0
    assert 0 <= ratio["fact_percentage"] <= 100
    assert 0 <= ratio["emotion_percentage"] <= 100


def test_update_phase1_context():
    """RED: Test updating shared context with Phase 1 results."""
    from src.cellophanemail.features.email_protection.shared_context import SharedContext
    
    context = SharedContext()
    email_content = "The meeting is at 3pm. You're always late!"
    
    # This will fail because update_phase_context doesn't exist yet
    context.update_phase_context(1, email_content)
    
    # Phase 1 data should now contain facts and ratio
    phase1_data = context.get_phase_data(1)
    assert "facts" in phase1_data
    assert "fact_emotion_ratio" in phase1_data
    assert len(phase1_data["facts"]) > 0
    assert "fact_percentage" in phase1_data["fact_emotion_ratio"]