# ------------------------------------------------------
# IMPORTS PRINCIPALES (NO IMPORTES NADA LOCAL TODAVÍA)
# ------------------------------------------------------
import asyncio
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND, HTTP_401_UNAUTHORIZED
import os, configparser


from datetime import datetime


# ------------------------------------------------------
# FASTAPI APP + CONFIG BÁSICA
# ------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")

config = configparser.ConfigParser()
config.read(CONFIG_PATH)

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

from services.unifi import unifi_guest_approve
actualver = "1.12.6"
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
# AUTH BÁSICA PARA /admin
# ------------------------------------------------------
security = HTTPBasic()


def check_admin(credentials: HTTPBasicCredentials = Depends(security)):
    user_ok = credentials.username == config["Admin"].get("username")
    pass_ok = credentials.password == config["Admin"].get("password")
    if not (user_ok and pass_ok):
        # FastAPI maneja el header WWW-Authenticate
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="No autorizado",
            headers={"WWW-Authenticate": 'Basic realm="Login Required"'},
        )
    return True


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

    # status: None | "success" | "error" | "error_unifi"
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
# INDEX (POST) – guarda en DB y autoriza en Unifi
# ------------------------------------------------------
@app.post("/", response_class=HTMLResponse)
async def index_post(
    request: Request,
    fullname: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
):
    # Query params UniFi
    qs = dict(request.query_params)

    if not fullname or not is_valid_email(email):
        # redirigimos con status=error
        url = app.url_path_for("index") + "?status=error"
        return RedirectResponse(url=url, status_code=HTTP_302_FOUND)

    signup = {
        "fullname": fullname.strip(),
        "email": email.strip(),
        "phone": phone.strip(),
        "client_mac": qs.get("id") or qs.get("mac") or "",
        "client_ip": qs.get("ip", ""),
        "ap_mac": qs.get("ap") or qs.get("ap_mac") or "",
    }

    # 1) Guardar en DB
    try:
        await asyncio.to_thread(db_insert_signup, signup)
    except Exception as e:
        log_error(f"Error insertando en DB: {e}")
        url = app.url_path_for("index") + "?status=error"
        return RedirectResponse(url=url, status_code=HTTP_302_FOUND)

    # 2) Autorizar en Unifi (microservicio interno)
    ok_unifi = False
    try:
        ok_unifi = await asyncio.to_thread(
            unifi_guest_approve,
            signup["client_mac"],
            signup["ap_mac"],
            qs.get("ssid", ""),
        )
    except Exception as e:
        log_error(f"ERROR en unifi_guest_approve: {e}")
        ok_unifi = False

    status = "success" if ok_unifi else "error_unifi"
    url = app.url_path_for("index") + f"?status={status}"
    return RedirectResponse(url=url, status_code=HTTP_302_FOUND)


# ------------------------------------------------------
# RUTAS DE CAPTIVE PORTAL UNIFI (igual que antes)
# ------------------------------------------------------
@app.get("/guest/s/{site}/")
async def guest_redirect_site(site: str, request: Request):
    # Mantener query params y redirigir a "/"
    qs = request.url.query
    base = app.url_path_for("index")
    target = f"{base}?{qs}" if qs else base
    return RedirectResponse(url=target, status_code=HTTP_302_FOUND)


@app.get("/guest/s/default/")
async def guest_redirect_default(request: Request):
    qs = request.url.query
    base = app.url_path_for("index")
    target = f"{base}?{qs}" if qs else base
    return RedirectResponse(url=target, status_code=HTTP_302_FOUND)


# ------------------------------------------------------
# ADMIN PANEL
# ------------------------------------------------------
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, _: bool = Depends(check_admin)):
    registros = db_get_all()
    # admin.html ya espera 'registros' y usa request para el link CSV :contentReference[oaicite:1]{index=1}
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "registros": registros,
        },
    )


# ------------------------------------------------------
# EXPORT CSV
# ------------------------------------------------------
@app.get("/admin/export")
async def export_csv(_: bool = Depends(check_admin)):
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

@app.get("/test")
async def test_unifi(mac: str = ""):
    if not mac:
        return {"error": "Falta ?mac=AA:BB:CC:DD:EE:FF"}

    try:
        ok = await asyncio.to_thread(unifi_guest_approve, mac, "", "")
        return {
            "mac": mac,
            "authorized": ok
        }
    except Exception as e:
        return {
            "mac": mac,
            "authorized": False,
            "error": str(e)
        }

# ------------------------------------------------------
# MAIN (solo si corres python main.py)
# ------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    port = int(config["Admin"].get("port", "80"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
