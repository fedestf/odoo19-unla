"""Consulta de solo lectura para confirmar las restricciones después de actualizar."""

expected = {
    "estate_property_tag_unique_tag_name",
    "estate_property_type_unique_type_name",
    "estate_property_offer_unique_partner_property",
}
env.cr.execute("""
    SELECT conname FROM pg_constraint
    WHERE connamespace = current_schema()::regnamespace
      AND conname = ANY(%s)
""", (list(expected),))
found = {row[0] for row in env.cr.fetchall()}
env.cr.rollback()
print("Restricciones encontradas:", sorted(found))
if expected - found:
    raise SystemExit("Faltan restricciones: " + ", ".join(sorted(expected - found)))
print("Las tres restricciones de unicidad están instaladas.")
