# Unidad 2 — Guía de estudio

Esta unidad tiene 27 puntos. Avance: 0/27 validados; punto 1 preparado. La Unidad 1 se documenta en unidad-1.md.

## Punto 1 — Superficie total computada

Se agrega total_area como Integer con etiqueta Superficie total y compute="_compute_total_area". El método recorre cada propiedad en self y asigna living_area + garden_area. Se usa Integer porque ambos campos de origen son Integer.

No se agrega store=True ni api.depends en esta etapa: el recorrido didáctico incorpora almacenamiento en el punto 4 y dependencias en el punto 5. El campo se mostrará en el formulario en el punto 2.

Estado: sintaxis y cálculo verificados para varios registros (100+25=125, 0+0=0, 80+20=100). Estas pruebas ejecutan el método aislado, no el ORM de Odoo. Actualización del módulo y registro del campo pendientes.

Para validar la carga: actualizar real_estate y consultar los Campos del modelo estate.property. Buscar total_area; debe aparecer como Superficie total, tipo integer y computado. Todavía no aparece en el formulario personalizado.

## Apunte — Campos computados

compute indica el método que calcula el valor del campo. La convención _compute_nombre facilita identificar su función. self puede incluir varias propiedades: el método debe asignar el resultado a cada registro, por eso usa un bucle.

Un campo computado sin almacenamiento se calcula a través del ORM cuando hace falta su valor; no genera una columna propia para guardar el resultado en la tabla. Sus campos de origen sí pueden estar almacenados. Los campos computados son de solo lectura por defecto cuando no tienen un método inverse.

El comportamiento de recálculo tras modificar las entradas depende de declarar las dependencias. Se observará paso a paso en los próximos ejercicios; aún no se considera probado el recálculo interactivo en el formulario.

### Validación de carga del punto 1

La captura de Campos de Propiedad muestra total_area, etiqueta Superficie total, tipo integer y Readonly marcado. Se confirma el registro del campo en Odoo; su método compute y suma se verificaron en el código. Esta pantalla no muestra el cálculo ejecutado en el formulario, que se probará en el punto 2.

Estado: punto 1 validado mediante carga del campo y verificación del método. Avance de Unidad 2: 1/27 completados; faltan 26.
