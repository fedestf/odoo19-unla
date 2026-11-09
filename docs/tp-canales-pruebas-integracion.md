# Resultado de las pruebas reales del TP de canales

Fecha: 9 de noviembre de 2026.

**Resultado final: 22 pruebas de integración, 0 fallos y 0 errores.** Además, las 33 pruebas aisladas previas siguen pasando.

## Entorno ejecutado

- Odoo OCB Community 19.0, rama `19.0` de `OCA/OCB`, commit `032ad6e5136094f681b8e5599681acc1b8f3b15f`.
- Python 3.12.14 en Windows, con dependencias en una carpeta exclusiva para esta ejecución.
- PostgreSQL 17.6, clúster nuevo y separado, escuchando solo en `127.0.0.1:25432` mientras se ejecutaban las pruebas.
- Base exclusiva `tp_canales_integration`, creada para las pruebas. No se usaron ni modificaron las bases `devel` o `tp_canales` de la VM.
- Instalación real de `sale_channel_tp` y sus dependencias. Se cargaron sus modelos, permisos, restricciones y vistas XML.
- Pruebas `post_install` mediante el ejecutor oficial de Odoo. Las pruebas usan transacciones y utilidades contables oficiales; crean registros reales de pedidos, entregas y facturas y los revierten al finalizar cada caso.
- No se sustituyó el ORM por mocks en estas 22 pruebas. Sí se conservan por separado las 33 pruebas aisladas originales.

El servidor PostgreSQL temporal se detuvo después de finalizar. Se conservaron el entorno y los registros locales para reproducir la ejecución.

## Las siete comprobaciones pendientes

| Comprobación | Caso ejecutado | Resultado |
| --- | --- | --- |
| Agrupar entregas por canal | `test_group_deliveries_by_channel` | Correcto: dos canales separados con su cantidad de entregas. |
| Agrupar facturas por canal | `test_group_invoices_by_channel` | Correcto: dos canales separados con su cantidad de facturas. |
| Filtrar pedidos por canal | `test_filter_orders_by_channel` | Correcto: cada filtro devuelve solo el pedido de ese canal. |
| Filtrar entregas por canal | `test_filter_deliveries_by_channel` | Correcto: cada filtro devuelve solo la entrega de ese canal. |
| Filtrar facturas por canal | `test_filter_invoices_by_channel` | Correcto: cada filtro devuelve solo la factura de ese canal. |
| Bloquear cambio de canal en un pedido confirmado | `test_channel_locked_after_confirmation` | Correcto: el servidor rechaza la modificación. |
| Bloquear cambios de configuración de un canal utilizado | `test_configuration_cannot_change_after_use` | Correcto: se rechazaron tanto el cambio de diario como el de depósito. |

La agrupación se ejecutó con `_read_group` y los filtros con `search`, contra registros reales guardados en PostgreSQL. Las restricciones se probaron intentando las escrituras y verificando las excepciones esperadas.

## Otros comportamientos incluidos en los 22 casos

Código normalizado y único; código vacío rechazado; canal obligatorio; diario de ventas y compañía coherentes; cálculo de depósito y diario al cambiar canal; formulario de Odoo con cambio de depósito; rechazo de depósito manual incompatible; entrega vinculada al pedido y al almacén correcto; canal archivado rechazado al confirmar; factura con canal y diario correctos; separación de facturas entre canales, incluso con un mismo diario; agrupación de pedidos compatibles del mismo canal; vendedor con lectura y sin escritura de canales; agrupación en los tres modelos.

## Ajustes realizados al ejecutar por primera vez

Se corrigió la preparación de las pruebas: el fixture contable estándar no asignaba al usuario el rol Administrador de Ventas requerido para crear canales. La suite ahora agrega los roles necesarios durante su preparación; el caso de vendedor sigue utilizando un usuario independiente sin permiso de configuración.

También se corrigieron expectativas de excepciones en los tests: al llamar directamente al ORM, las restricciones SQL de código único y canal obligatorio producen `IntegrityError`; la capa de la aplicación las convierte en mensajes de validación para la interfaz. El helper `assertRaises` de Odoo requiere una clase de excepción, no una tupla.

Se agregaron cinco casos explícitos para filtros y agrupaciones que, junto a los dos casos de bloqueo existentes, cubren exactamente las siete comprobaciones solicitadas. No se modificó la lógica funcional de los modelos para conseguir el resultado.

## Evidencia

El registro final está en `docs/evidencias/tp-canales-integracion.log`. Se reemplazaron las rutas absolutas de Windows por marcadores para evitar publicar ubicaciones personales.

La salida final del ejecutor indica:

```text
22 post-tests
0 failed, 0 error(s) of 22 tests when loading database 'tp_canales_integration'
```

El contador adicional de estadísticas internas muestra 24 porque incluye preparación/limpieza de la suite; el resultado de casos es 22. Los mensajes SQL de restricción y de acceso denegado que aparecen durante los casos negativos son los rechazos que esos casos esperan, no fallos de la ejecución final.

## Reproducir en la VM

En una base de prueba nueva, usar:

```bash
cd ~/odoo19
git pull --ff-only
docker compose -f devel.yaml -f compose.tp-canales.yaml stop odoo
docker compose -f devel.yaml -f compose.tp-canales.yaml run --rm -e PGDATABASE=tp_canales_test -e 'DB_FILTER=^tp_canales_test$' odoo odoo -d tp_canales_test -i sale_channel_tp --without-demo=all --test-enable --test-tags /sale_channel_tp --stop-after-init
docker compose -f devel.yaml -f compose.tp-canales.yaml up -d
```

Si `tp_canales_test` ya tiene instalado el módulo, reemplazar `-i sale_channel_tp` por `-u sale_channel_tp`. No ejecutar estos comandos de prueba contra las bases de trabajo.

## Límites de la conclusión

Esta ejecución comprueba comportamiento real de servidor, integridad de datos, vistas cargables y un formulario mediante las herramientas de Odoo. No es una sesión automatizada haciendo clic en un navegador. La VM utiliza Linux y la configuración del proyecto indica PostgreSQL 18, mientras que esta ejecución usó Windows y PostgreSQL 17; tampoco se verificó que la VM tenga exactamente el mismo commit de OCB. Las capturas del usuario siguen siendo la evidencia visual de su instalación concreta.
