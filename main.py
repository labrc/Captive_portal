# ------------------------------------------------------
# IMPORTS PRINCIPALES (NO IMPORTES NADA LOCAL TODAVÍA)
# ------------------------------------------------------
import asyncio
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, configparser
from fastapi import Cookie
from itsdangerous import URLSafeSerializer, BadSignature
from database import TABLE_NAME



from datetime import datetime
actualver = "1.12.13"

# ------------------------------------------------------
# FASTAPI APP + CONFIG BÁSICA
# ------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")

config = configparser.ConfigParser()
config.read(CONFIG_PATH)

SECRET_KEY = os.getenv("SECRET_KEY", "ClaveSceretisima")
serializer = URLSafeSerializer(SECRET_KEY, salt="admin-session")


app = FastAPI(title="Captive Portal", version="v2-fastapi-uvicorn")


# 🔥 MONTAR STATIC ANTES DE CUALQUIER IMPORT LOCAL
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
for r in app.routes:
    print("ROUTE:", r.name, r.path)

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ------------------------------------------------------
# AHORA PODEMOS IMPORTAR MÓDULOS LOCALES
# ------------------------------------------------------
from database import (
    db_init,
    db_insert_signup,
    safe_export_and_cleanup,   # o auto_export_and_cleanup
    db_get_all,
    count_records,
    generate_csv,
    CLEANUP_ON_EXPORT,
)
from database import auto_export_and_cleanup

# ------------------------------------------------------
# LOGGING SENCILLO
# ------------------------------------------------------
DEBUG_MODE = config["Admin"].get("debug", "no").lower() == "yes"
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "log.txt")


def log_info(msg: str):
    if not DEBUG_MODE:
        return
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final = f"[{ts}] INFO: {msg}"
    print(final, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(final + "\n")
    except Exception:
        pass


def log_error(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final = f"[{ts}] ERROR: {msg}"
    print(final, flush=True)
    if DEBUG_MODE:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(final + "\n")
        except Exception:
            pass


print(
    "....................................................\n"
    f"..................    {actualver}    ..................\n"
    "....................................................",
    flush=True,
)

# Inicializar DB al levantar
db_init()

# ------------------------------------------------------
# AUTH  PARA /admin
# ------------------------------------------------------
def is_admin_logged(session_cookie: str | None) -> bool:
    if not session_cookie:
        return False
    try:
        data = serializer.loads(session_cookie)
        return data.get("role") == "admin"
    except BadSignature:
        return False


def require_admin(session_cookie: str | None = Cookie(default=None, alias="admin_session")):
    if not is_admin_logged(session_cookie):
        # redirigir a login
        raise HTTPException(
            status_code=302,
            headers={"Location": "/login"}
        )


# ------------------------------------------------------
# VALIDACIÓN EMAIL (igual que antes)
# ------------------------------------------------------
import re


def is_valid_email(email: str) -> bool:
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email.strip()))


# ------------------------------------------------------
# INDEX (GET)
# ------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, status: str | None = None):
    hotel_name = config["General"].get("hotel_name", "Portal Wi-Fi")
    logo_file = config["General"].get("logo_file", "logo.jpg")
    redirect_url = config["Redirect"].get("default_url")
    redirect_delay = int(config["Redirect"].get("redirect_delay", "3"))
    default_languaje = config["General"].get("default_language")

    # status: None | "success" | "error"
    context = {
        "request": request,
        "hotel_name": hotel_name,
        "logo_file": logo_file,
        "redirect_url": redirect_url,
        "redirect_delay": redirect_delay,
        "status": status,  # tendrás que usarlo en index.html si querés mensajes
    }
    return templates.TemplateResponse("index.html", context)


# ------------------------------------------------------
# INDEX (POST) – guarda en DB
# ------------------------------------------------------
@app.post("/", response_class=HTMLResponse)
async def index_post(
    request: Request,
    fullname: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
):
    # Query params

    if not fullname or not is_valid_email(email):
        # redirigimos con status=error
        url = app.url_path_for("index") + "?status=error"
        return RedirectResponse(url=url, status_code=302)


    # 1) Guardar en DB
    try:
        await db_insert_signup_async(signup)
    except Exception:
        db_init()
        await db_insert_signup_async(signup)


    status = "success"
    url = app.url_path_for("index") + f"?status={status}"
    return RedirectResponse(url=url, status_code=302)



# ------------------------------------------------------
# ADMIN PANEL
# ------------------------------------------------------
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, _: bool = Depends(require_admin)):
    registros = db_get_all()
    # admin.html ya espera 'registros' y usa request para el link CSV :contentReference[oaicite:1]{index=1}
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "registros": registros,
        },
    )

from fastapi.responses import HTMLResponse, RedirectResponse

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "hotel_name": config["General"].get("hotel_name", "Portal Wi-Fi"),
        },
    )

@app.post("/login")
async def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    cfg_user = config["Admin"].get("username")
    cfg_pass = config["Admin"].get("password")

    if username == cfg_user and password == cfg_pass:
        token = serializer.dumps({"role": "admin", "user": username})
        resp = RedirectResponse(url="/admin", status_code=302)
        # Cookie segura (en HTTP local podés dejar secure=False)
        resp.set_cookie(
            "admin_session",
            token,
            httponly=True,
            samesite="Lax",
            max_age=8 * 3600,
        )
        return resp

    # Login incorrecto
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "hotel_name": config["General"].get("hotel_name", "Portal Wi-Fi"),
            "error": "Usuario o contraseña incorrectos",
        },
        status_code=401
    )


@app.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie("admin_session")
    return resp

# ------------------------------------------------------
# DB nueva
# ------------------------------------------------------
import asyncpg

db_pool: asyncpg.Pool | None = None

@app.on_event("startup")
async def startup_event():
    global db_pool
    db_pool = await asyncpg.create_pool(
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "portal"),
        password=os.getenv("DB_PASS", "portal123"),
        database=os.getenv("DB_NAME", "captive_portal"),
        min_size=1,
        max_size=5,
    )

async def db_insert_signup_async(data: dict):
    global db_pool
    if db_pool is None:
        # fallback por si algo falla
        return await asyncio.to_thread(db_insert_signup, data)

    async with db_pool.acquire() as conn:
        await conn.execute(f"""
            INSERT INTO {TABLE_NAME} (fullname, email, phone, client_mac, client_ip, ap_mac)
            VALUES ($1, $2, $3, $4, $5, $6)
        """,
        data["fullname"],
        data["email"],
        data.get("phone", ""),
        data.get("client_mac", ""),
        data.get("client_ip", ""),
        data.get("ap_mac", "")
        )

# ------------------------------------------------------
# EXPORT CSV
# ------------------------------------------------------
@app.get("/admin/export")
async def export_csv(_: bool = Depends(require_admin)):
    if CLEANUP_ON_EXPORT:
        filepath = safe_export_and_cleanup()
        if not filepath:
            return Response("Error exportando CSV.", media_type="text/plain")

        with open(filepath, "r", encoding="utf-8") as f:
            csv_data = f.read()

        filename = os.path.basename(filepath)
        return Response(
            csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:
        rows = db_get_all()
        csv_data = generate_csv(rows)
        return Response(
            csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="signups_manual.csv"'
            },
        )


# ------------------------------------------------------
# MAIN
# ------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    port = int(config["Admin"].get("port", "80"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
