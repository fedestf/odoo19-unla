# Unidad 2 — Implementación completa y validación final

Estado: **27/27 puntos implementados en código y documentados**. Se conservan **15/27 puntos validados mediante las capturas previas**. La aceptación del punto 16, la cinta Vendida y las pruebas integradas de los puntos restantes necesitan ejecución en la VM. No se consideran pruebas ORM aprobadas por haber pasado pruebas aisladas.

## Qué se agregó

| Punto | Implementación y concepto |
| --- | --- |
| 16 | Aceptar una oferta asigna comprador/precio, cambia la propiedad a Oferta aceptada y rechaza las demás. |
| 17 | Unicidad SQL de nombres de etiquetas y tipos. En Odoo 19 se usa `models.Constraint`, en lugar del `_sql_constraints` del PDF. `UNIQUE(name)` distingue mayúsculas/minúsculas y espacios. |
| 18 | `UNIQUE(partner_id, property_id)` permite un ofertante por propiedad; el mismo contacto puede ofertar por otras propiedades. |
| 19 | `offer_partner_ids` es Many2many computado desde `offer_ids.mapped('partner_id')`. La colección representa los contactos sin repetirlos. Un `related` no es adecuado para agregar colecciones atravesando un One2many. |
| 20 | Oferta automática: contacto activo que aún no ofertó e importe aleatorio dentro de ±30% del precio esperado. Se limita también a superar la mejor oferta, como requiere el punto 23. Si no hay contacto o importe posible, informa con UserError. |
| 21 | `Command.clear()` desvincula etiquetas; `Command.set(ids)` carga todas; `Command.link(id)` agrega A estrenar conservando las demás. Si A estrenar no existe, se crea una sola vez. No se borran los registros de etiquetas al desvincular. |
| 22 | `@api.ondelete(at_uninstall=False)` permite borrar solo propiedades nuevas o canceladas. Se evita interferir con la desinstalación del módulo, algo que un override de unlink sin cuidados podría impedir. La FK sigue impidiendo borrar una propiedad que conserva ofertas. |
| 23 | `create` con `@api.model_create_multi` valida precio estrictamente superior al máximo actual y estado Nuevo/Oferta recibida. Después crea y pasa la propiedad a Oferta recibida. Un lote se compara también contra sus precios anteriores. Se llama a super y se respetan ACL. |
| 24 | Herencia de res.users: `property_ids` One2many inverso a salesman_id. No hay modelo ni tabla nuevos, así que no se agregan ACL de un modelo nuevo; siguen vigentes las de usuarios y propiedades. |
| 25 | Vista heredada de `base.view_users_form`, XPath al notebook y página Propiedades de solo lectura. Se muestra a grupos inmobiliarios que además puedan entrar a la ficha de usuarios. |
| 26 | Nuevo módulo estate_account con dependencias real_estate y account. Su instalación debe ejecutarse en la VM. |
| 27 | Herencia de estate.property: action_sold llama a super y crea factura de cliente en borrador, con comprador, una línea de venta y otra de 100 por gastos administrativos. |

## Facturación: comportamiento concreto

- Las líneas se crean mediante `Command.create` en `invoice_line_ids`, el subconjunto de líneas de factura de `line_ids` de account.move. Odoo genera las contrapartidas contables. Evita crear manualmente líneas de diario incompletas.
- La factura queda en **borrador**. El código no la publica, envía, cobra ni crea movimientos bancarios.
- La línea de venta tiene nombre de la propiedad, cantidad 1 y precio unitario selling_price. Gastos administrativos tiene cantidad 1 y precio unitario 100.
- La compañía y moneda son las de la compañía activa. Se necesita un diario de ventas y una cuenta de ingresos; no se crean ni alteran automáticamente configuraciones fiscales.
- El usuario necesita acceso inmobiliario y permisos de facturación. No se usa sudo en el código de negocio para eludirlos.
- Se exige comprador y precio de venta positivo al vender con estate_account instalado.
- Más info. muestra Factura de venta a usuarios con acceso de facturación. Repetir la venta ya completada no genera otra factura en el flujo secuencial habitual. La factura no se copia al duplicar la propiedad.
- Las propiedades que ya estaban vendidas antes de instalar el módulo no se facturan retroactivamente.
- Si falla la creación de factura, la petición revierte también el cambio de estado por la transacción de Odoo. Las pruebas de esta transacción requieren PostgreSQL/Odoo; no están cubiertas por dobles aislados.

## Actualizar en Ubuntu sin borrar datos

1. Guardar trabajo abierto en Odoo. En terminal:

```bash
cd ~/odoo19
git pull --ff-only
docker compose stop odoo
```

2. Comprobar duplicados existentes, sin modificar datos:

```bash
docker compose run --rm -T odoo odoo shell -d devel --no-http < scripts/check_unit2_data.py
```

Debe indicar OK en etiquetas, tipos y ofertante por propiedad. Si encuentra duplicados, muestra los IDs y se detiene. Revisarlos desde la interfaz antes de continuar: no borrarlos a ciegas ni resetear la base. Para volver a la interfaz usar `invoke start`, resolverlos y luego detener Odoo de nuevo. El código no renombra ni elimina registros existentes.

3. Actualizar el módulo e instalar la extensión contable:

```bash
docker compose run --rm odoo odoo -d devel -u real_estate -i estate_account --stop-after-init
```

Si hay un error, detenerse y conservar la salida. Instalar account puede requerir completar su configuración contable desde la interfaz antes de probar la venta.

4. Confirmar que se crearon las tres restricciones y arrancar:

```bash
docker compose run --rm -T odoo odoo shell -d devel --no-http < scripts/verify_unit2_constraints.py
invoke start
```

Si faltan restricciones, revisar duplicados y logs; no dar la actualización por validada solo porque terminó sin excepción. Recargar Odoo con Ctrl+Shift+R.

## Recorrido final de prueba

Crear datos nuevos de prueba, conservando los ejemplos anteriores:

1. Crear una propiedad con precio esperado 100000 y vendedor actual. Asignar dos etiquetas.
2. Crear oferta 50000 de un contacto y luego 65000 de otro. Debe pasar a Oferta recibida; Mejor oferta 65000 y ambos Ofertantes deben aparecer.
3. Intentar 64000 de un tercero: error de precio. Intentar 70000 del primer contacto: error de unicidad. La persona puede ofertar en otra propiedad nueva.
4. Generar oferta automática: debe provenir de un contacto nuevo y superar el máximo sin salir de 70000–130000. Si ya no queda margen, debe explicar que no es posible.
5. Aceptar una oferta: elegida Aceptada, otras Rechazadas; comprador/precio deben coincidir y el estado pasar a Oferta aceptada. Intentar otra nueva oferta debe fallar por estado.
6. En etiquetas, probar Sacar etiquetas, Cargar todas y dos clics en A estrenar. Debe existir una sola etiqueta A estrenar. Intentar duplicar exactamente un nombre de etiqueta o tipo debe dar error.
7. Abrir Ajustes → Usuarios y compañías → Usuarios, elegir el vendedor y revisar Propiedades. La propiedad asignada debe aparecer y la colección no permitir creación directa.
8. Intentar borrar una propiedad con Oferta recibida o aceptada: UserError. Probar borrar una nueva sin ofertas y una cancelada sin ofertas: permitido. Las nuevas/canceladas con ofertas conservan la protección de FK: quitar ofertas antes de borrar.
9. Configurar Facturación y dar los permisos necesarios al usuario de prueba. Marcar vendida la propiedad con comprador/precio. Revisar cinta Vendida y Factura de venta en Más info.
10. Abrir la factura: borrador, cliente correcto y dos líneas con cantidades 1, precio de venta y 100. Repetir Marcar como vendida no debe crear otra factura. Cancelar la propiedad vendida debe dar UserError.

## Pruebas automatizadas

Ejecutadas en el equipo de desarrollo: sintaxis Python/XML y **10 pruebas aisladas** que cargan métodos reales con dobles del ORM: aceptación, ofertas crecientes, lotes, estados cerrados, generación dentro del rango, rango imposible, borrado, factura e idempotencia secuencial. Repetibles sin Odoo:

```bash
python3 scripts/test_unit2_logic.py
```

Estas pruebas no comprueban PostgreSQL, la instalación de módulos, permisos efectivos, vistas renderizadas ni asientos contables. Se incluyen **12 pruebas de integración** (10 inmobiliarias y 2 contables) para ejecutar sobre una **base de prueba nueva**, nunca devel:

```bash
docker compose run --rm odoo odoo -d unidad2_test -i estate_account --test-enable --test-tags /real_estate,/estate_account --without-demo=all --stop-after-init
```

Se necesita poder crear esa base de prueba. No usar resetdb ni borrar la base de trabajo. Las pruebas de integración están preparadas pero no ejecutadas en este equipo: no dispone de Docker ni de Odoo/PostgreSQL. Solo la salida real de la VM permite declararlas aprobadas.

## Referencias y diferencias con la guía

- Odoo 19 usa `models.Constraint` para las restricciones SQL. El objetivo de los puntos 17 y 18 se mantiene.
- Se hereda la vista de usuarios, sin reemplazar su XML completo.
- La herencia contable mantiene el método original mediante super. No requiere nuevas ACL para estate.property porque extiende el mismo modelo.
- La generación aleatoria del punto 20 debe convivir con la restricción de máximos del punto 23: no se evita la validación ni se altera la mejor oferta anterior para hacerla pasar.
- Fuentes técnicas oficiales: [restricciones](https://github.com/odoo/odoo/blob/19.0/odoo/orm/table_objects.py), [decoradores](https://github.com/odoo/odoo/blob/19.0/odoo/orm/decorators.py), [vista de usuarios](https://github.com/odoo/odoo/blob/19.0/odoo/addons/base/views/res_users_views.xml), [facturas y líneas](https://github.com/odoo/odoo/blob/19.0/addons/account/models/account_move.py).
