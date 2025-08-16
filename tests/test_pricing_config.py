"""
Test suite for pricing configuration module.
Following TDD methodology: Red -> Green -> Refactor
"""

import pytest
from cellophanemail.config.pricing import (
    STARTER_PRICE,
    STARTER_EMAILS,
    PROFESSIONAL_PRICE,
    PROFESSIONAL_EMAILS,
    UNLIMITED_PRICE,
    ADDON_PACK_PRICE,
    ADDON_PACK_EMAILS,
    TRIAL_PERIOD_DAYS,
    get_plan_details,
    calculate_email_limit,
    calculate_usage_percentage,
    get_addon_pack_details,
    get_trial_period_details,
)


class TestPricingConstants:
    """Test that all pricing constants are defined correctly."""
    
    def test_starter_plan_constants_exist(self):
        """Test that starter plan constants are defined."""
        assert STARTER_PRICE == 5
        assert STARTER_EMAILS == 100
    
    def test_professional_plan_constants_exist(self):
        """Test that professional plan constants are defined."""
        assert PROFESSIONAL_PRICE == 10
        assert PROFESSIONAL_EMAILS == 500
    
    def test_unlimited_plan_constants_exist(self):
        """Test that unlimited plan constants are defined."""
        assert UNLIMITED_PRICE == 25
    
    def test_addon_pack_constants_exist(self):
        """Test that add-on pack constants are defined."""
        assert ADDON_PACK_PRICE == 2
        assert ADDON_PACK_EMAILS == 50
    
    def test_trial_period_constant_exists(self):
        """Test that trial period constant is defined."""
        assert TRIAL_PERIOD_DAYS == 30


class TestPlanDetails:
    """Test plan details functionality."""
    
    def test_get_starter_plan_details(self):
        """Test getting starter plan details."""
        plan_details = get_plan_details("starter")
        
        assert plan_details["name"] == "starter"
        assert plan_details["price"] == 5
        assert plan_details["emails"] == 100
        assert plan_details["description"] == "Starter plan with 100 emails"
    
    def test_get_professional_plan_details(self):
        """Test getting professional plan details."""
        plan_details = get_plan_details("professional")
        
        assert plan_details["name"] == "professional"
        assert plan_details["price"] == 10
        assert plan_details["emails"] == 500
        assert plan_details["description"] == "Professional plan with 500 emails"
    
    def test_get_unlimited_plan_details(self):
        """Test getting unlimited plan details."""
        plan_details = get_plan_details("unlimited")
        
        assert plan_details["name"] == "unlimited"
        assert plan_details["price"] == 25
        assert plan_details["emails"] is None  # Unlimited
        assert plan_details["description"] == "Unlimited plan with unlimited emails"
    
    def test_get_invalid_plan_details(self):
        """Test getting invalid plan details raises ValueError."""
        with pytest.raises(ValueError, match="Unknown plan: invalid"):
            get_plan_details("invalid")


class TestEmailLimitCalculation:
    """Test email limit calculation functionality."""
    
    def test_calculate_starter_plan_limit_no_addons(self):
        """Test calculating email limit for starter plan without add-ons."""
        limit = calculate_email_limit("starter", addon_packs=0)
        assert limit == 100
    
    def test_calculate_professional_plan_limit_no_addons(self):
        """Test calculating email limit for professional plan without add-ons."""
        limit = calculate_email_limit("professional", addon_packs=0)
        assert limit == 500
    
    def test_calculate_unlimited_plan_limit(self):
        """Test calculating email limit for unlimited plan."""
        limit = calculate_email_limit("unlimited", addon_packs=0)
        assert limit is None  # Unlimited
    
    def test_calculate_starter_plan_with_addons(self):
        """Test calculating email limit for starter plan with add-on packs."""
        limit = calculate_email_limit("starter", addon_packs=2)
        # 100 (base) + 2 * 50 (add-ons) = 200
        assert limit == 200
    
    def test_calculate_professional_plan_with_addons(self):
        """Test calculating email limit for professional plan with add-on packs."""
        limit = calculate_email_limit("professional", addon_packs=3)
        # 500 (base) + 3 * 50 (add-ons) = 650
        assert limit == 650
    
    def test_calculate_unlimited_plan_ignores_addons(self):
        """Test that unlimited plan ignores add-on packs."""
        limit = calculate_email_limit("unlimited", addon_packs=5)
        assert limit is None  # Still unlimited
    
    def test_calculate_invalid_plan_raises_error(self):
        """Test that invalid plan names raise ValueError."""
        with pytest.raises(ValueError, match="Unknown plan: invalid"):
            calculate_email_limit("invalid", addon_packs=0)


class TestUsagePercentageCalculation:
    """Test usage percentage calculation functionality."""
    
    def test_calculate_usage_percentage_starter_plan(self):
        """Test calculating usage percentage for starter plan."""
        percentage = calculate_usage_percentage("starter", emails_used=50, addon_packs=0)
        assert percentage == 50.0  # 50/100 = 50%
    
    def test_calculate_usage_percentage_professional_plan(self):
        """Test calculating usage percentage for professional plan.""" 
        percentage = calculate_usage_percentage("professional", emails_used=250, addon_packs=0)
        assert percentage == 50.0  # 250/500 = 50%
    
    def test_calculate_usage_percentage_with_addons(self):
        """Test calculating usage percentage with add-on packs."""
        # Starter (100) + 2 add-ons (100) = 200 total
        percentage = calculate_usage_percentage("starter", emails_used=100, addon_packs=2)
        assert percentage == 50.0  # 100/200 = 50%
    
    def test_calculate_usage_percentage_over_limit(self):
        """Test calculating usage percentage when over limit."""
        percentage = calculate_usage_percentage("starter", emails_used=150, addon_packs=0)
        assert percentage == 150.0  # 150/100 = 150%
    
    def test_calculate_usage_percentage_unlimited_plan(self):
        """Test calculating usage percentage for unlimited plan."""
        percentage = calculate_usage_percentage("unlimited", emails_used=1000, addon_packs=0)
        assert percentage == 0.0  # Unlimited plans always return 0%
    
    def test_calculate_usage_percentage_zero_usage(self):
        """Test calculating usage percentage with zero usage."""
        percentage = calculate_usage_percentage("starter", emails_used=0, addon_packs=0)
        assert percentage == 0.0  # 0/100 = 0%
    
    def test_calculate_usage_percentage_invalid_plan(self):
        """Test that invalid plan names raise ValueError."""
        with pytest.raises(ValueError, match="Unknown plan: invalid"):
            calculate_usage_percentage("invalid", emails_used=50, addon_packs=0)


class TestAddonPackConfiguration:
    """Test add-on pack configuration functionality."""
    
    def test_get_addon_pack_details(self):
        """Test getting add-on pack details."""
        details = get_addon_pack_details()
        
        assert details["price"] == 2
        assert details["emails"] == 50
        assert details["description"] == "Add-on pack with 50 additional emails"
    
    def test_calculate_addon_cost_single_pack(self):
        """Test calculating cost for single add-on pack."""
        details = get_addon_pack_details()
        cost = details["price"] * 1
        assert cost == 2
    
    def test_calculate_addon_cost_multiple_packs(self):
        """Test calculating cost for multiple add-on packs."""
        details = get_addon_pack_details()
        cost = details["price"] * 5
        assert cost == 10  # 5 * $2 = $10
    
    def test_calculate_addon_emails_single_pack(self):
        """Test calculating emails for single add-on pack."""
        details = get_addon_pack_details()
        emails = details["emails"] * 1
        assert emails == 50
    
    def test_calculate_addon_emails_multiple_packs(self):
        """Test calculating emails for multiple add-on packs."""
        details = get_addon_pack_details()
        emails = details["emails"] * 3
        assert emails == 150  # 3 * 50 = 150


class TestTrialPeriodConfiguration:
    """Test trial period configuration functionality."""
    
    def test_get_trial_period_details(self):
        """Test getting trial period details."""
        details = get_trial_period_details()
        
        assert details["days"] == 30
        assert details["description"] == "30-day free trial period"
        assert details["email_limit"] == 100  # Should default to starter plan limit
    
    def test_trial_period_with_custom_limit(self):
        """Test getting trial period details with custom email limit.""" 
        details = get_trial_period_details(email_limit=250)
        
        assert details["days"] == 30
        assert details["description"] == "30-day free trial period"
        assert details["email_limit"] == 250