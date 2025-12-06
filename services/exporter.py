from database import safe_export_and_cleanup


def main():
    path = safe_export_and_cleanup()
    if path:
        print(f"🟢 Exportación correcta → {path}")
    else:
        print("⚠️ No se exportó nada (sin registros o error).")


if __name__ == "__main__":
    main()
