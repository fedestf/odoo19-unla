TP - Canales de venta (Parte 1)
==============================

Módulo para Odoo 19 Community que permite configurar canales con depósito y
diario de ventas. Los pedidos requieren un canal, usan su almacén y diario y lo
trasladan a entregas y facturas. Incluye búsquedas, agrupaciones, permisos y
controles de coherencia.

La guía de instalación, el alcance, las decisiones y el estado de las pruebas
están en ``docs/tp-canales-parte-1.md`` en la raíz del repositorio.

Instalar en una base nueva (``tp_canales``). Este módulo es independiente de los
ejercicios de inmobiliaria. La gestión de crédito se definirá al recibir la
parte 2 del enunciado.

Para instalar y cargar automáticamente los ejemplos desde la VM, ejecutar
``python3 scripts/preparar_tp_canales.py`` desde la raíz del repositorio.
El preparador solo trabaja sobre la base ``tp_canales``.
