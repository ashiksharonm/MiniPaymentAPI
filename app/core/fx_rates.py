"""
Static FX (Foreign Exchange) Rates.

IMPORTANT: These are hardcoded rates for demonstration purposes only.
In production, rates would be fetched from a real FX provider (e.g., XE, Open Exchange Rates).

Last updated: 2024-01-27 (fictional rates for demo)
"""
from decimal import Decimal
from typing import Optional


# Static exchange rates mapping
# Format: FX_RATES[source_currency][target_currency] = rate
FX_RATES: dict[str, dict[str, Decimal]] = {
    "USD": {
        "INR": Decimal("83.00"),
        "EUR": Decimal("0.92"),
        "GBP": Decimal("0.79"),
        "USD": Decimal("1.00"),
    },
    "EUR": {
        "USD": Decimal("1.08"),
        "INR": Decimal("89.64"),
        "GBP": Decimal("0.86"),
        "EUR": Decimal("1.00"),
    },
    "INR": {
        "USD": Decimal("0.012"),
        "EUR": Decimal("0.011"),
        "GBP": Decimal("0.0095"),
        "INR": Decimal("1.00"),
    },
    "GBP": {
        "USD": Decimal("1.27"),
        "EUR": Decimal("1.16"),
        "INR": Decimal("105.26"),
        "GBP": Decimal("1.00"),
    },
}

# Supported currencies for validation
SUPPORTED_CURRENCIES: set[str] = {"USD", "EUR", "INR", "GBP"}


def get_fx_rate(source_currency: str, target_currency: str) -> Optional[Decimal]:
    """
    Get the exchange rate for converting from source to target currency.
    
    Args:
        source_currency: The currency to convert from (e.g., "USD")
        target_currency: The currency to convert to (e.g., "INR")
        
    Returns:
        The exchange rate as a Decimal, or None if the pair is not supported.
    """
    source_upper = source_currency.upper()
    target_upper = target_currency.upper()
    
    if source_upper not in FX_RATES:
        return None
    if target_upper not in FX_RATES[source_upper]:
        return None
    
    return FX_RATES[source_upper][target_upper]


def convert_currency(
    amount: Decimal, 
    source_currency: str, 
    target_currency: str
) -> tuple[Optional[Decimal], Optional[Decimal]]:
    """
    Convert an amount from source currency to target currency.
    
    Args:
        amount: The amount to convert
        source_currency: The currency to convert from
        target_currency: The currency to convert to
        
    Returns:
        A tuple of (converted_amount, fx_rate) or (None, None) if conversion fails.
    """
    rate = get_fx_rate(source_currency, target_currency)
    if rate is None:
        return None, None
    
    converted = amount * rate
    # Round to 2 decimal places for currency
    converted = converted.quantize(Decimal("0.01"))
    
    return converted, rate


def is_currency_supported(currency: str) -> bool:
    """Check if a currency is supported."""
    return currency.upper() in SUPPORTED_CURRENCIES
