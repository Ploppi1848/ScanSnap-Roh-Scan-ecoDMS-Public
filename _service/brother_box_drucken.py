import sys
from pathlib import Path

import win32com.client


# ============================================================
# brother_box_drucken.py
# ============================================================
#
# Zweck:
# - Druckt ein Brother/P-touch Etikett über b-PAC.
# - Erwartet einen BOX-Code als Parameter.
#
# Beispiel:
# "C:\Users\H.-G. Hepp\AppData\Local\Programs\Python\Python314-32\python.exe" brother_box_drucken.py "Ordner003-06-2026-0001"
#
# Wichtig:
# - Dieses Script muss mit 32-Bit Python laufen.
# - b-PAC SDK muss installiert sein.
# - Die LBX-Vorlage muss passende Objektnamen enthalten:
#
#   QR_BOX
#   TXT_BOX
#   TXT_MONAT_JAHR
#   TXT_NUMMER
#   TXT_CODE
#
# ============================================================


BASIS_ORDNER = Path("C:/ScanSnap_Roh-Scan-ecoDMS")
CONFIG_ORDNER = BASIS_ORDNER / "_config"
ETIKETTEN_DATEI = CONFIG_ORDNER / "etiketten_konfiguration.txt"

DEFAULTS = {
    "ETIKETTENDRUCK": "1",
    "DRUCKER": "Brother QL-1110NWB",
    "VORLAGE": r"C:\ScanSnap_Roh-Scan-ecoDMS\_etiketten\BOX_ETIKETT.lbx",
    "PYTHON32": r"C:\Users\H.-G. Hepp\AppData\Local\Programs\Python\Python314-32\python.exe",
}


def lade_config() -> dict:
    CONFIG_ORDNER.mkdir(parents=True, exist_ok=True)

    if not ETIKETTEN_DATEI.exists():
        text = "\n".join(f"{k}={v}" for k, v in DEFAULTS.items()) + "\n"
        ETIKETTEN_DATEI.write_text(text, encoding="utf-8")

    werte = DEFAULTS.copy()

    with open(ETIKETTEN_DATEI, "r", encoding="utf-8") as f:
        for zeile in f:
            zeile = zeile.strip()

            if not zeile or zeile.startswith("#"):
                continue

            if "=" not in zeile:
                continue

            key, value = zeile.split("=", 1)
            werte[key.strip().upper()] = value.strip()

    return werte


def set_object_text(doc, name: str, value: str):
    obj = doc.GetObject(name)

    if obj is None:
        print(f"HINWEIS: Objekt nicht gefunden: {name}")
        return False

    obj.Text = value
    print(f"OK: {name} = {value}")
    return True


def zerlege_box_code(box_code: str):
    teile = box_code.split("-")

    if len(teile) >= 4:
        box = teile[0]
        monat = teile[1]
        jahr = teile[2]
        nummer = teile[3]
        monat_jahr = f"{monat}-{jahr}"
    else:
        box = box_code
        monat_jahr = ""
        nummer = ""

    return box, monat_jahr, nummer


def drucke_etikett(box_code: str):
    config = lade_config()

    if config.get("ETIKETTENDRUCK", "1") != "1":
        print("Etikettendruck ist deaktiviert: ETIKETTENDRUCK=0")
        return 0

    vorlage = Path(config.get("VORLAGE", DEFAULTS["VORLAGE"]))
    drucker = config.get("DRUCKER", DEFAULTS["DRUCKER"])

    if not vorlage.exists():
        print(f"FEHLER: Vorlage nicht gefunden: {vorlage}")
        return 2

    box, monat_jahr, nummer = zerlege_box_code(box_code)

    print("Brother b-PAC Etikettendruck")
    print(f"Vorlage: {vorlage}")
    print(f"Drucker: {drucker}")
    print(f"BOX-Code: {box_code}")

    doc = win32com.client.Dispatch("bpac.Document")

    if not doc.Open(str(vorlage)):
        print("FEHLER: Vorlage konnte nicht geöffnet werden.")
        return 3

    # Werte in Vorlage einsetzen
    set_object_text(doc, "QR_BOX", box_code)
    set_object_text(doc, "TXT_BOX", box)
    set_object_text(doc, "TXT_MONAT_JAHR", monat_jahr)
    set_object_text(doc, "TXT_NUMMER", nummer)
    set_object_text(doc, "TXT_CODE", box_code)

    try:
        doc.SetPrinter(drucker, True)
        print("OK: Drucker gesetzt.")
    except Exception as e:
        print(f"HINWEIS: Drucker konnte nicht explizit gesetzt werden: {e}")

    try:
        doc.StartPrint("BOX_ETIKETT", 0)
    except Exception as e:
        print(f"HINWEIS: StartPrint nicht verfügbar oder nicht nötig: {e}")

    doc.PrintOut(1, 0)

    print("FERTIG: Etikett wurde an b-PAC übergeben.")
    return 0


def main():
    if len(sys.argv) < 2:
        print("FEHLER: BOX-Code fehlt.")
        print()
        print("Beispiel:")
        print(r'"C:\Users\H.-G. Hepp\AppData\Local\Programs\Python\Python314-32\python.exe" brother_box_drucken.py "Ordner003-06-2026-0001"')
        sys.exit(1)

    box_code = sys.argv[1].strip()

    if not box_code:
        print("FEHLER: BOX-Code ist leer.")
        sys.exit(1)

    rc = drucke_etikett(box_code)
    sys.exit(rc)


if __name__ == "__main__":
    main()
