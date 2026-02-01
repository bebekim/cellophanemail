# ABOUTME: Unit tests for analysis_engine MockAnalyzer
# ABOUTME: Tests mock analyzer for offline testing without LLM API calls

import pytest

from analysis_engine import (
    MockAnalyzer,
    IAnalyzer,
    AnalysisResult,
    ThreatLevel,
    HorsemanDetection,
    create_clean_analyzer,
    create_toxic_analyzer,
    create_graduated_analyzer,
)


class TestMockAnalyzerInterface:
    """Verify MockAnalyzer implements IAnalyzer correctly."""

    def test_mock_analyzer_is_ianalyzer(self):
        """MockAnalyzer should be an instance of IAnalyzer."""
        mock = MockAnalyzer()
        assert isinstance(mock, IAnalyzer)

    @pytest.mark.asyncio
    async def test_analyze_returns_analysis_result(self):
        """analyze() should return AnalysisResult."""
        mock = MockAnalyzer()
        result = await mock.analyze("test content")
        assert isinstance(result, AnalysisResult)

    @pytest.mark.asyncio
    async def test_rephrase_returns_string(self):
        """rephrase() should return string."""
        mock = MockAnalyzer()
        analysis = await mock.analyze("test content")
        result = await mock.rephrase("test content", analysis)
        assert isinstance(result, str)


class TestMockAnalyzerDefaults:
    """Test MockAnalyzer default behavior."""

    @pytest.mark.asyncio
    async def test_default_safe(self):
        """Default safe should be True with no horsemen."""
        mock = MockAnalyzer()
        result = await mock.analyze("test content")
        assert result.safe is True
        assert result.threat_level == ThreatLevel.SAFE
        assert len(result.horsemen_detected) == 0

    @pytest.mark.asyncio
    async def test_custom_default_safe(self):
        """Custom default safe should be used."""
        mock = MockAnalyzer(default_safe=False)
        result = await mock.analyze("test content")
        # When default_safe=False and no horsemen, threat_level is LOW
        assert result.threat_level == ThreatLevel.LOW

    @pytest.mark.asyncio
    async def test_default_rephrase_prefix(self):
        """Default rephrase should add prefix."""
        mock = MockAnalyzer()
        analysis = await mock.analyze("test content")
        result = await mock.rephrase("original message", analysis)
        assert result == "[Rephrased] original message"

    @pytest.mark.asyncio
    async def test_custom_rephrase_prefix(self):
        """Custom rephrase prefix should be used."""
        mock = MockAnalyzer(rephrase_prefix="[SAFE] ")
        analysis = await mock.analyze("test content")
        result = await mock.rephrase("original message", analysis)
        assert result == "[SAFE] original message"


class TestMockAnalyzerCustomResponses:
    """Test MockAnalyzer custom response configuration."""

    @pytest.mark.asyncio
    async def test_set_response_with_horsemen(self):
        """set_response should configure horsemen for pattern."""
        mock = MockAnalyzer()
        mock.set_response(
            "toxic content",
            horsemen=[
                HorsemanDetection(horseman="contempt", confidence=0.8, indicators=["toxic"], severity="high"),
            ],
        )

        result = await mock.analyze("This has toxic content here")
        assert result.threat_level == ThreatLevel.HIGH
        assert len(result.horsemen_detected) == 1

    @pytest.mark.asyncio
    async def test_set_response_case_insensitive(self):
        """Pattern matching should be case-insensitive."""
        mock = MockAnalyzer()
        mock.set_response(
            "TOXIC",
            horsemen=[
                HorsemanDetection(horseman="contempt", confidence=0.9, indicators=["TOXIC"], severity="high"),
            ],
        )

        result = await mock.analyze("this is toxic stuff")
        assert result.threat_level == ThreatLevel.HIGH

    @pytest.mark.asyncio
    async def test_set_response_safe_flag(self):
        """set_response should configure safe flag."""
        mock = MockAnalyzer()
        mock.set_response(
            "danger",
            horsemen=[
                HorsemanDetection(horseman="criticism", confidence=0.7, indicators=["danger"], severity="medium"),
            ],
            safe=False
        )

        result = await mock.analyze("danger zone")
        assert result.safe is False

    @pytest.mark.asyncio
    async def test_set_response_contempt_is_high(self):
        """Contempt alone should result in HIGH threat level."""
        mock = MockAnalyzer()
        mock.set_response(
            "mocking",
            horsemen=[
                HorsemanDetection(
                    horseman="contempt",
                    confidence=0.8,
                    indicators=["mockery"],
                    severity="high",
                )
            ]
        )

        result = await mock.analyze("mocking words")
        assert result.threat_level == ThreatLevel.HIGH
        assert len(result.horsemen_detected) == 1
        assert result.horsemen_detected[0].horseman == "contempt"

    @pytest.mark.asyncio
    async def test_set_response_contempt_plus_other_is_critical(self):
        """Contempt + another horseman should result in CRITICAL threat level."""
        mock = MockAnalyzer()
        mock.set_response(
            "hateful",
            horsemen=[
                HorsemanDetection(horseman="contempt", confidence=0.9, indicators=["hate"], severity="high"),
                HorsemanDetection(horseman="criticism", confidence=0.8, indicators=["attack"], severity="high"),
            ]
        )

        result = await mock.analyze("hateful message")
        assert result.threat_level == ThreatLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_set_response_reasoning(self):
        """set_response should configure custom reasoning."""
        mock = MockAnalyzer()
        mock.set_response("test", horsemen=[], reasoning="Custom reason")

        result = await mock.analyze("test message")
        assert result.reasoning == "Custom reason"

    @pytest.mark.asyncio
    async def test_set_rephrase_custom(self):
        """set_rephrase should configure custom rephrased content."""
        mock = MockAnalyzer()
        mock.set_rephrase("angry message", "Calm message instead")

        analysis = await mock.analyze("angry message")
        result = await mock.rephrase("angry message here", analysis)
        assert result == "Calm message instead"

    @pytest.mark.asyncio
    async def test_no_pattern_match_uses_default(self):
        """No pattern match should return defaults."""
        mock = MockAnalyzer()
        mock.set_response(
            "specific pattern",
            horsemen=[HorsemanDetection(horseman="contempt", confidence=0.9, indicators=["specific"], severity="high")],
        )

        result = await mock.analyze("different content")
        assert result.threat_level == ThreatLevel.SAFE


class TestMockAnalyzerCallHistory:
    """Test MockAnalyzer call tracking."""

    @pytest.mark.asyncio
    async def test_call_count_increments(self):
        """call_count should increment with each call."""
        mock = MockAnalyzer()
        assert mock.call_count == 0

        await mock.analyze("first")
        assert mock.call_count == 1

        await mock.analyze("second")
        assert mock.call_count == 2

    @pytest.mark.asyncio
    async def test_call_history_records_analyze(self):
        """call_history should record analyze calls."""
        mock = MockAnalyzer()
        await mock.analyze("test content", sender="test@example.com")

        assert len(mock.analyze_calls) == 1
        assert mock.analyze_calls[0]["method"] == "analyze"
        assert "test content" in mock.analyze_calls[0]["content"]
        assert mock.analyze_calls[0]["sender"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_call_history_records_rephrase(self):
        """call_history should record rephrase calls."""
        mock = MockAnalyzer()
        analysis = await mock.analyze("test")
        await mock.rephrase("rephrase this", analysis)

        assert len(mock.rephrase_calls) == 1
        assert mock.rephrase_calls[0]["method"] == "rephrase"
        assert "rephrase this" in mock.rephrase_calls[0]["content"]

    @pytest.mark.asyncio
    async def test_call_history_truncates_long_content(self):
        """call_history should truncate long content."""
        mock = MockAnalyzer()
        long_content = "x" * 200
        await mock.analyze(long_content)

        assert len(mock.call_history[0]["content"]) < 200
        assert "..." in mock.call_history[0]["content"]

    @pytest.mark.asyncio
    async def test_reset_clears_history(self):
        """reset() should clear call history and custom responses."""
        mock = MockAnalyzer()
        mock.set_response("pattern", horsemen=[])
        await mock.analyze("test")

        mock.reset()

        assert mock.call_count == 0
        assert len(mock.custom_responses) == 0


class TestFactoryFunctions:
    """Test factory functions for common mock configurations."""

    def test_create_clean_analyzer(self):
        """create_clean_analyzer should return safe defaults."""
        mock = create_clean_analyzer()
        assert mock.default_safe is True

    def test_create_toxic_analyzer_has_patterns(self):
        """create_toxic_analyzer should have toxic patterns configured."""
        mock = create_toxic_analyzer()
        assert len(mock.custom_responses) > 0

    @pytest.mark.asyncio
    async def test_create_toxic_analyzer_hate_pattern(self):
        """create_toxic_analyzer should detect 'hate' as critical."""
        mock = create_toxic_analyzer()
        result = await mock.analyze("I hate you")
        assert result.threat_level == ThreatLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_create_toxic_analyzer_terrible_pattern(self):
        """create_toxic_analyzer should detect 'terrible' as medium."""
        mock = create_toxic_analyzer()
        result = await mock.analyze("This is terrible work")
        assert result.threat_level == ThreatLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_create_graduated_analyzer_minor(self):
        """create_graduated_analyzer should handle 'minor issue'."""
        mock = create_graduated_analyzer()
        result = await mock.analyze("This is a minor issue")
        assert result.threat_level == ThreatLevel.LOW

    @pytest.mark.asyncio
    async def test_create_graduated_analyzer_moderate(self):
        """create_graduated_analyzer should handle 'moderate problem'."""
        mock = create_graduated_analyzer()
        result = await mock.analyze("This is a moderate problem")
        assert result.threat_level == ThreatLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_create_graduated_analyzer_serious(self):
        """create_graduated_analyzer should handle 'serious issue'."""
        mock = create_graduated_analyzer()
        result = await mock.analyze("This is a serious issue")
        assert result.threat_level == ThreatLevel.HIGH

    @pytest.mark.asyncio
    async def test_create_graduated_analyzer_extreme(self):
        """create_graduated_analyzer should handle 'extreme threat'."""
        mock = create_graduated_analyzer()
        result = await mock.analyze("This is an extreme threat")
        assert result.threat_level == ThreatLevel.CRITICAL


class TestMockAnalyzerIntegration:
    """Integration tests for MockAnalyzer with analysis_engine."""

    @pytest.mark.asyncio
    async def test_analysis_result_properties_work(self):
        """AnalysisResult from MockAnalyzer should have working properties."""
        mock = MockAnalyzer()
        horsemen = [
            HorsemanDetection(
                horseman="contempt",
                confidence=0.8,
                indicators=["test"],
                severity="high",
            )
        ]
        mock.set_response("test", horsemen=horsemen)

        result = await mock.analyze("test content")

        assert "contempt" in result.detected_horsemen_names

    @pytest.mark.asyncio
    async def test_threat_level_from_horsemen_used(self):
        """MockAnalyzer should use ThreatLevel.from_horsemen correctly."""
        mock = MockAnalyzer()

        # LOW: single non-contempt horseman
        mock.set_response(
            "low",
            horsemen=[HorsemanDetection(horseman="criticism", confidence=0.6, indicators=["low"], severity="low")]
        )

        # MEDIUM: 2 non-contempt horsemen
        mock.set_response(
            "medium",
            horsemen=[
                HorsemanDetection(horseman="criticism", confidence=0.7, indicators=["medium"], severity="medium"),
                HorsemanDetection(horseman="defensiveness", confidence=0.6, indicators=["medium"], severity="medium"),
            ]
        )

        # HIGH: contempt alone
        mock.set_response(
            "high",
            horsemen=[HorsemanDetection(horseman="contempt", confidence=0.85, indicators=["high"], severity="high")]
        )

        low = await mock.analyze("low content")
        medium = await mock.analyze("medium content")
        high = await mock.analyze("high content")

        assert low.threat_level == ThreatLevel.LOW
        assert medium.threat_level == ThreatLevel.MEDIUM
        assert high.threat_level == ThreatLevel.HIGH
