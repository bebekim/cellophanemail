"""
Pricing configuration constants for CellophoneMail.
All pricing values are in USD.
"""

# Starter Plan Configuration
STARTER_PRICE = 1
STARTER_EMAILS = 50

# Plus Plan Configuration  
PLUS_PRICE = 2
PLUS_EMAILS = 150

# Professional Plan Configuration
PROFESSIONAL_PRICE = 5
PROFESSIONAL_EMAILS = 500

# Add-on Pack Configuration
ADDON_PACK_PRICE = 2
ADDON_PACK_EMAILS = 50

# Trial Period Configuration
TRIAL_PERIOD_DAYS = 30

# Plan Configuration Map
PLAN_CONFIGS = {
    "starter": {
        "price": STARTER_PRICE,
        "emails": STARTER_EMAILS,
        "description": f"Starter plan with {STARTER_EMAILS} emails"
    },
    "plus": {
        "price": PLUS_PRICE,
        "emails": PLUS_EMAILS,
        "description": f"Plus plan with {PLUS_EMAILS} emails"
    },
    "professional": {
        "price": PROFESSIONAL_PRICE,
        "emails": PROFESSIONAL_EMAILS,
        "description": f"Professional plan with {PROFESSIONAL_EMAILS} emails"
    }
}


def _validate_plan_name(plan_name: str) -> str:
    """
    Validate and normalize plan name.
    
    Args:
        plan_name: Plan name to validate
        
    Returns:
        Normalized plan name
        
    Raises:
        ValueError: If plan_name is not recognized
    """
    normalized_name = plan_name.lower()
    if normalized_name not in PLAN_CONFIGS:
        raise ValueError(f"Unknown plan: {plan_name}")
    return normalized_name


def get_plan_details(plan_name: str) -> dict:
    """
    Get plan details for a given plan name.
    
    Args:
        plan_name: Name of the plan ("starter", "plus", "professional")
        
    Returns:
        Dictionary containing plan details
        
    Raises:
        ValueError: If plan_name is not recognized
    """
    normalized_name = _validate_plan_name(plan_name)
    plan_config = PLAN_CONFIGS[normalized_name].copy()
    plan_config["name"] = normalized_name
    return plan_config


def calculate_email_limit(plan_name: str, addon_packs: int = 0) -> int:
    """
    Calculate the total email limit for a plan including add-on packs.
    
    Args:
        plan_name: Name of the plan ("starter", "plus", "professional")
        addon_packs: Number of add-on packs purchased
        
    Returns:
        Total email limit
        
    Raises:
        ValueError: If plan_name is not recognized
    """
    normalized_name = _validate_plan_name(plan_name)
    base_emails = PLAN_CONFIGS[normalized_name]["emails"]
    
    return base_emails + (addon_packs * ADDON_PACK_EMAILS)


def calculate_usage_percentage(plan_name: str, emails_used: int, addon_packs: int = 0) -> float:
    """
    Calculate the usage percentage for a given plan and usage.
    
    Args:
        plan_name: Name of the plan ("starter", "plus", "professional")
        emails_used: Number of emails used
        addon_packs: Number of add-on packs purchased
        
    Returns:
        Usage percentage as a float (0.0 to 100.0+)
        
    Raises:
        ValueError: If plan_name is not recognized
    """
    email_limit = calculate_email_limit(plan_name, addon_packs)
    return (emails_used / email_limit) * 100.0


def get_addon_pack_details() -> dict:
    """
    Get add-on pack details.
    
    Returns:
        Dictionary containing add-on pack details
    """
    return {
        "price": ADDON_PACK_PRICE,
        "emails": ADDON_PACK_EMAILS,
        "description": f"Add-on pack with {ADDON_PACK_EMAILS} additional emails"
    }


def get_trial_period_details(email_limit: int | None = None) -> dict:
    """
    Get trial period details.
    
    Args:
        email_limit: Custom email limit for trial period (defaults to starter plan limit)
        
    Returns:
        Dictionary containing trial period details
    """
    if email_limit is None:
        email_limit = STARTER_EMAILS  # Default to starter plan limit
        
    return {
        "days": TRIAL_PERIOD_DAYS,
        "description": f"{TRIAL_PERIOD_DAYS}-day free trial period",
        "email_limit": email_limit
    }