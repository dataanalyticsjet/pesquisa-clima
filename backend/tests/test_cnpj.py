import pytest

from app.services.cnpj import normalize_cnpj, validate_cnpj


@pytest.mark.parametrize("value", ["11222333000181", "11.222.333/0001-81"])
def test_numeric_cnpj_is_valid_with_or_without_mask(value):
    assert validate_cnpj(value) is True


def test_numeric_cnpj_normalizes_mask():
    assert normalize_cnpj("11.222.333/0001-81") == "11222333000181"


@pytest.mark.parametrize("value", ["00000000E08G12", "00.000.000/E08G-12"])
def test_alphanumeric_cnpj_is_valid_with_or_without_mask(value):
    assert validate_cnpj(value) is True


def test_alphanumeric_cnpj_normalizes_to_uppercase():
    assert normalize_cnpj("00.000.000/e08g-12") == "00000000E08G12"


@pytest.mark.parametrize("value", ["123", "00.000.000/E08G-1X", "00.000.000/E08@-12", "00.000.000/E08G-13"])
def test_invalid_cnpj_length_characters_and_check_digits_are_rejected(value):
    assert validate_cnpj(value) is False
    if value != "00.000.000/E08G-13":
        with pytest.raises(ValueError):
            normalize_cnpj(value)
