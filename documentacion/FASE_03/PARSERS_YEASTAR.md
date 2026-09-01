# 📞 FASE 03 — Catalogación y Parser Genérico Yeastar

## Estado de Verificación
`NO VERIFICADO — REQUIERE ARCHIVO DE MUESTRA`

## Arquitectura de Adaptación
Para evitar inventar esquemas ficticios o campos arbitrarios:
- Los reportes Yeastar se procesan mediante el `GenericParser` (`generic-v1.0`).
- Se mantiene el registro inmutable en `NormalizedRecord` con `raw_data` que contiene todas las columnas detectadas.
- Los parsers específicos para `Extension`, `Call Center`, `Call Activity` y `AI Reports` se acoplarán heredando de `BaseParser` una vez se entreguen archivos muestra reales.
