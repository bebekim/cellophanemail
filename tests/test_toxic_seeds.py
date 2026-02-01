# ABOUTME: Tests Four Horsemen detection against realistic toxic text seeds
# ABOUTME: Validates the horsemen-based threat level detection

import pytest
from typing import List

from analysis_engine import (
    ThreatLevel,
    HorsemanDetection,
    AnalysisResult,
    decide_action,
    ProtectionAction,
)

from tests.fixtures.toxic_text_seeds import (
    ALL_SEEDS,
    ALL_TOXIC_SEEDS,
    CLEAN_SEEDS,
    CRITICISM_SEEDS,
    CONTEMPT_SEEDS,
    DEFENSIVENESS_SEEDS,
    STONEWALLING_SEEDS,
    MULTIPLE_HORSEMEN_SEEDS,
    get_critical_seeds,
    get_contempt_seeds,
    ToxicTextSeed,
)


class TestSeedDataStructure:
    """Verify seed data is properly structured."""

    def test_all_seeds_have_content(self):
        """Every seed should have non-empty content."""
        for seed in ALL_SEEDS:
            assert seed.content, f"Seed missing content: {seed}"
            assert len(seed.content) > 0

    def test_all_seeds_have_threat_level(self):
        """Every seed should have a valid threat level."""
        valid_levels = {"safe", "low", "medium", "high", "critical"}
        for seed in ALL_SEEDS:
            assert seed.expected_threat_level in valid_levels, \
                f"Invalid threat level '{seed.expected_threat_level}' in: {seed.content[:50]}"

    def test_all_toxic_seeds_have_horsemen(self):
        """Every toxic seed should have at least one horseman."""
        for seed in ALL_TOXIC_SEEDS:
            assert len(seed.expected_horsemen) > 0, \
                f"Toxic seed missing horsemen: {seed.content[:50]}"

    def test_clean_seeds_have_no_horsemen(self):
        """Clean seeds should have no horsemen."""
        for seed in CLEAN_SEEDS:
            assert len(seed.expected_horsemen) == 0, \
                f"Clean seed should have no horsemen: {seed.content[:50]}"
            assert seed.expected_threat_level == "safe"

    def test_seed_count_is_reasonable(self):
        """Verify we have enough seeds for testing."""
        assert len(ALL_SEEDS) >= 30, "Need at least 30 total seeds"
        assert len(ALL_TOXIC_SEEDS) >= 25, "Need at least 25 toxic seeds"
        assert len(CLEAN_SEEDS) >= 3, "Need at least 3 clean seeds"

    def test_horsemen_categories_covered(self):
        """Verify all four horsemen are represented."""
        assert len(CRITICISM_SEEDS) >= 3, "Need criticism examples"
        assert len(CONTEMPT_SEEDS) >= 3, "Need contempt examples"
        assert len(DEFENSIVENESS_SEEDS) >= 3, "Need defensiveness examples"
        assert len(STONEWALLING_SEEDS) >= 3, "Need stonewalling examples"


class TestThreatLevelMapping:
    """Test that expected threat levels match the horsemen-based logic."""

    def test_safe_requires_no_horsemen(self):
        """SAFE threat level requires no horsemen."""
        safe_seeds = [s for s in ALL_SEEDS if s.expected_threat_level == "safe"]
        for seed in safe_seeds:
            assert len(seed.expected_horsemen) == 0, \
                f"SAFE should have no horsemen: {seed.content[:50]}"

    def test_low_requires_single_non_contempt(self):
        """LOW threat level = single non-contempt horseman."""
        low_seeds = [s for s in ALL_SEEDS if s.expected_threat_level == "low"]
        for seed in low_seeds:
            assert len(seed.expected_horsemen) == 1, \
                f"LOW should have exactly 1 horseman: {seed.content[:50]}"
            assert "contempt" not in seed.expected_horsemen, \
                f"LOW should not have contempt: {seed.content[:50]}"

    def test_medium_requires_two_non_contempt(self):
        """MEDIUM threat level = 2 non-contempt horsemen."""
        medium_seeds = [s for s in ALL_SEEDS if s.expected_threat_level == "medium"]
        for seed in medium_seeds:
            assert len(seed.expected_horsemen) == 2, \
                f"MEDIUM should have exactly 2 horsemen: {seed.content[:50]}"
            assert "contempt" not in seed.expected_horsemen, \
                f"MEDIUM should not have contempt: {seed.content[:50]}"

    def test_high_is_contempt_alone_or_three_horsemen(self):
        """HIGH = contempt alone OR 3+ non-contempt horsemen."""
        high_seeds = [s for s in ALL_SEEDS if s.expected_threat_level == "high"]
        for seed in high_seeds:
            has_contempt = "contempt" in seed.expected_horsemen
            if has_contempt:
                # Contempt alone = HIGH
                assert len(seed.expected_horsemen) == 1, \
                    f"HIGH with contempt should be contempt alone: {seed.content[:50]}"
            else:
                # 3+ non-contempt = HIGH
                assert len(seed.expected_horsemen) >= 3, \
                    f"HIGH without contempt needs 3+ horsemen: {seed.content[:50]}"

    def test_critical_is_contempt_plus_other_or_all_four(self):
        """CRITICAL = contempt + any other, OR all 4 horsemen."""
        critical_seeds = get_critical_seeds()
        for seed in critical_seeds:
            has_contempt = "contempt" in seed.expected_horsemen
            num_horsemen = len(seed.expected_horsemen)

            # CRITICAL requires: contempt + other, OR all 4
            valid_critical = (
                (has_contempt and num_horsemen >= 2) or
                (num_horsemen >= 4)
            )
            assert valid_critical, \
                f"CRITICAL needs contempt+other or all 4: {seed.content[:50]}, got {seed.expected_horsemen}"


class TestThreatLevelFromHorsemen:
    """Test ThreatLevel.from_horsemen against seed expectations."""

    def _create_horsemen(self, names: List[str]) -> List[HorsemanDetection]:
        """Create HorsemanDetection objects from names."""
        return [
            HorsemanDetection(
                horseman=name,
                confidence=0.8,  # Above significance threshold
                indicators=["test"],
                severity="medium"
            )
            for name in names
        ]

    def test_threat_levels_match_expectations(self):
        """Verify from_horsemen produces expected threat levels."""
        for seed in ALL_SEEDS:
            horsemen = self._create_horsemen(seed.expected_horsemen)
            actual_level = ThreatLevel.from_horsemen(horsemen)
            expected_level = ThreatLevel(seed.expected_threat_level)

            assert actual_level == expected_level, \
                f"Expected {expected_level}, got {actual_level} for: {seed.content[:50]}... " \
                f"(horsemen: {seed.expected_horsemen})"


class TestDecideActionFromSeeds:
    """Test decide_action produces appropriate protection actions."""

    def _create_horsemen(self, names: List[str]) -> List[HorsemanDetection]:
        """Create HorsemanDetection objects from names."""
        return [
            HorsemanDetection(
                horseman=name,
                confidence=0.8,
                indicators=["test"],
                severity="medium"
            )
            for name in names
        ]

    def test_clean_seeds_forward_clean(self):
        """Clean messages should forward clean."""
        for seed in CLEAN_SEEDS:
            horsemen = self._create_horsemen(seed.expected_horsemen)
            action = decide_action(horsemen)
            assert action == ProtectionAction.FORWARD_CLEAN, \
                f"Clean should forward clean: {seed.content[:50]}"

    def test_single_horseman_forwards_with_context(self):
        """Single horseman (non-contempt) should forward with context."""
        single_horseman_seeds = [
            s for s in ALL_TOXIC_SEEDS
            if len(s.expected_horsemen) == 1 and "contempt" not in s.expected_horsemen
        ]
        for seed in single_horseman_seeds:
            horsemen = self._create_horsemen(seed.expected_horsemen)
            action = decide_action(horsemen)
            assert action == ProtectionAction.FORWARD_WITH_CONTEXT, \
                f"Single horseman should add context: {seed.content[:50]}"

    def test_contempt_alone_summarizes(self):
        """Contempt alone should summarize only."""
        contempt_alone = [
            s for s in CONTEMPT_SEEDS
            if len(s.expected_horsemen) == 1
        ]
        for seed in contempt_alone:
            horsemen = self._create_horsemen(seed.expected_horsemen)
            action = decide_action(horsemen)
            assert action == ProtectionAction.SUMMARIZE_ONLY, \
                f"Contempt alone should summarize: {seed.content[:50]}"

    def test_critical_seeds_block(self):
        """Critical threat should block entirely."""
        for seed in get_critical_seeds():
            horsemen = self._create_horsemen(seed.expected_horsemen)
            action = decide_action(horsemen)
            assert action == ProtectionAction.BLOCK_ENTIRELY, \
                f"Critical should block: {seed.content[:50]} (horsemen: {seed.expected_horsemen})"


class TestContemptWeighting:
    """Test that contempt is properly weighted as most destructive."""

    def _create_horsemen(self, names: List[str]) -> List[HorsemanDetection]:
        return [
            HorsemanDetection(horseman=name, confidence=0.8, indicators=["test"], severity="medium")
            for name in names
        ]

    def test_contempt_alone_is_high(self):
        """Single contempt should be HIGH threat level."""
        horsemen = self._create_horsemen(["contempt"])
        level = ThreatLevel.from_horsemen(horsemen)
        assert level == ThreatLevel.HIGH

    def test_single_criticism_is_low(self):
        """Single criticism (non-contempt) should be LOW."""
        horsemen = self._create_horsemen(["criticism"])
        level = ThreatLevel.from_horsemen(horsemen)
        assert level == ThreatLevel.LOW

    def test_contempt_plus_any_is_critical(self):
        """Contempt + any other horseman = CRITICAL."""
        for other in ["criticism", "defensiveness", "stonewalling"]:
            horsemen = self._create_horsemen(["contempt", other])
            level = ThreatLevel.from_horsemen(horsemen)
            assert level == ThreatLevel.CRITICAL, \
                f"contempt + {other} should be CRITICAL, got {level}"

    def test_contempt_escalates_from_any_combination(self):
        """Adding contempt to any combination should escalate to CRITICAL."""
        # Two non-contempt = MEDIUM
        horsemen_without = self._create_horsemen(["criticism", "defensiveness"])
        level_without = ThreatLevel.from_horsemen(horsemen_without)
        assert level_without == ThreatLevel.MEDIUM

        # Add contempt = CRITICAL
        horsemen_with = self._create_horsemen(["criticism", "defensiveness", "contempt"])
        level_with = ThreatLevel.from_horsemen(horsemen_with)
        assert level_with == ThreatLevel.CRITICAL


class TestSeedCoverage:
    """Verify seeds cover important scenarios."""

    def test_has_financial_manipulation(self):
        """Should have financial manipulation examples."""
        financial = [s for s in ALL_TOXIC_SEEDS if "money" in s.content.lower() or "insurance" in s.content.lower() or "pay" in s.content.lower()]
        assert len(financial) >= 2, "Need financial manipulation examples"

    def test_has_boundary_violations(self):
        """Should have boundary violation examples."""
        boundary = [s for s in ALL_TOXIC_SEEDS if "permission" in s.content.lower() or "right to" in s.content.lower()]
        assert len(boundary) >= 1, "Need boundary violation examples"

    def test_has_holiday_manipulation(self):
        """Should have holiday manipulation examples."""
        holiday = [s for s in ALL_TOXIC_SEEDS if any(h in s.content.lower() for h in ["christmas", "thanksgiving", "holiday"])]
        assert len(holiday) >= 2, "Need holiday manipulation examples"

    def test_has_gaslighting(self):
        """Should have gaslighting examples."""
        gaslighting = [s for s in ALL_TOXIC_SEEDS if "never happened" in s.content.lower() or "making things up" in s.content.lower()]
        assert len(gaslighting) >= 1, "Need gaslighting examples"
