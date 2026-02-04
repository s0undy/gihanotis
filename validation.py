"""
Input validation utilities for GiHaNotis
Provides validation functions for user input
"""

import re
from typing import Dict, Any, Optional


class ValidationError(ValueError):
    """Custom exception for validation errors"""
    pass


def validate_request_data(data: Dict[str, Any]) -> None:
    """
    Validate request creation/update data.

    Args:
        data: Dictionary containing request fields

    Raises:
        ValidationError: If validation fails
    """
    # Item name validation
    if 'item_name' in data:
        item_name = data['item_name']
        if not item_name or not item_name.strip():
            raise ValidationError("Item name cannot be empty")
        if len(item_name) > 255:
            raise ValidationError("Item name too long (max 255 characters)")
        if len(item_name) < 2:
            raise ValidationError("Item name too short (min 2 characters)")
        # Sanitize HTML to prevent XSS
        data['item_name'] = sanitize_html(item_name)

    # Quantity validation
    if 'quantity_needed' in data:
        quantity = data['quantity_needed']
        if not isinstance(quantity, int):
            raise ValidationError("Quantity must be an integer")
        if quantity < 0:
            raise ValidationError("Quantity cannot be negative")
        if quantity > 1000000:
            raise ValidationError("Quantity too large (max 1,000,000)")

    # Unit validation
    if 'unit' in data:
        unit = data['unit']
        if not unit or not unit.strip():
            raise ValidationError("Unit cannot be empty")
        if len(unit) > 50:
            raise ValidationError("Unit too long (max 50 characters)")

    # Description validation
    if 'description' in data and data['description']:
        description = data['description']
        if len(description) > 5000:
            raise ValidationError("Description too long (max 5000 characters)")
        # Sanitize HTML to prevent XSS
        data['description'] = sanitize_html(description)


def validate_response_data(data: Dict[str, Any]) -> None:
    """
    Validate response submission data.

    Args:
        data: Dictionary containing response fields

    Raises:
        ValidationError: If validation fails
    """
    # Quantity validation
    if 'quantity_available' in data:
        quantity = data['quantity_available']
        if not isinstance(quantity, int):
            raise ValidationError("Quantity must be an integer")
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")
        if quantity > 1000000:
            raise ValidationError("Quantity too large (max 1,000,000)")

    # Location validation
    if 'location' in data:
        location = data['location']
        if not location or not location.strip():
            raise ValidationError("Location cannot be empty")
        if len(location) > 500:
            raise ValidationError("Location too long (max 500 characters)")
        if len(location) < 3:
            raise ValidationError("Location too short (min 3 characters)")
        # Sanitize HTML to prevent XSS
        data['location'] = sanitize_html(location)

    # Name validation
    if 'responder_name' in data and data['responder_name']:
        name = data['responder_name']
        if len(name) > 255:
            raise ValidationError("Name too long (max 255 characters)")
        # Sanitize HTML to prevent XSS
        data['responder_name'] = sanitize_html(name)

    # Contact validation
    if 'responder_contact' in data and data['responder_contact']:
        contact = data['responder_contact']
        if len(contact) > 255:
            raise ValidationError("Contact info too long (max 255 characters)")

    # Notes validation
    if 'notes' in data and data['notes']:
        notes = data['notes']
        if len(notes) > 2000:
            raise ValidationError("Notes too long (max 2000 characters)")
        # Sanitize HTML to prevent XSS
        data['notes'] = sanitize_html(notes)


def sanitize_html(text: Optional[str]) -> Optional[str]:
    """
    Basic HTML sanitization - removes potentially dangerous characters.
    Note: Jinja2 auto-escapes by default, but this adds extra protection.

    Args:
        text: Input text

    Returns:
        Sanitized text or None
    """
    if not text:
        return text

    # Remove any potential script tags or HTML
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'javascript:',
        r'onerror=',
        r'onload=',
    ]

    result = text
    for pattern in dangerous_patterns:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE | re.DOTALL)

    return result


def validate_pagination_params(page: Any, per_page: Any) -> tuple[int, int]:
    """
    Validate and sanitize pagination parameters.

    Args:
        page: Page number (as string or int)
        per_page: Items per page (as string or int)

    Returns:
        Tuple of (page, per_page) as integers

    Raises:
        ValidationError: If validation fails
    """
    try:
        page = int(page) if page else 1
        per_page = int(per_page) if per_page else 50
    except (ValueError, TypeError):
        raise ValidationError("Invalid pagination parameters")

    if page < 1:
        raise ValidationError("Page must be >= 1")
    if per_page < 1 or per_page > 100:
        raise ValidationError("Per page must be between 1 and 100")

    return page, per_page
