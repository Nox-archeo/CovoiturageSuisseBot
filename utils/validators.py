from datetime import datetime

def validate_date(date_str):
    """Valide le format de la date"""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y %H:%M")
    except ValueError:
        return None

def validate_price(price_str):
    """Valide le prix"""
    try:
        price = float(price_str)
        return price if 0 < price <= 1000 else None
    except ValueError:
        return None

def validate_seats(seats_str):
    """Valide le nombre de places"""
    try:
        seats = int(seats_str)
        return seats if 0 < seats <= 8 else None
    except ValueError:
        return None
