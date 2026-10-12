# Unidad 2 — Guía de estudio

Esta unidad tiene 27 puntos. Avance actual: 12/27 validados; punto 13 preparado. La Unidad 1 se documenta en unidad-1.md.

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

### Validación del punto 3

La captura de pgweb muestra la consulta indicada con dos filas: garden_area y living_area, sin total_area. Se confirma que el campo computado no almacenado no genera una columna para su resultado.

Avance: 3/27 completados; faltan 24.

## Punto 4 — Almacenar el campo computado

Se agrega store=True a total_area conservando compute y sin api.depends todavía. Sintaxis y configuración verificadas. La actualización debe crear la columna total_area y calcular sus valores durante la inicialización correspondiente.

Estado: código preparado; prueba en Odoo y pgweb pendiente. Esta etapa reproduce un problema didáctico: sin dependencias declaradas, cambiar living_area o garden_area no informa al ORM que debe recomputar el total almacenado. No se considera una configuración final adecuada; se corregirá en el punto 5 después de observar el resultado real.

Prueba: actualizar, anotar el total de una propiedad con cubierta 100 y jardín 25; cambiar cubierta a 120, guardar y reabrir. Observar si el total permanece en 125 en lugar de 145. Repetir la consulta de columnas del punto 3: ahora debe incluir total_area. Documentar el comportamiento observado antes de agregar el decorador.

Apunte: store=True almacena el resultado del compute en la base; no convierte el campo en editable ni declara automáticamente las entradas de las que depende. Las dependencias permiten decidir cuándo recalcular un valor almacenado.

### Validación del punto 4

La consulta de pgweb devuelve garden_area, living_area y total_area: el resultado computado ahora tiene columna. La captura del formulario muestra cubierta 120 y total 125, reproduciendo el valor desactualizado esperado con el jardín 25 de la prueba previa. El jardín no está visible en este recorte.

Estado: punto 4 validado. Avance: 4/27 completados; faltan 23.

## Punto 5 — Dependencias del campo computado

Se importa api y se decora _compute_total_area con @api.depends("living_area", "garden_area"). Se conserva store=True. Sintaxis, importación y nombres de dependencias verificados; recálculo con ORM pendiente.

api.depends declara qué entradas afectan al cálculo. El ORM utiliza esa información para invalidar y recomputar el total cuando cambia living_area o garden_area. El decorador no realiza la suma: el método sigue asignando el resultado a cada registro. store=True guarda ese resultado actualizado en la base.

Prueba: actualizar real_estate, confirmar jardín 25 y cambiar cubierta a 130. El total debe calcularse como 155; guardar y reabrir para verificar persistencia. Luego cambiar jardín a 30: el total debe resultar 160. No depender únicamente de que la actualización del módulo corrija valores anteriores; modificar las entradas comprueba que las dependencias funcionan.

Estado: punto 5 preparado para validación. Tras validar, continuar automáticamente al punto 6.

### Validación del punto 5

Las capturas muestran cubierta 130 con total 155, y luego cubierta 130 con total 160, siguiendo la prueba de jardín 25 y 30. Se confirma el resultado actualizado tras cambiar las entradas. El jardín no aparece en estos recortes ni se documenta visualmente el momento exacto de actualización.

Estado: punto 5 validado mediante resultados de la prueba indicada. Avance: 5/27 completados; faltan 22.

## Punto 6 — Preparar ofertas de prueba

No requiere cambios de código. Abrir una propiedad de prueba y, en Ofertas, registrar al menos dos ofertantes distintos con precios diferentes. Por ejemplo, 50000 y 65000. Estado puede quedar vacío. Guardar, reabrir y comprobar que ambas ofertas siguen asociadas a esa propiedad. Si ya existe una oferta de 50000, basta agregar otra con distinto ofertante y precio 65000 en esa misma propiedad.

Estado: carga de ofertas pendiente. Estos datos servirán para comprobar el máximo calculado por best_offer en el punto 7. Dos filas en una misma propiedad permiten comparar sus precios; usar propiedades distintas no valida ese máximo por propiedad.

### Validación del punto 6

Casa Lanús muestra ofertas guardadas de 65000 de Douglas Fletcher y 50000 de Floyd Steward, ambas con Estado vacío. Se confirma la preparación de dos ofertantes y precios diferentes en una misma propiedad. Avance: 6/27 completados; faltan 21.

## Punto 7 — Mejor oferta computada

Se agrega best_offer como Float computado, etiqueta Mejor oferta, debajo de selling_price en el formulario. _compute_best_offer usa offer_ids.mapped("price") y max(..., default=0.0). @api.depends("offer_ids.price") declara la dependencia de los precios de las ofertas relacionadas. Se incluye toda oferta, sin filtrar estado, como indica la consigna.

No se almacena en esta etapa: el máximo es barato de calcular para el conjunto pequeño del práctico y evita una columna de resultado. Si se necesitara búsqueda SQL, agrupación o consultas frecuentes sobre grandes volúmenes, podría evaluarse store=True con dependencias correctas y su costo de recomputación. Almacenar es una decisión de uso y rendimiento, no una condición para mostrar el campo.

Apunte: mapped devuelve aquí la lista de precios; max obtiene el mayor. default=0.0 resuelve el caso sin ofertas, evitando un error por una lista vacía. La dependencia con punto recorre el One2many hasta price de cada oferta.

Estado: sintaxis, ubicación XML y método aislado verificados para [50000,65000]→65000, []→0 y [70000]→70000. Prueba ORM pendiente. Actualizar, abrir Casa Lanús y verificar Mejor oferta 65000. Cambiar la oferta mayor a 70000, guardar y reabrir: debe mostrar 70000. En otra propiedad sin ofertas, debe mostrar 0.

### Validación del resultado inicial del punto 7

La captura de Casa Lanús muestra Mejor oferta 65,000.00 debajo de Precio de venta, coincidiendo con el máximo de las dos ofertas registradas en el punto 6. Se confirma presentación y cálculo inicial. La prueba de cambio a 70000 y de propiedad sin ofertas no fue aportada; se conservan como verificaciones pendientes.

Avance: 7/27 implementaciones y resultados iniciales comprobados; faltan 20 puntos.

## Punto 8 — Ofertas desde un formulario

Se quita editable="top" de la vista de lista de ofertas, conservando Precio, Ofertante y Estado. XML y ausencia del atributo verificados. Al agregar o abrir una oferta desde el One2many se espera un formulario emergente, en lugar de una fila editable. El menú y la acción de propiedades no cambian.

Prueba: actualizar real_estate, abrir una propiedad y entrar en Ofertas. Pulsar una oferta existente o Add a line: debe abrir un formulario. Aprovecharlo para cambiar la oferta mayor de 65000 a 70000, guardar el formulario y la propiedad, y reabrir: Mejor oferta debe mostrar 70000. Esto completa la prueba de recálculo pendiente del punto 7. Una propiedad sin ofertas debe mostrar 0.

Apunte: editable="top" habilita edición en línea en esa vista, colocando registros nuevos arriba; quitarlo cambia la forma de interacción, no los permisos ni los datos guardados. El formulario puede ser generado automáticamente por Odoo si no hay uno personalizado.

Estado: punto 8 preparado para validación; avance 7/27.

### Validación del punto 8 y recálculo del punto 7

La primera captura muestra formulario emergente de una oferta con precio 70000. La segunda muestra la oferta de 70000 y la de 50000 en Casa Lanús, y Mejor oferta 70000. Se confirma apertura del formulario y actualización del máximo siguiendo la prueba indicada. El caso sin ofertas sigue sin captura.

Avance: 8/27 completados; faltan 19.

## Punto 9 — Validez y fecha límite

Se agregan validity Integer con etiqueta Validez (días) y default=7, y date_deadline Date con etiqueta Fecha límite, al modelo de ofertas. Se incluyen ambos en la lista tras Estado. Sintaxis, valor predeterminado y columnas verificados; carga y prueba pendientes.

En este punto ambos son campos normales independientes: ingresar días no calcula aún la fecha ni ingresar fecha modifica los días. Esa relación compute/inverse corresponde al punto 10. Date no contiene hora y validity expresa una cantidad de días, no una fecha.

Validación: actualizar, abrir Ofertas de una propiedad y comprobar ambas columnas. Add a line debe abrir formulario con Validez 7 y Fecha límite vacía. Completar precio y ofertante, ingresar una fecha manual y guardar el formulario y la propiedad. Verificar que días y fecha se conservan en la fila. Puede descartarse la oferta nueva si solo se quiere inspeccionar los valores iniciales.

### Validación del punto 9

La captura confirma Validez 7 y Fecha límite vacía en ambas ofertas. Avance actual: 9/27 completados; faltan 18. Los avances anteriores del documento son registros históricos.

## Punto 10 — Fecha límite con compute e inverse

Código subido: fecha límite = fecha de creación + validez en días. Para ofertas aún no guardadas se usa la fecha actual del usuario. La inversa modifica validity según la diferencia entre la fecha límite ingresada y la fecha base; el ajuste se comprueba al guardar y reabrir. Se declaran dependencias create_date y validity. No se almacena el resultado ni se modifica create_date. Las ofertas antiguas usan su fecha de creación original.

Pruebas aisladas correctas: base 11/10/2026 y validez 7 producen 18/10/2026; ingresar 25/10/2026 produce validez 14. Pendiente probar en Odoo: crear oferta con validez 10, guardar y luego mover fecha límite tres días adelante. Guardar y reabrir: debe tener validez 13. Compute calcula el resultado desde las entradas; inverse ajusta una entrada cuando se edita el resultado. Al borrar la fecha se conserva validity y se recalcula desde esa duración.

### Validación del punto 10 y avance al 11

La oferta de Colleen Diaz muestra 7 días/19 de octubre, luego 10 días/22 de octubre y finalmente 13 días/25 de octubre tras editar la fecha. Se confirma cálculo e inversa. Avance: 10/27 completados; faltan 17.

## Punto 11 — Tipo de propiedad relacionado y almacenado

Se agrega property_type_id Many2one en la oferta con related="property_id.property_type_id" y store=True. El tipo se deriva de la propiedad; no se elige independientemente. Por defecto es de solo lectura. El ORM establece dependencias de la cadena relacionada. Almacenarlo permite disponer de su columna y agrupar por el tipo. No representa una copia histórica congelada.

Sintaxis y definición verificadas; prueba en Odoo pendiente. Actualizar y revisar property_type_id en Campos de estate.property.offer, y su columna en pgweb. Asignar Casa al Tipo Propiedad de una propiedad con ofertas, guardar y abrir una oferta: el formulario automático debe mostrar Tipo Propiedad Casa. Cambiar el tipo de la propiedad a Departamento, guardar y reabrir la oferta permite comprobar propagación. Acción, menú y agrupación se incorporan en el punto 12.

### Validación del punto 11

La segunda captura muestra Tipo Propiedad DEPARTAMENTO de solo lectura en el formulario de la oferta. Se confirma presentación del relacionado después de asignar ese tipo a la propiedad siguiendo la prueba indicada. La primera captura no muestra el campo; no se considera evidencia del valor Casa. El almacenamiento se verificó en el código, sin captura de pgweb.

Avance: 11/27 completados; faltan 16.

## Punto 12 — Todas las ofertas y agrupación por tipo

Se agregan formulario personalizado con los siete campos de oferta, vista de búsqueda y acción Ofertas con list,form. En Inmobiliaria → Anuncios se agrega Ofertas después de Propiedades. La búsqueda permite agrupar por property_type_id; al ser un relacionado almacenado se puede usar para agrupación de base de datos. Se conserva la lista existente y su uso dentro de propiedades.

Estado: XML, formulario, contexto de agrupación y menú verificados; navegación en Odoo pendiente. Actualizar, abrir Anuncios → Ofertas y usar Agrupar por → Tipo de propiedad. Abrir una fila debe mostrar Precio, Ofertante, Propiedad, Tipo Propiedad, Estado, Validez y Fecha límite. Los grupos solo aparecen si tienen ofertas; propiedades sin tipo se agrupan bajo un valor vacío. Las ACL se mantienen para Manager y Vendedor.

### Validación del punto 12

Las capturas muestran agrupación por Tipo de propiedad con tres ofertas y suma 231111, y formulario propio con Precio, Ofertante, Propiedad, Tipo Propiedad, Estado, Validez y Fecha límite. Se confirma navegación, agrupación y formulario. Avance: 12/27; faltan 15.

## Punto 13 — Onchange del jardín

Se agrega @api.onchange("garden") sobre _onchange_garden. Al marcar garden se asigna garden_area=10; al desmarcar se asigna 0. Sintaxis y método aislado comprobados en ambos sentidos. No altera automáticamente registros existentes durante la actualización.

Apunte: onchange responde a cambios en el formulario y ajusta sus valores antes de guardar. No equivale a una regla de negocio ejecutada siempre por create/write: operaciones externas al formulario pueden no ejecutarlo. El usuario puede modificar la superficie propuesta después. Los cambios se persisten al guardar; descartarlos conserva los valores anteriores.

Prueba: actualizar, abrir propiedad de prueba, ir a Jardín y marcar el booleano (si ya está marcado, desmarcar y volver a marcar). La superficie debe ser 10. Desmarcar debe poner 0. Guardar y reabrir comprueba persistencia. Superficie total debe actualizarse por api.depends al cambiar garden_area. Con cubierta 130: jardín marcado da total 140 y desmarcado 130.

Estado: punto 13 preparado para validación.
