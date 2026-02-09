import os
from datetime import datetime
import configparser
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import time


# ------------------------------------------------------
# CONFIG
# ------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")

config = configparser.ConfigParser()
config.read(CONFIG_PATH)

modelo = int(config["Unifi"].get("modelo", "4"))

# Desactivar warnings SSL
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ------------------------------------------------------
# LOGGING SIMPLE
# ------------------------------------------------------
def _ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_info(msg: str):
    print(f"[{_ts()}] [UNIFI] INFO: {msg}", flush=True)


def log_error(msg: str):
    print(f"[{_ts()}] [UNIFI] ERROR: {msg}", flush=True)


# ------------------------------------------------------
# MODELO 2 — LOGIN PERSISTENTE
# ------------------------------------------------------
session2 = requests.Session()
session2.verify = False
session2_csrf = None
FAIL_COUNT = 0
MAX_FAIL = 5


def _post_retry(session, url, payload, headers=None, retries=2):
    """POST con retry + backoff para máxima estabilidad."""
    global FAIL_COUNT
    for attempt in range(retries + 1):
        try:
            r = session.post(url, json=payload, headers=headers, timeout=4)
            # reset conteo si fue bien
            if r.status_code < 500:
                FAIL_COUNT = 0
            return r
        except Exception as e:
            FAIL_COUNT += 1
            log_error(f"[POST_RETRY] Error intento {attempt+1}/{retries+1}: {e}")
            time.sleep(0.4 * (attempt + 1))  # backoff suave
    return None



def modelo2_login(ctrl, user, pwd):
    global session2_csrf

    login_url = f"{ctrl}/api/auth/login"
    payload = {"username": user, "password": pwd}

    log_info(f"[MODELO2] LOGIN → {login_url}")
    r = _post_retry(session2, login_url, payload)

    if not r:
        log_error("[MODELO2] Login FAIL: sin respuesta del controlador")
        return False

    if r.status_code != 200:
        log_error(f"[MODELO2] Login FAIL: {r.status_code} {r.text[:200]}")
        return False

    session2_csrf = (
        r.headers.get("x-csrf-token")
        or r.headers.get("x-updated-csrf-token")
        or r.headers.get("X-Csrf-Token")
    )
    log_info(f"[MODELO2] CSRF → {session2_csrf}")
    return True


def modelo2_unauthorize(ctrl, site, mac):
    url = f"{ctrl}/proxy/network/api/s/{site}/cmd/stamgr"
    headers = {"X-Csrf-Token": session2_csrf}
    payload = {"cmd": "unauthorize-guest", "mac": mac}

    r = _post_retry(session2, url, payload, headers=headers)

    if not r:
        log_error("[MODELO2] UNAUTH falló sin respuesta")
        return False

    log_info(f"[MODELO2] UNAUTH → {r.status_code}")

    return True


def modelo2_authorize(ctrl, site, mac, minutes):
    global session2_csrf

    url = f"{ctrl}/proxy/network/api/s/{site}/cmd/stamgr"
    headers = {"X-Csrf-Token": session2_csrf}
    payload = {"cmd": "authorize-guest", "mac": mac, "minutes": minutes}

    r = _post_retry(session2, url, payload, headers=headers)
    if not r:
        log_error("[MODELO2] AUTH sin respuesta del UDM")
        return False

    if r.status_code in (401, 403):
        log_error("[MODELO2] Sesión expirada → Re-login")
        session2.cookies.clear()
        session2_csrf = None

        if not modelo2_login(
            ctrl,
            config["Unifi"].get("username"),
            config["Unifi"].get("password"),
        ):
            return False

        headers["X-Csrf-Token"] = session2_csrf
        r = _post_retry(session2, url, payload, headers=headers)
        
        if not r:
            log_error("[MODELO2] AUTH reintento sin respuesta")
            return False

    log_info(f"[MODELO2] AUTH → {r.status_code} {r.text[:200]}")
    return r.status_code == 200


def unifi_udm_modelo2(mac, minutes, ctrl, site, user, pwd):
    if not session2_csrf:
        if not modelo2_login(ctrl, user, pwd):
            return False
    modelo2_unauthorize(ctrl, site, mac)
    return modelo2_authorize(ctrl, site, mac, minutes)



# ------------------------------------------------------
# MODELO 3 — LDocker
# ------------------------------------------------------
# ------------------------------------------------------
# MODELO 3 — UniFi Controller Docker (jacobalberty)
# ------------------------------------------------------

session3 = requests.Session()
session3.verify = False
session3_csrf = None

def modelo3_login(ctrl, user, pwd):
    global session3_csrf

    # Si ya hay sesión activa, no relogin
    if session3_csrf:
        return True

    login_url = f"{ctrl}/api/login"
    log_info(f"[MODELO3] LOGIN → {login_url}")

    r = session3.post(login_url, json={"username": user, "password": pwd}, timeout=4)

    if r.status_code != 200:
        log_error(f"[MODELO3] Login FAIL {r.status_code} {r.text[:200]}")
        return False

    session3_csrf = (
        r.headers.get("X-CSRF-Token")
        or r.headers.get("x-csrf-token")
        or r.headers.get("x-updated-csrf-token")
    )

    log_info(f"[MODELO3] CSRF → {session3_csrf}")
    return True


def modelo3_unauthorize(ctrl, site, mac):
    url = f"{ctrl}/api/s/{site}/cmd/stamgr"
    headers = {"X-CSRF-Token": session3_csrf}
    payload = {"cmd": "unauthorize-guest", "mac": mac}

    r = _post_retry(session3, url, payload, headers=headers)
    if not r:
        log_error("[MODELO3] UNAUTH sin respuesta")
        return False
    log_info(f"[MODELO3] UNAUTH → {r.status_code} {r.text[:200]}")
    return True


def modelo3_authorize(ctrl, site, mac, minutes):
    url = f"{ctrl}/api/s/{site}/cmd/stamgr"
    headers = {"X-CSRF-Token": session3_csrf}
    payload = {"cmd": "authorize-guest", "mac": mac, "minutes": minutes}

    r = session3.post(url, json=payload, headers=headers, timeout=4)
    log_info(f"[MODELO3] AUTH → {r.status_code} {r.text[:200]}")
    return r.status_code == 200


def unifi_modelo3(mac, minutes, ctrl, site, user, pwd):
    if not modelo3_login(ctrl, user, pwd):
        return False
    modelo3_unauthorize(ctrl, site, mac)
    return modelo3_authorize(ctrl, site, mac, minutes)




# ------------------------------------------------------
# MODELO 4 — LOGIN PERSISTENTE
# ------------------------------------------------------
session4 = requests.Session()
session4.verify = False
session4_csrf = None


def modelo4_login(ctrl, user, pwd):
    global session4_csrf

    if session4_csrf:
        return True

    login_url = f"{ctrl}/api/auth/login"
    r = session4.post(login_url, json={"username": user, "password": pwd}, timeout=4)

    if r.status_code != 200:
        log_error(f"[MODELO4] Login FAIL {r.status_code} {r.text[:200]}")
        return False

    session4_csrf = (
        r.headers.get("x-csrf-token") or r.headers.get("x-updated-csrf-token")
    )
    log_info(f"[MODELO4] CSRF → {session4_csrf}")
    return True


def modelo4_unauthorize(ctrl, site, mac):
    url = f"{ctrl}/proxy/network/api/s/{site}/cmd/stamgr"
    headers = {"X-Csrf-Token": session4_csrf}
    payload = {"cmd": "unauthorize-guest", "mac": mac}
    r = session4.post(url, json=payload, headers=headers, timeout=4)
    log_info(f"[MODELO4] UNAUTH → {r.status_code}")
    return True


def modelo4_authorize(ctrl, site, mac, minutes):
    url = f"{ctrl}/proxy/network/api/s/{site}/cmd/stamgr"
    headers = {"X-Csrf-Token": session4_csrf}
    payload = {"cmd": "authorize-guest", "mac": mac, "minutes": minutes}
    r = session4.post(url, json=payload, headers=headers, timeout=4)
    log_info(f"[MODELO4] AUTH → {r.status_code}")
    return r.status_code == 200


def unifi_udm_modelo4(mac, minutes, ctrl, site, user, pwd):
    if not modelo4_login(ctrl, user, pwd):
        return False
    modelo4_unauthorize(ctrl, site, mac)
    return modelo4_authorize(ctrl, site, mac, minutes)



# ------------------------------------------------------
# DISPATCH GENERAL – FUNCIÓN QUE LLAMA main.py
# ------------------------------------------------------
def unifi_guest_approve(client_mac: str, ap_mac: str | None, ssid: str | None):
    global FAIL_COUNT
    if FAIL_COUNT >= MAX_FAIL:
        log_error("Demasiados errores UniFi, reseteando sesiones")
        session2.cookies.clear()
        session3.cookies.clear()
        session4.cookies.clear()
        # reset CSRFs
        session2_csrf = None
        session3_csrf = None
        session4_csrf = None
        FAIL_COUNT = 0

    if not client_mac:
        log_error("client_mac vacío")
        return False

    ctrl = config["Unifi"].get("controller").rstrip("/")
    site = config["Unifi"].get("site", "default")
    user = config["Unifi"].get("username")
    pwd = config["Unifi"].get("password")
    minutes = int(config["Unifi"].get("session_minutes", "360"))

    log_info(f"UNIFI modelo={modelo} MAC={client_mac} AP={ap_mac} SSID={ssid}")

    try:
        if modelo == 2:
            return unifi_udm_modelo2(client_mac, minutes, ctrl, site, user, pwd)
        elif modelo == 3:
            return unifi_modelo3(client_mac, minutes, ctrl, site, user, pwd)
        elif modelo == 4:
            return unifi_udm_modelo4(client_mac, minutes, ctrl, site, user, pwd)
        else:
            log_error(f"MODELO desconocido: {modelo}")
            return False
    except Exception as e:
        log_error(f"ERROR en unifi_guest_approve: {e}")
        return False
