import re


def normalize_phone(phone: str | None) -> str | None:
    """
    formats phone as 380XXXXXXXXX.
    Removes +, spaces, parentheses.
    """
    if phone is None:
        return None

    clean = re.sub(r'[^\d]', '', phone)
    if clean.startswith('0') and len(clean) == 10:  # 050 -> 38050
        clean = '38' + clean
    return clean


def normalize_plate(plate: str) -> str:
    """
    Replaces Ukrainian symbols to english ones.
    Cleans string.
    """
    if not plate:
        return ""

    # Спочатку чистимо від сміття
    plate = plate.upper().strip().replace(" ", "").replace("-", "")

    # Словник замін (Кирилиця -> Латиниця)
    mapping = {
        'А': 'A',
        'В': 'B',
        'Е': 'E',
        'І': 'I',
        'К': 'K',
        'М': 'M',
        'Н': 'H',
        'О': 'O',
        'Р': 'P',
        'С': 'C',
        'Т': 'T',
        'У': 'Y',
        'Х': 'X',
        'Y': 'Y',
    }

    table = str.maketrans(mapping)
    return plate.translate(table)
