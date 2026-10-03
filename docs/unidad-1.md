# Unidad 1 — Guía de estudio con Odoo 19 Community

Se conserva el orden de la guía de la cátedra versión 20250927b, usando Odoo 19 en lugar de Odoo 18.

## Punto 1 — Entorno Doodba

Estado: validado en la práctica.

Doodba organiza Odoo, PostgreSQL y herramientas de desarrollo mediante contenedores. Se verificó acceso a Odoo, MailHog, wdb y pgweb. El código se versiona con Git; la base de datos requiere respaldos separados. Reiniciar el servicio no equivale a recrear la base.

## Punto 2 — Módulo real_estate

Estado: instalado y validado.

Ubicación: odoo/custom/src/private/real_estate. En Doodba, private contiene los módulos propios.

__manifest__.py declara nombre, versión, dependencias y archivos de datos. __init__.py carga el código Python. El módulo se llama Inmobiliaria y depende de base. Un módulo instalado sin menús todavía no ofrece navegación propia.

## Punto 3 — Modelo estate.property

Estado: tabla verificada en pgweb.

La clase hereda models.Model. _name identifica el modelo; _description lo describe. El init del módulo importa models; models/__init__.py importa estate_property.

| Campo | Tipo | Particularidad |
| --- | --- | --- |
| name | Char | Obligatorio |
| description | Text | Descripción |
| postcode | Char | Código postal |
| date_availability | Date | Disponibilidad |
| expected_price | Float | Precio esperado |
| selling_price | Float | Precio de venta |
| bedrooms | Integer | default=2 |
| living_area | Integer | Superficie cubierta |
| facades | Integer | Fachadas |
| garage | Boolean | Garage |
| garden | Boolean | Jardín |
| garden_orientation | Selection | north/south/east/west; default=north |
| garden_area | Integer | Superficie jardín |

Actualizar el módulo incorpora el modelo a la base. estate.property genera la tabla estate_property.

## Punto 4 — Campos automáticos

Estado: observado en pgweb.

Además de los 13 campos propios, Odoo agregó id, create_uid, create_date, write_uid y write_date.

id identifica el registro. Los otros cuatro registran quién creó/modificó y cuándo. Odoo los administra automáticamente. Un default del ORM no necesariamente aparece como DEFAULT de PostgreSQL.

## Punto 5 — Acción Propiedades

Estado: validado mediante el formulario de Acciones de ventana.

Archivo: views/estate_property_views.xml, incluido en data del manifest.

| Atributo | Valor |
| --- | --- |
| ID externo | real_estate.estate_property_action |
| Tipo | ir.actions.act_window |
| Nombre | Propiedades |
| Modelo | estate.property |
| view_mode | list,form |

Una acción indica qué abrir y qué modos ofrecer. Una vista define cómo mostrarlo. No se crearon vistas personalizadas en este punto.

Para inspeccionar: modo desarrollador > Ajustes > Técnico > Acciones > Acciones de ventana. La lista general de Acciones ofrece menos detalles.

## Punto 6 — Menús

Estado: código preparado; actualización y validación en Odoo pendientes.

Archivo: views/real_estate_menuitem.xml.

Jerarquía: Inmobiliaria > Anuncios > Propiedades.

- real_estate_menu_root: menú raíz.
- real_estate_menu_announcements: hijo del menú raíz.
- real_estate_menu_properties: hijo de Anuncios y asociado a estate_property_action.

parent construye la jerarquía y action vincula el último menú con la acción de ventana.

El manifest carga primero estate_property_views.xml y después real_estate_menuitem.xml. Odoo procesa los archivos de datos en orden: la acción debe existir cuando el menú la referencia. Invertir el orden en una instalación limpia puede provocar un error de ID externo no encontrado. Si la acción ya existe en la base, una actualización puede ocultar ese problema.

La consigna contiene una repetición: primero pide colocar el menú después de la acción y luego pregunta por ese mismo orden. La comparación útil es después frente a antes.

Aún no se definieron permisos para estate.property. La falta de acceso puede ocultar los menús al usuario habitual; el punto 7 propone observarlos como superusuario y los siguientes puntos introducen permisos.

## Registro de validación

Los puntos 1 a 5 se comprobaron con las salidas y capturas de la práctica. El punto 6 requiere actualizar el módulo y comprobar los registros de menú. Este archivo se ampliará a medida que se resuelvan las siguientes consignas.
