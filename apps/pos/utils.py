from datetime import datetime


def generate_invoice_number(sales_collection):
    year = datetime.now().year

    prefix = f"INV-{year}-"

    last_sale = sales_collection.find_one(
        {
            "invoiceNumber": {
                "$regex": f"^{prefix}"
            }
        },
        sort=[
            ("invoiceNumber", -1)
        ]
    )

    if not last_sale:
        number = 1
    else:
        last_invoice = last_sale.get(
            "invoiceNumber",
            ""
        )

        try:
            number = int(
                last_invoice.split("-")[-1]
            ) + 1
        except (ValueError, IndexError):
            number = 1

    return f"{prefix}{number:04d}"