from decimal import Decimal, InvalidOperation


def required(value, field_name):
    if not str(value or "").strip():
        raise ValueError(f"{field_name} wajib diisi.")
    return str(value).strip()


def non_negative_decimal(value, field_name):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} harus berupa angka.") from exc
    if result < 0:
        raise ValueError(f"{field_name} tidak boleh negatif.")
    return result


def non_negative_int(value, field_name):
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} harus berupa bilangan bulat.") from exc
    if result < 0:
        raise ValueError(f"{field_name} tidak boleh negatif.")
    return result


def validate_prices(purchase_price, selling_price):
    purchase = non_negative_decimal(purchase_price, "Harga beli")
    selling = non_negative_decimal(selling_price, "Harga jual")
    if selling < purchase:
        raise ValueError("Harga jual tidak boleh lebih kecil dari harga beli.")
    return purchase, selling
