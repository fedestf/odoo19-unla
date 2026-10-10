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

Estado: validado al abrir Inmobiliaria > Anuncios > Propiedades como superusuario.

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

Los puntos 1 a 5 se comprobaron con las salidas y capturas de la práctica. Los puntos 6 y 7 se comprobaron mediante la lista Propiedades abierta como superusuario. Este archivo se ampliará a medida que se resuelvan las siguientes consignas.

## Punto 7 — Superusuario

Estado: validado. El modo superusuario evita restricciones de acceso y permitió ver la lista vacía de Propiedades. No asigna permisos permanentes al usuario. Para volver al usuario habitual, cerrar sesión y volver a ingresar.

## Punto 8 — Modos de vista

Estado: pruebas realizadas; el estudiante confirmó la restauración de list,form.

- list: abre una lista de registros.
- form: abre un formulario; sin registro indicado, un registro nuevo.
- list,form: abre primero la lista y ofrece formulario.

Se cambió view_mode desde la interfaz. Esos cambios se guardan en la base, no en Git. Actualizar el módulo vuelve a cargar el valor del XML.

Durante la prueba, el navegador continuó mostrando la lista a pesar de que la configuración decía form. Tras reiniciar el servicio y entrar desde el menú se observó un formulario; no se determinó con certeza la causa de la persistencia anterior. El parámetro view_type sugerido inicialmente no resolvió el caso. Se desactivó Data Caching temporalmente y luego se indicó restaurarlo.

El formulario generado automáticamente mostró bedrooms=2 y orientación Norte. Guardar sin Título produjo Missing required fields, coherente con required=True.

## Punto 9 — Tipos de usuario

Interno: trabaja en el backend según sus grupos; base.group_user.
Portal: accede a información autorizada desde el portal; base.group_portal.
Público: representa visitantes sin autenticación; base.group_public.

El superusuario es un modo privilegiado, no un cuarto tipo de usuario.

## Punto 10 — Permiso de lectura

Estado: validado. Tras descargar el CSV y actualizar el módulo se abrió la lista con el usuario habitual, sin botón New.

Archivo: security/ir.model.access.csv, incluido en data del manifest antes de vistas y menús.

La regla access_estate_property_user usa model_estate_property para referenciar el modelo y base.group_user para usuarios internos.

| Permiso | Valor |
| --- | --- |
| perm_read | 1 |
| perm_write | 0 |
| perm_create | 0 |
| perm_unlink | 0 |

Para dar todos los permisos en esta regla, los cuatro valores serían 1. En esta consigna se conserva solo lectura.

Los permisos de acceso se suman: un 0 no revoca permisos concedidos por otra regla o grupo. El superusuario evita estas comprobaciones. Por eso la validación debe hacerse con un usuario interno habitual, fuera del modo superusuario.

Resultado esperado: menú y lista visibles; creación, modificación y eliminación no permitidas, salvo que existan otras reglas que las concedan. Si la tabla está vacía, ver la lista confirma el acceso, pero todavía no demuestra lectura de un registro existente.

## Punto 11 — Grupo creado desde la interfaz

Estado: validado por el estudiante, quien confirmó creación, modificación y eliminación de una propiedad de prueba con su usuario habitual.

En Odoo 19, se accedió por Ajustes > Usuarios y compañías > Grupos. Se creó Manager de Propiedades, se asignó el usuario y se agregó en Access Rights una regla sobre Propiedad con lectura, escritura, creación y eliminación habilitadas.

Los permisos son aditivos: la regla de solo lectura del grupo interno no impide que Manager conceda los demás permisos.

La configuración manual vive en la base y no se incluye automáticamente en Git.

## Punto 12 — Grupo definido en el módulo

Estado: validado mediante captura de ambos grupos: Manager de Propiedades del módulo y Manager de propiedades (manual).

security/real_estate_res_groups.xml define un registro res.groups con ID group_estate_property_manager y nombre Manager de Propiedades. El manifest lo carga antes del CSV de permisos.

ID externo completo: real_estate.group_estate_property_manager. Odoo usa ese identificador para actualizar el mismo registro al recargar el XML; no identifica registros por el nombre visible.

El grupo manual del punto 11 no se fusiona automáticamente con el grupo XML. Para distinguirlos, renombrar el grupo manual a Manager de Propiedades (manual - punto 11), conservando de momento sus usuarios y permisos. El grupo del módulo se mantendrá con el nombre solicitado. En el punto 14 se definirán los permisos del grupo XML y se podrá completar el reemplazo de la configuración manual.

Este punto define solo el grupo; todavía no añade sus permisos ni asigna usuarios en código.

### Interfaz frente a código

Interfaz: permite probar rápidamente sin programar; el cambio queda en esa base, es fácil olvidar documentarlo y no se reproduce con git pull o una instalación nueva.

Código: deja historial y revisión en Git, facilita reproducir la configuración al instalar el módulo y referenciarla por ID externo; exige respetar sintaxis y orden de carga, y actualizar el módulo para aplicarlo.

Una actualización puede sobrescribir campos definidos en XML, según las opciones de carga. Las asignaciones de usuarios se gestionan en la base salvo que se incluyan expresamente en los datos del módulo.

## Punto 13 — Grupo Vendedor de Propiedades

Estado: validado mediante captura de Vendedor de Propiedades en la lista de grupos.

Se agregó al mismo real_estate_res_groups.xml un registro res.groups con nombre Vendedor de Propiedades e ID externo real_estate.group_estate_property_salesman.

El manifest ya carga este XML; no requiere una segunda entrada. Este punto crea solo el grupo. Los permisos de lectura del vendedor y los permisos completos del manager se definirán en el punto 14.

Validación: descargar los cambios, actualizar Inmobiliaria y buscar Vendedor de Propiedades en Ajustes > Usuarios y compañías > Grupos. No asignar permisos manuales al nuevo grupo para esta consigna.

## Punto 14 — Permisos del Manager y del Vendedor

Estado: Manager validado para creación, modificación y eliminación según confirmación del estudiante. Vendedor validado para acceso a la lista, sin botón New; falta observar lectura de un registro existente y probar rechazo de escritura/eliminación.

En security/ir.model.access.csv se conserva el ID access_estate_property_user de la regla del punto 10 y se cambia su group_id de base.group_user a real_estate.group_estate_property_salesman. Conservar el ID actualiza la misma regla; cambiarlo podría dejar activa la regla anterior.

Se agrega access_estate_property_manager para real_estate.group_estate_property_manager.

| Grupo | Leer | Escribir | Crear | Eliminar |
| --- | --- | --- | --- | --- |
| Vendedor de Propiedades | 1 | 0 | 0 | 0 |
| Manager de Propiedades | 1 | 1 | 1 | 1 |

Se comprobó la estructura de ocho columnas y las referencias contra los ID del XML de grupos. La ejecución se comprueba después de actualizar el módulo.

Los permisos del grupo manual del punto 11 siguen en la base: Git no los elimina. Para validar el nuevo Manager, asignar al usuario el grupo del módulo y quitar su pertenencia al grupo manual, sin borrar el grupo ni sus reglas.

Prueba Manager: crear, leer, modificar y eliminar una propiedad de prueba como usuario habitual. Prueba Vendedor: quitar temporalmente la pertenencia al Manager y asignar Vendedor; cerrar sesión y volver a ingresar; comprobar lectura y ausencia de creación. Tener ambos grupos concede los permisos del Manager porque los permisos son aditivos. Usar preferentemente un usuario de prueba para comparar roles.

La respuesta sobre un usuario sin ninguno de los grupos corresponde al punto 15, y debe considerar otras reglas o grupos presentes en la base.

### Resultado observado del punto 14

Tras actualizar el módulo, el estudiante confirmó que pudo crear, modificar y eliminar con el Manager del módulo. Reiniciar sin actualizar el módulo no había cargado los permisos nuevos.

Para Vendedor se comprobó la pertenencia del usuario al grupo y una regla de solo lectura. Hubo inicialmente un error de acceso y un aviso de página desactualizada; después de renovar la página y la sesión, se pudo abrir la lista sin New. No se atribuye el error a una causa única confirmada.

La última captura muestra una lista vacía. Confirma acceso a la acción/lista y ausencia del control de creación, pero no demuestra lectura de un registro existente ni un intento denegado de modificación o eliminación. Estas comprobaciones quedan pendientes para completar la evidencia de solo lectura.

## Punto 15 — Usuario sin Vendedor ni Manager

Estado: validado mediante captura de Access Error después de la prueba de retirar las pertenencias.

Un usuario habitual sin grupos que otorguen acceso a estate.property no puede leer sus registros. El menú puede ocultarse; abrir la acción directamente produce Access Error.

La captura enumera Manager de Propiedades, Manager de propiedades (manual) y Vendedor de Propiedades como grupos que permiten la operación. La regla del grupo manual sigue existiendo en la base aunque se haya retirado al usuario de ese grupo.

Los permisos de acceso son aditivos: cualquier otra regla aplicable podría conceder acceso. El modo superusuario evita estas restricciones y no sirve para esta prueba.

Después de validar, volver a asignar al usuario el Manager de Propiedades definido por el módulo, cerrar sesión y volver a ingresar para continuar. Esta restauración queda pendiente de confirmación.

## Punto 16 — Categoría Inmobiliaria (adaptación a Odoo 19)

Estado: validado mediante captura de Groups: Manager y Vendedor muestran Inmobiliaria en la columna Privilege; el grupo manual permanece sin privilegio.

En Odoo 19, los grupos se vinculan mediante privilege_id a res.groups.privilege. El privilegio tiene category_id que apunta a ir.module.category. Por eso el XML define:

1. module_category_real_estate: categoría Inmobiliaria.
2. privilege_real_estate: privilegio Inmobiliaria, vinculado a esa categoría.
3. Manager y Vendedor: vinculados al privilegio mediante privilege_id.

El orden permite resolver las referencias antes de usarlas. Se mantienen los ID externos de los grupos existentes, sus permisos y sus asignaciones de usuarios. El grupo manual no se vincula a esta categoría.

La organización facilita encontrar los grupos. No concede permisos ni hace que Manager herede Vendedor: no se agregan implied_ids.

Para validar, actualizar el módulo y abrir Ajustes > Usuarios y compañías > Grupos. La columna Privilege debe mostrar Inmobiliaria para ambos grupos. En cada formulario, Privilege debe tener ese valor. Buscar el nombre del privilegio o agrupar por él permite ubicarlos juntos.

Fuente técnica: código oficial Odoo 19, res_groups.py y res_groups_privilege.py.

## Punto 17 — Vista de búsqueda

Estado: vista cargada y pruebas con datos verificadas para Mis propiedades, agrupación por Código Postal y búsqueda por Habitaciones.

En estate_property_views.xml se crea estate_property_search_view de ir.ui.view, vinculada a estate.property. La acción la referencia expresamente mediante search_view_id.

Campos de búsqueda: name, postcode, expected_price, bedrooms, living_area y facades.

Filtro Mis propiedades: dominio [('create_uid', '=', uid)]. create_uid es el creador; uid representa al usuario actual. No se filtra por vendedor asignado, porque la consigna pide registros creados por el usuario.

Agrupaciones: create_uid (Creado por), create_date:month (Mes de creación) y postcode (Código Postal). Se interpreta mes como mes de creación, usando la fecha automática de auditoría.

Un dominio selecciona registros; group_by organiza los resultados sin modificar los datos. La vista search configura el buscador, no las columnas de la lista.

Para validar: actualizar el módulo, abrir Propiedades y desplegar el buscador. Deben aparecer Mis propiedades y las tres agrupaciones. Al escribir un texto o número en el buscador, elegir el campo por el que se desea buscar.

Crear propiedades de prueba con distintos códigos postales y valores permite comprobar resultados. Para crear, el usuario debe pertenecer al Manager del módulo. La aparición de controles no demuestra por sí sola el comportamiento del filtrado con datos.

No se cambian permisos ni se crea aún una vista de lista o formulario personalizada.

### Evidencias del punto 17

Las capturas muestran:
- Mis propiedades: Casa Lanús y Casa Banfield (dos registros).
- Código Postal: grupo 1824 con Casa Lanús y grupo 1828 con Casa Banfield.
- Habitaciones = 3: solo Casa Banfield.

La captura del desplegable también mostró Creado por y Mes de creación. Su agrupación con datos todavía no se comprobó. Otros campos de búsqueda se implementaron, pero no se probaron individualmente.

El filtro Mis propiedades incluyó los registros del usuario; no se hizo todavía una prueba con registros de otro creador que deban excluirse.
