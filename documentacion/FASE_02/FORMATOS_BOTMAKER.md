# 🤖 FASE 02 — Especificación de Formatos Botmaker

## Tipos de Reportes Soportados

### 1. `users` (`users-*.tsv`)
- **Formato:** TSV (Tab Separated Values) / UTF-8
- **Campos esperados:** conversación, fecha/hora, sesión, canal, contacto, participación del agente, mensajes, tipificación.
- **Nomenclatura típica:** `users-YYYY.MM.DD-HH.MM.tsv`

### 2. `operatorsSessionsDebug` (`operatorsSessionsDebug-*.tsv`)
- **Formato:** TSV (Tab Separated Values) / UTF-8
- **Campos esperados:** sesión, usuario, inicio, fin, agente, cola, tipificación, conversaciones, respuestas, transferencias, tiempos de espera/abandono, enlace de conversación.
- **Nomenclatura típica:** `operatorsSessionsDebug-YYYY.MM.DD-HH.MM.tsv`

### 3. `sessionStartingCauses` (`sessionStartingCauses-*.tsv`)
- **Formato:** TSV (Tab Separated Values) / UTF-8
- **Campos esperados:** usuario, contacto/número, inicio de sesión, canal, usuario nuevo, plantilla/notificación, enviado, entregado, leído, respondido, fallos, timestamps.
- **Nomenclatura típica:** `sessionStartingCauses-YYYY.MM.DD-HH.MM.tsv`
