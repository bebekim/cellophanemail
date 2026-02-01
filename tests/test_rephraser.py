# ABOUTME: Unit tests for analysis_engine rephraser module
# ABOUTME: Tests rephrasing logic used by Android app for toxic message transformation

import pytest

from analysis_engine import (
    AnalysisResult,
    ThreatLevel,
    HorsemanDetection,
    build_rephrase_context,
    format_rephrased_with_notice,
    get_rephrase_instructions,
    estimate_rephrase_difficulty,
    should_attempt_rephrase,
    create_rephrase_summary,
)


def _create_analysis(
    horsemen: list[str] | None = None,
    reasoning: str = "Test reasoning",
) -> AnalysisResult:
    """Helper to create AnalysisResult for testing."""
    horsemen_detected = []
    if horsemen:
        for h in horsemen:
            horsemen_detected.append(
                HorsemanDetection(
                    horseman=h,
                    confidence=0.8,
                    indicators=["test indicator"],
                    severity="medium",
                )
            )
    threat_level = ThreatLevel.from_horsemen(horsemen_detected)
    return AnalysisResult(
        safe=threat_level == ThreatLevel.SAFE,
        threat_level=threat_level,
        horsemen_detected=horsemen_detected,
        reasoning=reasoning,
        processing_time_ms=100,
    )


class TestBuildRephraseContext:
    """Tests for build_rephrase_context function."""

    def test_builds_context_with_threat_level(self):
        """Context should include threat level."""
        analysis = _create_analysis(["contempt"])
        context = build_rephrase_context(analysis)
        assert context["threat_level"] == "high"

    def test_builds_context_with_detected_patterns(self):
        """Context should include comma-separated horsemen names."""
        analysis = _create_analysis(["criticism", "contempt"])
        context = build_rephrase_context(analysis)
        assert "criticism" in context["detected_patterns"]
        assert "contempt" in context["detected_patterns"]

    def test_builds_context_with_no_patterns(self):
        """Context should show 'none' when no horsemen detected."""
        analysis = _create_analysis()
        context = build_rephrase_context(analysis)
        assert context["detected_patterns"] == "none"

    def test_builds_context_with_reasoning(self):
        """Context should include the reasoning."""
        analysis = _create_analysis(reasoning="Custom reasoning here")
        context = build_rephrase_context(analysis)
        assert context["reasoning"] == "Custom reasoning here"


class TestFormatRephrasedWithNotice:
    """Tests for format_rephrased_with_notice function."""

    def test_includes_wellbeing_header(self):
        """Output should include wellbeing notice header."""
        analysis = _create_analysis(["criticism"])
        result = format_rephrased_with_notice("original", "rephrased", analysis)
        assert "[This message was rephrased for your wellbeing" in result

    def test_includes_detected_patterns_in_header(self):
        """Header should include detected horsemen patterns."""
        analysis = _create_analysis(["manipulation"])
        result = format_rephrased_with_notice("original", "rephrased", analysis)
        assert "manipulation" in result

    def test_includes_rephrased_content(self):
        """Output should include the rephrased content."""
        analysis = _create_analysis(["criticism"])
        result = format_rephrased_with_notice("original", "This is rephrased", analysis)
        assert "This is rephrased" in result

    def test_includes_archive_note_by_default(self):
        """Output should include archive note by default."""
        analysis = _create_analysis(["criticism"])
        result = format_rephrased_with_notice("original", "rephrased", analysis)
        assert "Original message archived" in result

    def test_excludes_archive_note_when_disabled(self):
        """Output should not include archive note when disabled."""
        analysis = _create_analysis(["criticism"])
        result = format_rephrased_with_notice(
            "original", "rephrased", analysis, include_archive_note=False
        )
        assert "Original message archived" not in result

    def test_does_not_include_original_content(self):
        """Output should NOT include the original toxic content."""
        analysis = _create_analysis(["criticism"])
        result = format_rephrased_with_notice(
            "TOXIC ORIGINAL CONTENT", "Safe rephrased", analysis
        )
        assert "TOXIC ORIGINAL CONTENT" not in result


class TestGetRephraseInstructions:
    """Tests for get_rephrase_instructions function."""

    def test_returns_instructions_for_criticism(self):
        """Should return criticism-specific instructions."""
        analysis = _create_analysis(["criticism"])
        instructions = get_rephrase_instructions(analysis)
        assert any("constructive" in i.lower() for i in instructions)

    def test_returns_instructions_for_contempt(self):
        """Should return contempt-specific instructions."""
        analysis = _create_analysis(["contempt"])
        instructions = get_rephrase_instructions(analysis)
        assert any("mockery" in i.lower() or "sarcasm" in i.lower() for i in instructions)

    def test_returns_instructions_for_defensiveness(self):
        """Should return defensiveness-specific instructions."""
        analysis = _create_analysis(["defensiveness"])
        instructions = get_rephrase_instructions(analysis)
        assert any("blame" in i.lower() for i in instructions)

    def test_returns_instructions_for_stonewalling(self):
        """Should return stonewalling-specific instructions."""
        analysis = _create_analysis(["stonewalling"])
        instructions = get_rephrase_instructions(analysis)
        assert any("engagement" in i.lower() or "dismissive" in i.lower() for i in instructions)

    def test_returns_instructions_for_manipulation(self):
        """Should return manipulation-specific instructions."""
        analysis = _create_analysis(["manipulation"])
        instructions = get_rephrase_instructions(analysis)
        assert any("guilt" in i.lower() or "manipulation" in i.lower() for i in instructions)

    def test_returns_instructions_for_multiple_horsemen(self):
        """Should return instructions for all detected horsemen."""
        analysis = _create_analysis(["criticism", "contempt", "manipulation"])
        instructions = get_rephrase_instructions(analysis)
        assert len(instructions) == 3

    def test_returns_general_instructions_when_no_horsemen(self):
        """Should return general instructions when no horsemen detected."""
        analysis = _create_analysis()
        instructions = get_rephrase_instructions(analysis)
        assert len(instructions) > 0
        assert any("hostile" in i.lower() or "respectful" in i.lower() for i in instructions)


class TestEstimateRephraseDifficulty:
    """Tests for estimate_rephrase_difficulty function."""

    def test_easy_for_no_horsemen(self):
        """No horsemen should be easy."""
        analysis = _create_analysis()
        assert estimate_rephrase_difficulty(analysis) == "easy"

    def test_easy_with_one_horseman(self):
        """One non-contempt horseman should be easy."""
        analysis = _create_analysis(["criticism"])
        assert estimate_rephrase_difficulty(analysis) == "easy"

    def test_moderate_with_two_horsemen(self):
        """Two non-contempt horsemen should be moderate."""
        analysis = _create_analysis(["criticism", "defensiveness"])
        assert estimate_rephrase_difficulty(analysis) == "moderate"

    def test_difficult_with_contempt(self):
        """Contempt alone should be difficult (hardest to rephrase)."""
        analysis = _create_analysis(["contempt"])
        assert estimate_rephrase_difficulty(analysis) == "difficult"

    def test_difficult_with_many_horsemen(self):
        """Three or more horsemen should be difficult."""
        analysis = _create_analysis(["criticism", "defensiveness", "stonewalling"])
        assert estimate_rephrase_difficulty(analysis) == "difficult"


class TestShouldAttemptRephrase:
    """Tests for should_attempt_rephrase function."""

    def test_should_not_rephrase_critical(self):
        """Should not attempt rephrase for CRITICAL threat level (contempt + other)."""
        analysis = _create_analysis(["contempt", "criticism"])  # CRITICAL
        assert should_attempt_rephrase(analysis) is False

    def test_should_not_rephrase_safe_content(self):
        """Should not attempt rephrase for safe content (no horsemen)."""
        analysis = _create_analysis()  # SAFE
        assert should_attempt_rephrase(analysis) is False

    def test_should_rephrase_low_threat(self):
        """Should attempt rephrase for LOW threat level."""
        analysis = _create_analysis(["criticism"])  # LOW
        assert should_attempt_rephrase(analysis) is True

    def test_should_rephrase_medium_threat(self):
        """Should attempt rephrase for MEDIUM threat level."""
        analysis = _create_analysis(["criticism", "defensiveness"])  # MEDIUM
        assert should_attempt_rephrase(analysis) is True

    def test_should_rephrase_high_threat(self):
        """Should attempt rephrase for HIGH threat level (contempt alone)."""
        analysis = _create_analysis(["contempt"])  # HIGH
        assert should_attempt_rephrase(analysis) is True


class TestCreateRephraseSummary:
    """Tests for create_rephrase_summary function."""

    def test_includes_original_length(self):
        """Summary should include original content length."""
        analysis = _create_analysis(["criticism"])
        summary = create_rephrase_summary(100, 80, analysis)
        assert summary["original_length"] == 100

    def test_includes_rephrased_length(self):
        """Summary should include rephrased content length."""
        analysis = _create_analysis(["criticism"])
        summary = create_rephrase_summary(100, 80, analysis)
        assert summary["rephrased_length"] == 80

    def test_calculates_length_change_percent(self):
        """Summary should calculate length change percentage."""
        analysis = _create_analysis(["criticism"])
        summary = create_rephrase_summary(100, 80, analysis)
        assert summary["length_change_percent"] == -20.0

    def test_handles_zero_original_length(self):
        """Should handle zero original length gracefully."""
        analysis = _create_analysis(["criticism"])
        summary = create_rephrase_summary(0, 10, analysis)
        assert summary["length_change_percent"] == 0

    def test_includes_is_toxic(self):
        """Summary should include is_toxic flag."""
        analysis = _create_analysis(["criticism"])
        summary = create_rephrase_summary(100, 80, analysis)
        assert summary["is_toxic"] is True

    def test_includes_threat_level(self):
        """Summary should include threat level."""
        analysis = _create_analysis(["contempt"])  # HIGH
        summary = create_rephrase_summary(100, 80, analysis)
        assert summary["threat_level"] == "high"

    def test_includes_horsemen_detected(self):
        """Summary should include detected horsemen names."""
        analysis = _create_analysis(["criticism", "contempt"])
        summary = create_rephrase_summary(100, 80, analysis)
        assert "criticism" in summary["horsemen_detected"]
        assert "contempt" in summary["horsemen_detected"]

    def test_includes_difficulty(self):
        """Summary should include difficulty estimate."""
        analysis = _create_analysis(["criticism", "contempt", "manipulation"])
        summary = create_rephrase_summary(100, 80, analysis)
        assert summary["difficulty"] == "difficult"
