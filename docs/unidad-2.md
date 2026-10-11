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

## Punto 2 — Superficie total en el formulario

Avance: 1/27 completados; punto 2 preparado para validación. Faltan 26, incluido este. Preferencia del estudiante: al validar un punto, continuar directamente con el siguiente sin pedir otro mensaje de avance.

Se incorpora total_area después de living_area en la página Descripción. XML y ubicación verificados. El campo conserva compute sin store=True ni api.depends según la secuencia de ejercicios.

Prueba: actualizar el módulo y abrir una propiedad de prueba. Ingresar Superficie cubierta 100 y Superficie jardín 25 en sus respectivas pestañas. Volver a Descripción y observar Superficie total antes de guardar; luego guardar y reabrir para comprobar el cálculo 125. Cambiar cubierta a 120 y observar el resultado antes y después de guardar/reabrir (esperado al calcular desde los datos actuales: 145).

Si el valor no se refresca inmediatamente, registrar el comportamiento real: todavía no hay dependencias declaradas para invalidar el valor computado al cambiar las entradas. No dar por probado el recálculo interactivo solo porque la suma se vea correcta después de reabrir. Las dependencias se incorporarán en el punto 5.

Estado: código preparado; observación del formulario pendiente.

### Validación visual del punto 2

La captura de Casa Lanús muestra Superficie cubierta 100 y Superficie total 125 en Descripción, resultado compatible con la prueba indicada de jardín 25. El valor del jardín y el momento de actualización del total no están visibles; no se infiere recálculo inmediato ni reapertura de esta captura.

Estado: presentación y resultado de cálculo del punto 2 validados visualmente. Avance: 2/27 completados; faltan 25.

## Punto 3 — Campo computado no almacenado en pgweb

No requiere cambio de código. Abrir pgweb y consultar las columnas de estate_property. total_area debe estar ausente porque el campo computado no usa store=True; living_area y garden_area sí están almacenados. El ORM calcula el resultado al acceder al campo, lo que permite mostrarlo en el formulario sin una columna persistente.

Consulta de solo lectura para comprobar columnas:

```sql
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'estate_property'
  AND column_name IN ('living_area', 'garden_area', 'total_area')
ORDER BY column_name;
```

Resultado esperado: garden_area y living_area, sin total_area. Estado: comprobación en pgweb pendiente. No usar esta ausencia para concluir que falta el campo en Odoo: los metadatos del ORM y las columnas físicas son distintos.
