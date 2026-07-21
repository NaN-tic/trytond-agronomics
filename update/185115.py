if "pool" not in globals():
    # Prevent pyflakes warnings when the script is not executed by Tryton.
    pool = None
    transaction = None


Template = pool.get("product.template")

location_types = [
    value for value, _label in Template.lot_required.selection]
templates = Template.search([
        ("producible", "=", True),
        ("active", "in", [True, False]),
        ])

Template.write(templates, {
        "lot_required": location_types,
        })
transaction.commit()
