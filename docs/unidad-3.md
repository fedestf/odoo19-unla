# Unidad 3 — Asistentes, reportes, cron, correo, Pytest y traducciones

**Avance de implementación: 6/6 temas. Validación en la VM: 0/6 completados; 6 pendientes.** Se ejecutaron 23 casos con Pytest en el entorno de desarrollo. Las nueve pruebas de integración de Odoo están preparadas, no ejecutadas aquí. Estas cantidades no equivalen a seis temas validados en la interfaz.

La página 21 de la guía enumera seis temas sin consignas funcionales detalladas. Se concretaron con funciones de práctica sobre Inmobiliaria. Si la cátedra agrega ejercicios específicos, habrá que contrastarlos con ese enunciado nuevo.

## Instalación

Se agregó el addon `real_estate_training`, dependiente de `real_estate` y `mail`. Extiende las Unidades 1 y 2 sin necesitar `estate_account` para sus funciones de práctica. No reemplaza su instalación ni sus pruebas pendientes.

En la terminal de Ubuntu:

```bash
cd ~/odoo19
git pull --ff-only
docker compose stop odoo
```

Si todavía no se aplicaron las restricciones de la Unidad 2, ejecutar primero su comprobación de duplicados:

```bash
docker compose run --rm -T odoo odoo shell -d devel --no-http < scripts/check_unit2_data.py
```

Si informa duplicados, detenerse y resolverlos desde Odoo antes de actualizar. No se borran ni renombran datos automáticamente.

```bash
docker compose run --rm odoo odoo -d devel -u real_estate -i real_estate_training --stop-after-init
invoke start
```

Recargar con Ctrl+Shift+R. Si se quiere completar también la instalación contable de la Unidad 2, seguir `unidad-2-cierre.md`; el comando anterior no instala estate_account. Los servicios de MailHog y PostgreSQL ya están definidos en el entorno de desarrollo existente.

## 1/6 — Asistentes

### Función implementada

El botón **Asignar vendedor** abre un diálogo para elegir un usuario interno activo y asignarlo a una o varias propiedades. También aparece como acción contextual para las propiedades seleccionadas en la lista. Rechaza lotes que incluyan propiedades vendidas o canceladas antes de escribir ninguna.

Solo los Managers tienen ACL sobre el asistente. El método también comprueba el grupo en el servidor y respeta los permisos de escritura de propiedades. No basta con ocultar el botón.

### Conceptos

- **Wizard/asistente:** formulario temporal que recoge datos para ejecutar una operación.
- **TransientModel:** modelo cuyos registros se guardan temporalmente y se limpian automáticamente. No significa que nunca use la base. Normalmente un usuario solo puede acceder a los transitorios que creó.
- **target=new:** abre la acción en un diálogo.
- **active_model/active_ids:** contexto que comunica desde qué modelo y registros se abrió el asistente; debe verificarse antes de interpretar los IDs.
- **default_get:** obtiene valores iniciales. Aquí prepara la selección, pero el permiso se vuelve a comprobar al aplicar.
- **special=cancel:** cierra el diálogo sin ejecutar la operación de asignación.

### Prueba en Odoo

Como Manager, seleccionar dos propiedades nuevas en la lista y abrir Acción → Asignar vendedor. Elegir un usuario interno y aplicar. Revisar Más info. en ambas. Repetir con una propiedad cancelada: debe mostrar error sin cambiar las demás. Como Vendedor, no debe permitirse ejecutar esta acción ni invocando el método directamente.

## 2/6 — QWeb y reportes

### Función implementada

**Imprimir → Ficha de propiedad** genera una ficha por propiedad seleccionada con datos generales, descripción y tabla de ofertas. Utiliza el encabezado y pie de la compañía mediante `web.external_layout`.

### Conceptos

- **QWeb:** motor de plantillas XML/HTML de Odoo.
- **ir.actions.report:** acción que conecta modelo, plantilla y tipo de salida.
- **qweb-pdf:** salida PDF a partir del HTML renderizado; requiere que el motor PDF de Odoo esté disponible.
- **docs:** recordset de registros elegidos para imprimir.
- **t-call:** reutiliza otra plantilla, como el contenedor y el diseño externo.
- **t-foreach/t-as:** recorre una colección y nombra el registro actual.
- **t-field:** presenta un campo con formato según su tipo. Los valores de usuario se escapan; no se usa t-raw.
- **t-if/t-else:** muestran contenido según una condición, incluida la ausencia de ofertas.
- **binding_model_id:** vincula el reporte con el menú Imprimir del modelo.

### Prueba en Odoo

Abrir una propiedad y usar Imprimir → Ficha de propiedad. Verificar nombres, importes, ofertas y paginación. Imprimir varias desde la lista. Probar una descripción con caracteres como `<` para comprobar que se muestran como texto y no se ejecuta HTML arbitrario. La prueba automatizada de integración verifica HTML; la generación de PDF y su aspecto deben comprobarse en la VM.

## 3/6 — Acciones planificadas

### Función implementada

El cron **Inmobiliaria - Resumen diario de práctica** registra cantidades de propiedades, disponibles, ofertas y ofertas pendientes. Guarda o actualiza un único resumen por día. Se consulta en **Inmobiliaria → Ajustes → Resúmenes diarios**; **Generar resumen de hoy** permite probar sin esperar al día siguiente.

El cron está activo y ejecuta una vez al día. Usa el usuario técnico raíz para contar todos los registros de esta base de práctica; los resúmenes son visibles solo para Managers. Los modelos originales no separan propiedades por compañía: los totales no se presentan como estadísticas aisladas por empresa. La fecha sigue el contexto del usuario ejecutor. En una implantación real se elegiría un usuario de servicio y alcance adecuados.

El resumen no cambia propiedades ni ofertas, no borra registros y no manda correo.

### Conceptos

- **ir.cron:** modelo de trabajos periódicos ejecutados por el servidor.
- **Usuario ejecutor:** determina los permisos y contexto de la acción.
- **Intervalo:** frecuencia definida por cantidad y unidad temporal.
- **nextcall:** próxima fecha de ejecución, gestionada por el planificador.
- **Idempotencia diaria:** ejecutar otra vez el mismo día actualiza el mismo resumen, en vez de duplicarlo.
- **noupdate:** preserva configuraciones cargadas como datos cuando se actualiza el módulo; cambios manuales de calendario no se restablecen automáticamente.

### Prueba en Odoo

Ir a Resúmenes diarios, generar dos veces y comprobar un registro para la fecha actual con cantidades coherentes. En Ajustes → Técnico → Automatización → Acciones planificadas buscar la acción, revisar frecuencia y ejecutar manualmente. No hace falta esperar 24 horas. La VM y el servidor deben estar en ejecución para que el cron se ejecute normalmente.

## 4/6 — MailHog

### Función implementada

El botón **Prueba de MailHog** envía, solo al presionarlo, un mensaje de prueba a `odoo-study@localhost.test`, con remitente `training@localhost.test`. Usa un servidor dedicado `smtp:1025`, sin credenciales ni cifrado, correspondiente al servicio MailHog del Compose de desarrollo. La bandeja se abre dentro de Ubuntu en `http://localhost:19025`.

El código comprueba ese destino SMTP y no usa un servidor de producción como alternativa. El destinatario no se toma del comprador ni de contactos. No se envía correo desde cron. Si alguien modifica host, puerto, autenticación o credenciales, el botón rechaza el envío hasta restablecer la configuración local.

El acceso al botón exige Manager en el servidor. Solo se eleva la operación técnica de correo para este mensaje de destino fijo; no se elevan búsquedas de propiedades ni se permite elegir destinatarios arbitrarios. El nombre de la propiedad se escapa antes de incorporarlo al cuerpo HTML.

### Conceptos

- **SMTP:** protocolo de entrega de correo; el puerto 1025 es el capturador interno de esta práctica.
- **MailHog:** servidor de prueba que captura mensajes para inspeccionarlos sin entregarlos a personas reales.
- **ir.mail_server:** configuración de salida SMTP en Odoo.
- **mail.mail:** registro de un correo saliente y su estado de entrega.
- **Escape HTML:** convierte caracteres especiales de datos en texto seguro, evitando interpretarlos como etiquetas o scripts.
- **Entrega SMTP y persistencia:** son efectos distintos. Una entrega SMTP ya realizada no se deshace con rollback de la base. Aquí el mensaje solo se dirige al capturador local.

### Prueba en Odoo

Abrir una propiedad como Manager, pulsar Prueba de MailHog y entrar en la bandeja local. Revisar asunto, remitente, destinatario y cuerpo. Si el servicio está detenido, iniciar el entorno con invoke start; no cambiar el servidor por un SMTP externo para hacer pasar la prueba. Las pruebas automáticas reemplazan send por un doble y no abren conexiones SMTP.

## 5/6 — Pytest y pruebas de integración

### Pruebas ejecutadas aquí

**23 casos con Pytest aprobados.** Incluyen reasignación múltiple, rechazo de lotes cerrados sin escritura parcial, permisos de Manager, selección de usuario, ruta SMTP fija, rechazo de otras configuraciones antes de crear correo, escape HTML, actualización del resumen diario, metadatos de cron y reporte, archivos del manifiesto y compilación de ambos catálogos de traducción.

Se ejecutaron métodos reales con dobles de sus dependencias y comprobaciones de archivos. Esto no prueba que Odoo cargue vistas ni que PostgreSQL aplique sus reglas.

Para repetir sin Odoo desde la raíz del repositorio:

```bash
python3 -m venv .venv-unit3
.venv-unit3/bin/python -m pip install -r tests_unit3/requirements.txt
.venv-unit3/bin/python -m pytest tests_unit3 -q
```

El entorno virtual es independiente de los paquetes del sistema y del contenedor. No hace falta activar el entorno cuando se invoca su ejecutable directamente.

### Integración preparada, pendiente en la VM

El addon incluye nueve pruebas TransactionCase: selección inicial, reasignación, bloqueo sin cambios parciales, acceso del Vendedor, renderizado QWeb HTML, actualización de resumen, configuración del cron, correo con SMTP simulado y rechazo de servidor modificado. Ejecutarlas en una base de prueba nueva, no en devel:

```bash
docker compose run --rm odoo odoo -d unidad3_test -i real_estate_training --test-enable --test-tags /real_estate_training --without-demo=all --stop-after-init
```

Se necesita poder crear esa base. No usar resetdb ni borrar la base de trabajo. Los tests no envían correo real y se revierten dentro del aislamiento de Odoo. Si se vuelve a ejecutar sobre una base de prueba ya instalada, usar `-u real_estate_training` en lugar de `-i`.

### Conceptos

- **Caso de prueba:** prepara un escenario, ejecuta una operación y compara con el resultado esperado.
- **assert:** expresa una condición que debe cumplirse.
- **Parametrización:** ejecuta un caso con varias entradas; explica por qué hay más casos que funciones de prueba.
- **Doble/mock:** sustituye una dependencia, como SMTP, para observar llamadas sin producir efectos externos.
- **Prueba de integración:** usa el ORM y la base reales para verificar componentes en conjunto.
- **TransactionCase:** infraestructura de Odoo para pruebas con aislamiento transaccional.

## 6/6 — Traducciones

Se incluyen catálogos `i18n/es.po` e `i18n/es_AR.po`, con 45 mensajes por catálogo: etiquetas, botones, acciones, reporte y mensajes Python. La fuente nueva se mantiene en inglés para poder observar el cambio de idioma. Los campos y opciones de real_estate conservan el idioma en que fueron definidos anteriormente.

### Conceptos

- **Internacionalización/i18n:** preparar textos para que puedan traducirse, separando texto fuente de su traducción.
- **Localización:** adaptación a idioma y convenciones regionales; no equivale por sí sola a instalar un plan contable fiscal.
- **_():** marca cadenas Python traducibles y obtiene la versión correspondiente al idioma del entorno.
- **Archivo PO:** catálogo de gettext con msgid (fuente), msgstr (traducción) y referencias al lugar donde se usa.
- **Idioma y contexto:** el usuario y el entorno determinan qué traducción se consulta.
- **Traducción de interfaz:** no traduce automáticamente valores libres guardados por usuarios, como nombres de propiedades.

### Prueba en Odoo

Con Español de Argentina instalado y elegido en Preferencias, revisar Asignar vendedor, Resúmenes diarios y Ficha de propiedad. Cambiar a inglés y comprobar sus nombres fuente. Si el idioma se instala después del módulo, actualizar el módulo para importar sus catálogos. La compilación gettext se verificó aquí; la importación y visualización efectiva en Odoo quedan pendientes.

## Cierre y límites de validación

| Tema | Código | Prueba local | Prueba real pendiente |
| --- | --- | --- | --- |
| Asistente | Preparado | Lógica, permisos y lote | Diálogo, guardado y ACL ORM |
| QWeb/reporte | Preparado | XML y estructura | HTML ORM y PDF visible |
| Cron | Preparado | Configuración y reutilización diaria | Ejecución del planificador |
| MailHog | Preparado | Payload, escape y ruta | Captura SMTP local |
| Pytest | Preparado | 23 casos aprobados | Nueve TransactionCase |
| Traducciones | Preparado | Dos PO compilados | Importación y cambio de idioma |

No se ejecutaron pruebas en tu VM desde este chat. Instalar el módulo y recorrer estas comprobaciones permite cerrar los 6/6 con evidencia real.

## Fuentes técnicas

- [Reportes QWeb de Odoo 19](https://www.odoo.com/documentation/19.0/developer/reference/backend/reports.html).
- [Acciones y acciones planificadas](https://www.odoo.com/documentation/19.0/developer/reference/backend/actions.html).
- [Pruebas de Odoo](https://www.odoo.com/documentation/19.0/developer/reference/backend/testing.html).
- [Traducciones](https://www.odoo.com/documentation/19.0/developer/howtos/translations.html).
- [Pytest](https://docs.pytest.org/en/stable/).
- Código oficial consultado: `ir_cron.py`, `ir_mail_server.py`, `ir_actions.py`, `ir_actions_report.py` y `mail_mail.py` de la rama 19.0 de odoo/odoo.
