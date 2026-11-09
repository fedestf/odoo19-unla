# TP de Programación en Odoo - Parte 1

Estado: parte 1 implementada para Odoo 19 Community. 21 pruebas locales ejecutadas y correctas; 17 pruebas de integración preparadas. Instalación y pruebas dentro de Odoo pendientes para cuando se retomen las validaciones.

Consigna: documento UNLa, Lic. en Sistemas, «Trabajo Práctico - Parte 1/2», versión 20251021. La parte 2 todavía no fue proporcionada. La introducción menciona crédito, pero esta entrega no define grupos, cálculo de saldo ni reglas de consumo/liberación; no se inventaron esas reglas.

## Organización

Misma VM, mismo entorno Docker y repositorio `fedestf/odoo19-unla`. Módulo nuevo `sale_channel_tp`, independiente de inmobiliaria, en `odoo/custom/src/private/sale_channel_tp`. Base nueva `tp_canales`.

El módulo depende de `sale_management` y `sale_stock`; Odoo resuelve sus dependencias estándar de ventas, inventario y facturación. No requiere Enterprise ni los módulos `real_estate`, `estate_account` o `real_estate_training`.

El archivo `compose.tp-canales.yaml` se combina con `devel.yaml`: selecciona `tp_canales` para Odoo y pgweb. Mantiene el volumen PostgreSQL existente. La base `devel` conserva sus datos y sus módulos. Al arrancar con la configuración habitual se vuelve a inmobiliaria.

## Correspondencia con la consigna

| Punto | Implementación |
| --- | --- |
| 1: gestión de canales | Ventas > Configuración > Canales de venta, con lista, formulario, búsqueda y archivado. |
| 1: nombre obligatorio | Campo Nombre obligatorio, sin aceptar solo espacios. |
| 1: código obligatorio y único | Código obligatorio, normalizado a mayúsculas y sin espacios al inicio/final; restricción UNIQUE global, incluidas otras compañías y canales archivados. |
| 1: depósito y diario | Relaciones con almacén y diario de ventas de la misma compañía. |
| 2a: canal en pedido | Campo obligatorio en presupuestos y pedidos, sin selección automática para que el usuario lo elija. |
| 2b: depósito del canal | Campo computado almacenado y control en servidor; el flujo estándar de inventario usa el almacén del pedido. |
| 2c: diario del canal | Diario del pedido tomado del canal, trasladado al preparar la factura y controlado también en ella. |
| 2d: traslado a entregas | Campo relacionado almacenado en entregas a través de `sale_id`. |
| 2d: traslado a facturas | Campo almacenado trasladado al crear facturas desde los pedidos. |
| 2d: filtrar y agrupar | Campo de búsqueda, agrupación y columna en presupuestos/pedidos, transferencias y facturas. |

## Decisiones de implementación

- Se exige completar depósito y diario para que un canal siempre pueda utilizarse, aunque el listado de la consigna solo marca expresamente nombre y código como obligatorios.
- La compañía del canal, almacén, diario y pedido debe coincidir. El diario debe ser de ventas. Se verifica en el servidor además del filtro de selección de la interfaz.
- Una vez utilizado el canal en un pedido, no se puede cambiar su depósito, diario o compañía. Así no se alteran indirectamente presupuestos ni documentos históricos; para otra configuración se crea otro canal. Nombre, código y archivado siguen disponibles según permisos.
- Solo puede cambiarse el canal de presupuestos sin entregas ni facturas. Al confirmarse queda bloqueado también en el servidor.
- El campo Depósito del pedido queda de solo lectura porque lo determina el canal. El diario estándar del pedido también queda de solo lectura y conserva su visibilidad estándar.
- Los canales archivados no se ofrecen para nuevas selecciones; un presupuesto que conserve uno no puede confirmarse hasta elegir un canal activo.
- La facturación conjunta agrupa por canal y diario además de las claves estándar. Dos canales diferentes no se mezclan en una factura, aunque tengan el mismo cliente y diario. Pedidos compatibles del mismo canal pueden agruparse.
- Las facturas manuales y transferencias ajenas a pedidos no están obligadas a tener canal. Las facturas de pedido lo reciben automáticamente. No se publican ni envían facturas automáticamente.
- Las rutas logísticas siguen siendo las de Odoo. La comprobación prevista utiliza productos físicos y el flujo estándar desde el almacén del canal; no se configuraron dropshipping, rutas alternativas ni abastecimiento externo al almacén.
- No se insertan canales, ventas ni facturas de prueba en la base de trabajo. Los casos automatizados de integración generan sus propios datos en una base separada.

## Permisos

Responsable/Administrador de Ventas: crear, leer, editar, archivar y eliminar canales no referenciados. Usuario de ventas, usuario de inventario y usuario de facturación: lectura. Los documentos conservan sus permisos estándar.

Una regla global limita los canales a las compañías habilitadas del usuario. Las relaciones usan `check_company` y verificaciones adicionales. El único `sudo()` añadido es una búsqueda de existencia de pedidos al intentar cambiar la configuración de un canal; incluye los pedidos ocultos por reglas de vendedor y no devuelve sus datos al usuario. No se usa para crear, confirmar, entregar ni facturar documentos comerciales.

## Instalación en la VM, cuando se decida utilizar el TP

Estos comandos están preparados; no fueron ejecutados desde este chat. No requieren borrar ninguna base ni usar `invoke resetdb`.

Primera instalación, utilizando una base nueva llamada `tp_canales`:

```bash
cd ~/odoo19
git pull --ff-only
docker compose -f devel.yaml -f compose.tp-canales.yaml stop odoo
docker compose -f devel.yaml -f compose.tp-canales.yaml run --rm odoo odoo -d tp_canales -i sale_channel_tp --without-demo=all --load-language=es_AR --stop-after-init
docker compose -f devel.yaml -f compose.tp-canales.yaml up -d
```

Abrir `http://localhost:19069/web/login?db=tp_canales` dentro de la VM. Usar las credenciales de esa base nueva; los usuarios de `devel` no se copian automáticamente. Si la base ya fue inicializada, usar la actualización indicada más abajo, no repetir una inicialización como método de actualización.

Antes de cargar ventas:

1. Completar la compañía, país, moneda y configuración contable correspondiente. Configurar el plan contable/localización desde Odoo si todavía falta.
2. Asignar al usuario permisos de administrador de Ventas y los permisos de Inventario y Facturación necesarios para operar y configurar esos módulos.
3. Tener al menos un almacén de la compañía. Para comprobar canales con distintos depósitos, habilitar varios almacenes y crear un segundo.
4. Tener diarios de tipo Ventas de la compañía. Se pueden crear dos para distinguir la facturación por canal.
5. Crear los canales desde Ventas > Configuración > Canales de venta, eligiendo sus depósitos y diarios. Los permisos y la configuración contable se gestionan desde las aplicaciones estándar.
6. Preparar un cliente y un producto físico vendible. Para la prueba inicial de facturación puede usarse una política de facturación por cantidades pedidas; con cantidades entregadas, primero debe realizarse la entrega.

Actualizaciones posteriores, sobre la misma base del TP:

```bash
cd ~/odoo19
git pull --ff-only
docker compose -f devel.yaml -f compose.tp-canales.yaml stop odoo
docker compose -f devel.yaml -f compose.tp-canales.yaml run --rm odoo odoo -d tp_canales -u sale_channel_tp --stop-after-init
docker compose -f devel.yaml -f compose.tp-canales.yaml up -d
```

Para volver al entorno habitual de inmobiliaria:

```bash
cd ~/odoo19
docker compose -f devel.yaml up -d
```

Abrir `http://localhost:19069/web/login?db=devel`. Estos comandos cambian el servicio/base seleccionada; no eliminan la otra base. Evitar instalar `sale_channel_tp` en `devel`: allí hay otros ejercicios y la obligatoriedad del canal afecta a todos los pedidos de la base en la que esté instalado.

## Pruebas preparadas para más adelante

Pruebas locales, sin servidor Odoo y sin dependencias externas:

```bash
python3 -m unittest discover -s tests_tp_canales -v
```

Resultado de desarrollo: 21 pruebas correctas. Ejecutan métodos reales extraídos del módulo con sustitutos mínimos del ORM y revisan sintaxis Python/XML, manifiesto, ACL, regla de compañías y filtros. No demuestran instalación, recomputación real del ORM, permisos reales ni generación de documentos.

Además se verificaron estáticamente 11 expresiones XPath contra los archivos oficiales de vistas de Odoo 19. Esto comprueba los puntos de inserción, no sustituye la compilación de vistas de la instalación OCB concreta.

Hay 17 casos de integración en `sale_channel_tp/tests/test_sale_channel.py`, pendientes de ejecutar: código único, campos vacíos, diario y compañía incorrectos, canal obligatorio, cambio desde formulario, recomputación, depósito incoherente, protección de configuración, entrega real con almacén/canal, bloqueo de canal confirmado/archivado, factura con diario/canal, separación o agrupación de facturas, ACL de vendedor y agrupación en los tres modelos.

Para ejecutarlos por primera vez, usar una base de pruebas nueva, no `devel` ni `tp_canales`:

```bash
cd ~/odoo19
docker compose -f devel.yaml -f compose.tp-canales.yaml stop odoo
docker compose -f devel.yaml -f compose.tp-canales.yaml run --rm -e PGDATABASE=tp_canales_test -e 'DB_FILTER=^tp_canales_test$' odoo odoo -d tp_canales_test -i sale_channel_tp --without-demo=all --test-enable --test-tags /sale_channel_tp --stop-after-init
docker compose -f devel.yaml -f compose.tp-canales.yaml up -d
```

En siguientes ejecuciones sobre esa base ya instalada, cambiar `-i sale_channel_tp` por `-u sale_channel_tp`. La clase usa las utilidades oficiales de pruebas de Contabilidad para preparar cuentas y diarios de prueba; no utiliza la configuración comercial real.

Cuando se retomen las pruebas manuales, crear dos canales, confirmar pedidos en cada uno, verificar almacén y canal en sus entregas, crear facturas y verificar diario/canal, y buscar/agrupar los tres documentos. Probar también código duplicado y cambio de canal después de confirmar. La validación manual queda aplazada por pedido del usuario.

## Conceptos técnicos para repasar

- Módulo/addon: paquete que agrega o extiende funcionalidades de Odoo.
- Dependencia: módulo que debe cargarse antes para disponer de sus modelos y funcionalidades.
- Modelo: definición de una entidad de negocio; aquí `sale.channel.tp` representa los canales.
- Herencia de extensión: ampliación de un modelo existente; aquí pedidos, transferencias y asientos/facturas.
- Many2one: relación de varios registros con un registro de otro modelo, por ejemplo muchos pedidos con un canal.
- Campo obligatorio: dato que debe completarse para guardar un registro.
- Campo computado almacenado: valor derivado de otros campos y persistido en la base de datos.
- Dependencias de cálculo: campos cuyos cambios provocan la recomputación de un valor.
- Campo relacionado almacenado: valor obtenido recorriendo relaciones y guardado para búsquedas y agrupaciones eficientes.
- Restricción SQL: regla de integridad aplicada por PostgreSQL; aquí la unicidad global del código.
- Restricción Python: validación de reglas de negocio ejecutada por el ORM.
- Dominio: expresión que limita los registros visibles o seleccionables. No sustituye una validación del servidor.
- ACL: permisos por modelo para leer, crear, editar y eliminar.
- Regla de registros: restricción sobre los registros concretos a los que un usuario puede acceder.
- Multicompañía: separación y coherencia de datos pertenecientes a distintas compañías.
- Vista heredada/XPath: adaptación de una pantalla existente mediante puntos de inserción o modificación.
- Acción de ventana: definición de la pantalla y modelo que abre un menú.
- Diario de ventas: registro contable que organiza las facturas de clientes y su numeración/configuración.
- Almacén/depósito: estructura logística desde la cual se organiza el abastecimiento y despacho de productos.
- Presupuesto/pedido: propuesta comercial y su confirmación para gestionar venta, entrega y facturación.
- Transferencia/entrega: documento de inventario que registra movimientos de productos.
- Factura en borrador: documento contable aún no publicado.
- Claves de agrupación: valores que deben coincidir para combinar pedidos en una misma factura.
- Prueba aislada: comprobación de lógica con sustitutos de dependencias, sin ejecutar la plataforma completa.
- Prueba de integración: comprobación del comportamiento con el ORM y los módulos reales de Odoo.

## Referencias técnicas verificadas

- Odoo 19, modelo de pedidos y agrupación de facturas: https://github.com/odoo/odoo/blob/19.0/addons/sale/models/sale_order.py
- Integración de almacenes con ventas: https://github.com/odoo/odoo/blob/19.0/addons/sale_stock/models/sale_order.py
- Enlace de entregas con pedidos en Odoo 19: https://github.com/odoo/odoo/blob/19.0/addons/sale_stock/models/stock.py
- Vistas estándar de ventas: https://github.com/odoo/odoo/blob/19.0/addons/sale/views/sale_order_views.xml
- Preparación contable para pruebas: https://github.com/odoo/odoo/blob/19.0/addons/account/tests/common.py
