import os
import psycopg2
import csv
from io import StringIO
from datetime import datetime
import configparser

# ------------------------------------------------------
# 📌 CARGAR CONFIG (sin interpolación)
# ------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")

config = configparser.ConfigParser(interpolation=None)
config.read(CONFIG_PATH)

MAX_RECORDS = int(config["Database"].get("max_records", "500"))
CLEANUP_ON_EXPORT = config["Database"].get("cleanup_on_export", "yes").lower() == "yes"
import re

RAW_TABLE_NAME = config["Database"].get("table_name", "signups")

def sanitize_table_name(name: str) -> str:
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
        return name
    return "signups"

TABLE_NAME = sanitize_table_name(RAW_TABLE_NAME)


EXPORT_DIR = config["Export"].get("export_dir", "exports")
DATE_FORMAT = config["Export"].get("date_format", "%Y-%m-%d_%H-%M-%S")
ABSOLUTE_PATH = config["Export"].get("absolute_export_path", "").strip()
SEPARADOR_ALTERNATIVO = (
    config["Export"].get("separador_alternativo", "false").lower() == "true"
)

CSV_DELIMITER = ";" if SEPARADOR_ALTERNATIVO else ","

# Ruta final donde guardar CSV
if ABSOLUTE_PATH:
    FINAL_EXPORT_DIR = ABSOLUTE_PATH
else:
    FINAL_EXPORT_DIR = os.path.join(BASE_DIR, EXPORT_DIR)

os.makedirs(FINAL_EXPORT_DIR, exist_ok=True)

# ------------------------------------------------------
# 🔌 CONEXIÓN A POSTGRES
# ------------------------------------------------------
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER", "portal"),
        password=os.getenv("DB_PASS", "portal123"),
        dbname=os.getenv("DB_NAME", "captive_portal")
    )

# ------------------------------------------------------
# 🧱 CREAR DB Y TABLA
# ------------------------------------------------------
def db_init():
    """Crea la base y tabla si no existen."""
    try:
        sys_conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
            user=os.getenv("POSTGRES_USER", os.getenv("DB_USER", "portal")),
            password=os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASS", "portal123")),
            dbname="postgres"
        )
        sys_conn.autocommit = True
        cur = sys_conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s",
                    (os.getenv("DB_NAME", "captive_portal"),))
        if not cur.fetchone():
            cur.execute(f"CREATE DATABASE {os.getenv('DB_NAME', 'captive_portal')}")
            print("🟢 Base de datos creada.")
        cur.close()
        sys_conn.close()
    except Exception as e:
        print(f"⚠️ Error creando/verificando DB: {e}")

    # Crear tabla principal
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id SERIAL PRIMARY KEY,
                fullname VARCHAR(200),
                email VARCHAR(200),
                phone VARCHAR(50),
                client_mac VARCHAR(50),
                client_ip VARCHAR(50),
                ap_mac VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print(f"🟢 Tabla '{TABLE_NAME}' OK.")
    except Exception as e:
        print(f"⚠️ Error creando tabla '{TABLE_NAME}': {e}")

# ------------------------------------------------------
# 📥 OBTENER TODOS LOS REGISTROS
# ------------------------------------------------------
def db_get_all():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM {TABLE_NAME} ORDER BY id DESC")
        rows = cur.fetchall()
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        db_init()
        cur.execute(f"SELECT * FROM {TABLE_NAME} ORDER BY id DESC")
        rows = cur.fetchall()
    finally:
        cur.close()
        conn.close()
    return rows

# ------------------------------------------------------
# 🔢 CONTAR REGISTROS
# ------------------------------------------------------
def count_records():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total

# ------------------------------------------------------
# ✍️ INSERTAR REGISTRO Y CHEQUEAR EXPORT
# ------------------------------------------------------
def db_insert_signup(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO {TABLE_NAME} (fullname, email, phone, client_mac, client_ip, ap_mac)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data["fullname"],
        data["email"],
        data.get("phone", ""),
        data.get("client_mac", ""),
        data.get("client_ip", ""),
        data.get("ap_mac", "")
    ))
    conn.commit()
    cur.close()
    conn.close()

    # export automático
    total = count_records()
    if total >= MAX_RECORDS:
        print(f"📦 Límite de {MAX_RECORDS} registros → Export autom.")
        auto_export_and_cleanup()

# ------------------------------------------------------
# 📝 LOG DE ERRORES
# ------------------------------------------------------
def log_db_error(msg):
    """Guarda un error en tabla 'errors'."""
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id SERIAL PRIMARY KEY,
                error TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

        cur.execute("INSERT INTO errors (error) VALUES (%s)", (msg,))
        conn.commit()
        cur.close()
        conn.close()

        print("📝 Error registrado en 'errors'.")
    except Exception as e:
        print(f"⚠️ No se pudo registrar error: {e}")

# ------------------------------------------------------
# 🧪 GENERATE CSV (para export manual)
# ------------------------------------------------------
def generate_csv(rows):
    """Convierte registros a CSV (descarga manual en /admin/export)."""
    output = StringIO()
    writer = csv.writer(output, delimiter=CSV_DELIMITER)
    writer.writerow(["ID", "Nombre", "Email", "Teléfono", "MAC", "IP", "AP MAC", "Fecha"])

    for row in rows:
        writer.writerow(row)

    return output.getvalue()

# ------------------------------------------------------
# 🛡 EXPORTACIÓN SEGURA
# ------------------------------------------------------
def safe_export_and_cleanup():
    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        # 1) Lock fuerte
        cur.execute(f"LOCK TABLE {TABLE_NAME} IN ACCESS EXCLUSIVE MODE")

        cur.execute(f"SELECT * FROM {TABLE_NAME} ORDER BY id DESC")
        rows = cur.fetchall()

        if not rows:
            conn.commit()
            return None

        # 2) CSV en memoria
        mem = StringIO()
        w = csv.writer(mem, delimiter=CSV_DELIMITER)
        w.writerow(["ID", "Nombre", "Email", "Teléfono", "MAC", "IP", "AP MAC", "Fecha"])

        for row in rows:
            if len(row) != 8:
                raise ValueError(f"Fila corrupta: {row}")
            w.writerow(row)

        csv_mem = mem.getvalue()

        # 3) Validar CSV
        test_mem = list(csv.reader(StringIO(csv_mem), delimiter=CSV_DELIMITER))
        if len(test_mem) < 2:
            raise ValueError("CSV vacío o incompleto")

        # 4) Escribir archivo
        filename = f"{TABLE_NAME}_{datetime.now().strftime(DATE_FORMAT)}.csv"
        filepath = os.path.join(FINAL_EXPORT_DIR, filename)

        with open(filepath, "w", encoding="utf-8", newline="") as f:
            f.write(csv_mem)

        # 5) Releer y verificar
        with open(filepath, "r", encoding="utf-8") as f:
            test_disk = list(csv.reader(f, delimiter=CSV_DELIMITER))

        if test_disk != test_mem:
            raise ValueError("El CSV escrito difiere del generado en memoria")

        # 6) BORRADO FINAL (solo si todo OK)
        cur.execute(f"DELETE FROM {TABLE_NAME}")
        conn.commit()

        print(f"🟢 Exportación segura OK → {filepath}")
        return filepath

    except Exception as e:
        print(f">>>>❌ ERROR exportando CSV: {e}")
        log_db_error(str(e))

        if conn:
            conn.rollback()

        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# ------------------------------------------------------
# 🚀 EXPORT AUTOMÁTICO
# ------------------------------------------------------
def auto_export_and_cleanup():
    print("📦 Export automático solicitado")
    return safe_export_and_cleanup()
