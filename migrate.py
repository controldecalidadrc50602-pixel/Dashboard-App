import sqlite3
import json

conn = sqlite3.connect('dashboard.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE clients ADD COLUMN kpi_modules JSON;")
    print("Added kpi_modules column to clients")
except Exception as e:
    print("clients.kpi_modules:", e)

try:
    cursor.execute("ALTER TABLE monthly_reports ADD COLUMN extra_data JSON;")
    print("Added extra_data column to monthly_reports")
except Exception as e:
    print("monthly_reports.extra_data:", e)

default_modules = json.dumps(["chat_sales", "appointments", "calls", "quality_kidoz"])
cursor.execute("UPDATE clients SET kpi_modules = ? WHERE kpi_modules IS NULL;", (default_modules,))

conn.commit()
conn.close()
print("Migration completed successfully!")
