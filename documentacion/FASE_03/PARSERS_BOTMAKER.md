# 🤖 FASE 03 — Mapeo y Parsers de Botmaker

## 1. Parser `users` (`botmaker-users-v1.0`)
- **Columnas de Origen:** `conversation`, `date`, `time`, `session`, `channel`, `contact`, `agent`, `messages`, `typification`.
- **Mapeo Aplicado:**
  - `event_id` ➔ `conversation`
  - `user_id` ➔ `contact`
  - `channel` ➔ `channel`
  - `agent` ➔ `agent`
  - `start_at` ➔ `date` + `time`
  - `messages_count` ➔ `parse_int(messages)`
  - `typification` ➔ `typification`
  - `wait_time_seconds` ➔ `NULL` (No disponible en el reporte `users`)
  - `duration_seconds` ➔ `NULL` (No disponible en el reporte `users`)

## 2. Parser `operatorsSessionsDebug` (`botmaker-operators-v1.0`)
- **Columnas de Origen:** `session`, `user`, `start`, `end`, `agent`, `queue`, `typification`, `wait`, `link`.
- **Mapeo Aplicado:**
  - `event_id` ➔ `session`
  - `user_id` ➔ `user`
  - `agent` ➔ `agent`
  - `queue` ➔ `queue`
  - `start_at` ➔ `parse_datetime(start)`
  - `end_at` ➔ `parse_datetime(end)`
  - `wait_time_seconds` ➔ `parse_duration_seconds(wait)`
  - `duration_seconds` ➔ `(end_at - start_at).total_seconds()`
  - `typification` ➔ `typification`

## 3. Parser `sessionStartingCauses` (`botmaker-sessions-v1.0`)
- **Columnas de Origen:** `user`, `contact`, `channel`, `template`, `sent`, `delivered`, `read`, `responded`, `timestamp`.
- **Mapeo Aplicado:**
  - `user_id` ➔ `user` / `contact`
  - `channel` ➔ `channel`
  - `start_at` ➔ `parse_datetime(timestamp)`
  - `is_abandoned` ➔ `NOT responded`
  - `typification` ➔ `template`
