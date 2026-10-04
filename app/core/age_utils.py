"""
Account tier logic — determines what a user can and cannot do based
on their age. Used at registration and enforced across the app.
"""

from datetime import date

# Age thresholds
MIN_AGE_FOR_ADULT = 18
MIN_AGE_FOR_TEEN = 13


def calculate_age(dob: date) -> int:
    """Calculate current age from date of birth."""
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def classify_account(dob: date) -> str:
    """Return 'child' | 'teen' | 'adult'."""
    age = calculate_age(dob)
    if age < MIN_AGE_FOR_TEEN:
        return "child"
    if age < MIN_AGE_FOR_ADULT:
        return "teen"
    return "adult"


def tier_message(tier: str) -> str:
    """Human-readable description of what each tier means."""
    messages = {
        "child": (
            "You'll be signed up as a child account. This includes safety features: "
            "restricted content, Kids focus mode, and no access to communities or stitch projects."
        ),
        "teen": (
            "You'll be signed up as a teen account. You get the full app with "
            "age-appropriate content restrictions."
        ),
        "adult": "You'll have full access to the platform.",
    }
    return messages.get(tier, "")


def is_child_account(dob: date | None) -> bool:
    """Convenience: is this a child account?"""
    if dob is None:
        return False
    return classify_account(dob) == "child"
