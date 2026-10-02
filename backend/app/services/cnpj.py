import re


_MASK_CHARACTERS = re.compile(r"[.\-/\s]")
_CNPJ_BODY = re.compile(r"^[A-Z0-9]{12}$")
_CNPJ_CHECK_DIGITS = re.compile(r"^[0-9]{2}$")


def normalize_cnpj(value: str) -> str:
    """Remove CNPJ mask separators and spaces, uppercase, and require 14 valid characters."""
    normalized = _MASK_CHARACTERS.sub("", value).upper()
    if len(normalized) != 14 or not _CNPJ_BODY.fullmatch(normalized[:12]) or not _CNPJ_CHECK_DIGITS.fullmatch(normalized[12:]):
        raise ValueError("invalid CNPJ format")
    return normalized


def _calculate_check_digit(body: str) -> int:
    total = sum(
        (ord(character) - 48) * ((len(body) - index - 1) % 8 + 2)
        for index, character in enumerate(body)
    )
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def validate_cnpj(value: str) -> bool:
    """Validate both CNPJ formats using Receita Federal's ASCII-minus-48 mod-11 rule."""
    try:
        normalized = normalize_cnpj(value)
    except (AttributeError, TypeError, ValueError):
        return False

    first_digit = _calculate_check_digit(normalized[:12])
    second_digit = _calculate_check_digit(normalized[:12] + str(first_digit))
    return normalized[12:] == f"{first_digit}{second_digit}"
