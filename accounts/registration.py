"""Caso de uso CU-01 y CU-02: crear la cuenta de un cliente, en la web o en la tienda."""


def normalize_phone(text):
    """Deja solo los dígitos del teléfono: «7123-4567» y «71234567» son el mismo número."""
    return "".join(character for character in text if character.isdigit())
