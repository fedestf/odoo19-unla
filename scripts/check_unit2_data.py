"""Ejecutar con odoo shell: solo consulta datos, nunca modifica registros."""

checks = [
    ("Etiquetas duplicadas", """
        SELECT name, array_agg(id ORDER BY id), count(*)
        FROM estate_property_tag GROUP BY name HAVING count(*) > 1
    """),
    ("Tipos duplicados", """
        SELECT name, array_agg(id ORDER BY id), count(*)
        FROM estate_property_type GROUP BY name HAVING count(*) > 1
    """),
    ("Ofertante repetido por propiedad", """
        SELECT partner_id, property_id, array_agg(id ORDER BY id), count(*)
        FROM estate_property_offer
        GROUP BY partner_id, property_id HAVING count(*) > 1
    """),
]
conflicts = False
for label, query in checks:
    env.cr.execute(query)
    rows = env.cr.fetchall()
    print(label, rows if rows else "OK")
    conflicts = conflicts or bool(rows)
env.cr.rollback()
if conflicts:
    raise SystemExit("Revisar duplicados antes de actualizar. No se modificó ningún registro.")
print("Sin duplicados incompatibles con las nuevas restricciones.")
