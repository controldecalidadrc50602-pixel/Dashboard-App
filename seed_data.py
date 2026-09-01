"""
Script para cargar los datos históricos del reporte Rc506 (Ene-Ago 2026)
en la base de datos. Ejecutar UNA VEZ después de iniciar la app.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal, engine
from app.models import Base, Client, MonthlyReport

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Verificar si ya existe
existing = db.query(Client).filter(Client.name == "Kidoz").first()
if existing:
    print("[SKIP] El cliente Kidoz ya existe. Saltando seed.")
    db.close()
    sys.exit(0)

# Crear cliente
client = Client(
    name="Kidoz",
    description="Cliente - Centro especializado en neurodesarrollo",
    color="#009688",
    logo_text="KZ"
)
db.add(client)
db.flush()

# Datos históricos Enero-Agosto 2026
monthly_data = [
    # month, chats, leads, sales, conf_citas, support, csat,
    # total_calls, answered, contact_rate, inbound, inb_ans, outbound, out_ans,
    # kid_opt_c, kid_opt_ch, kid_acc_c, kid_acc_ch, kid_def_c, kid_def_ch, kid_total, kid_pct
    (1,  1673, 194,  49,  980,  499, 4.78, 1226, 1031, 84.1, 50,  50,  1176, 981,  68, 62, 4, 5, 0, 0, 139, 93.5),
    (2,  1813, 232,  66,  1106, 475, 4.57,  419,  370, 88.3, 57,  56,   362, 314,  64, 67, 2, 8, 0, 0, 141, 92.9),
    (3,  2282, 410, 120,  1075, 797, 4.85,  345,  314, 91.0, 89,  84,   256, 230,  64, 83, 0, 4, 0, 0, 151, 97.4),
    (4,  3009, 440, 147,  1604, 965, 4.62,  332,  293, 88.3, 93,  92,   239, 201,  55, 67, 8, 1, 0, 0, 131, 93.1),
    (5,  3053, 386, 147,  1664,1003, 4.85,  356,  318, 89.3, 98,  98,   258, 220,  81, 80, 3, 7, 0, 0, 171, 92.4),
    (6,  2051, 336, 143,  1010, 705, 4.76,  561,  519, 92.5,119, 119,   442, 400,  69, 79, 1, 1, 0, 0, 150, 98.7),
    (7,  2299, 383, 161,  1053, 863, 4.84,  414,  371, 89.6,146, 143,   268, 228,  79, 88, 3, 4, 0, 0, 174, 96.0),
    (8,  2651, 413, 149,  1462, 776, 4.69,  206,  181, 87.9, 68,  61,   138, 120,  62, 79, 1, 1, 1, 0, 143, 98.6),
]

for row in monthly_data:
    (month, chats, leads, sales, conf, support, csat,
     total_calls, answered, contact_rate, inbound, inb_ans, outbound, out_ans,
     kid_opt_c, kid_opt_ch, kid_acc_c, kid_acc_ch, kid_def_c, kid_def_ch, kid_total, kid_pct) = row

    report = MonthlyReport(
        client_id=client.id,
        year=2026, month=month,
        chats=chats, leads=leads, sales=sales,
        appointment_confirmations=conf, support=support, csat=csat,
        total_calls=total_calls, answered_calls=answered,
        contact_rate=contact_rate,
        inbound_calls=inbound, inbound_answered=inb_ans,
        outbound_calls=outbound, outbound_answered=out_ans,
        kidoz_optimal_calls=kid_opt_c, kidoz_optimal_chats=kid_opt_ch,
        kidoz_acceptable_calls=kid_acc_c, kidoz_acceptable_chats=kid_acc_ch,
        kidoz_deficient_calls=kid_def_c, kidoz_deficient_chats=kid_def_ch,
        kidoz_total_evaluations=kid_total, kidoz_optimal_pct=kid_pct
    )
    db.add(report)

db.commit()
print(f"[OK] Cliente 'Kidoz' creado con ID={client.id}")
print(f"[OK] {len(monthly_data)} meses de datos cargados (Enero-Agosto 2026)")
db.close()
