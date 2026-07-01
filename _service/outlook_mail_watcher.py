import time
import logging
import re
from pathlib import Path
from datetime import datetime

import pythoncom
import win32com.client


VERSION = "1.3.0"

BASIS_ORDNER = Path("C:/ScanSnap_Roh-Scan-ecoDMS")
CONFIG_ORDNER = BASIS_ORDNER / "_config"
LOG_ORDNER = BASIS_ORDNER / "_logs"

MAIL_STATUS_ORDNER = BASIS_ORDNER / "_mail"
MAIL_INPUT_ORDNER = BASIS_ORDNER / "mail_input"

OUTLOOK_CONFIG_DATEI = CONFIG_ORDNER / "outlook_konfiguration.txt"
LIEFERANTEN_MAIL_DATEI = CONFIG_ORDNER / "lieferanten_mail_konfiguration.txt"
VERARBEITET_DATEI = MAIL_STATUS_ORDNER / "_mail_verarbeitet.txt"
LOG_DATEI = LOG_ORDNER / "outlook_mail_watcher.log"

for ordner in [BASIS_ORDNER, CONFIG_ORDNER, LOG_ORDNER, MAIL_INPUT_ORDNER]:
    ordner.mkdir(parents=True, exist_ok=True)


logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

if not logger.handlers:
    file_handler = logging.FileHandler(LOG_DATEI, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def lade_key_value_config(pfad: Path, defaults: dict, beispiel_text: str) -> dict:
    if not pfad.exists():
        pfad.write_text(beispiel_text, encoding="utf-8")
        logging.warning(f"Konfiguration wurde neu erstellt: {pfad}")

    werte = defaults.copy()

    try:
        with open(pfad, "r", encoding="utf-8") as f:
            for zeile in f:
                zeile = zeile.strip()
                if not zeile or zeile.startswith("#"):
                    continue
                if "=" not in zeile:
                    continue
                key, value = zeile.split("=", 1)
                werte[key.strip().upper()] = value.strip()
    except Exception as e:
        logging.error(f"Fehler beim Lesen von {pfad}: {e}")

    return werte



def migriere_alte_verarbeitet_datei():
    alte_datei = BASIS_ORDNER / "_mail_verarbeitet.txt"

    try:
        if alte_datei.exists() and not VERARBEITET_DATEI.exists():
            MAIL_STATUS_ORDNER.mkdir(parents=True, exist_ok=True)
            alte_datei.replace(VERARBEITET_DATEI)
            logging.info(f"Alte Mail-Verarbeitet-Datei migriert nach: {VERARBEITET_DATEI}")
    except Exception as e:
        logging.warning(f"Konnte alte Mail-Verarbeitet-Datei nicht migrieren: {e}")



def lade_config() -> dict:
    defaults = {
        "OUTLOOK_AKTIV": "1",
        "INTERVALL_SEKUNDEN": "30",
        "NUR_PDF": "1",
        "NUR_UNGELESENE": "0",
        "NACH_EXPORT_KATEGORIE_SETZEN": "1",
        "KATEGORIE": "ecoDMS archiviert",
        "NACH_EXPORT_ALS_GELESEN_MARKIEREN": "0",
        "MAX_MAILS_PRO_LAUF": "25",
        "DATEINAME_MIT_ABSENDER": "1",
        "DATEINAME_MIT_DATUM": "1",
        "META_DATEI_ERZEUGEN": "1",
        "ALLE_POSTEINGAENGE_PRUEFEN": "1",
        "MAIL_DEBUG_LOG": "1",
    }

    beispiel = (
        "# Outlook Mail Watcher Konfiguration\n"
        "OUTLOOK_AKTIV=1\n"
        "INTERVALL_SEKUNDEN=30\n"
        "NUR_PDF=1\n"
        "NUR_UNGELESENE=0\n"
        "NACH_EXPORT_KATEGORIE_SETZEN=1\n"
        "KATEGORIE=ecoDMS archiviert\n"
        "NACH_EXPORT_ALS_GELESEN_MARKIEREN=0\n"
        "MAX_MAILS_PRO_LAUF=25\n"
        "DATEINAME_MIT_ABSENDER=1\n"
        "DATEINAME_MIT_DATUM=1\n"
        "META_DATEI_ERZEUGEN=1\n"
    )

    return lade_key_value_config(OUTLOOK_CONFIG_DATEI, defaults, beispiel)


def lade_lieferanten_mail_config() -> list[dict]:
    beispiel = (
        "# Lieferantenerkennung anhand Mail-Absender\n"
        "# Format:\n"
        "# Lieferant|DomainOderMail1;DomainOderMail2\n"
        "#\n"
        "Amazon|amazon.de;amazon.com\n"
        "Telekom|telekom.de;t-online.de\n"
        "Stadtwerke Bochum|stadtwerke-bochum.de\n"
    )

    if not LIEFERANTEN_MAIL_DATEI.exists():
        LIEFERANTEN_MAIL_DATEI.write_text(beispiel, encoding="utf-8")
        logging.warning(f"Lieferanten-Mail-Konfiguration wurde neu erstellt: {LIEFERANTEN_MAIL_DATEI}")

    eintraege = []

    try:
        with open(LIEFERANTEN_MAIL_DATEI, "r", encoding="utf-8") as f:
            for zeile in f:
                zeile = zeile.strip()
                if not zeile or zeile.startswith("#"):
                    continue
                if "|" not in zeile:
                    continue
                name, suchwerte = zeile.split("|", 1)
                werte = [w.strip().lower() for w in suchwerte.split(";") if w.strip()]
                if name.strip() and werte:
                    eintraege.append({"name": name.strip(), "werte": werte})
    except Exception as e:
        logging.error(f"Fehler beim Lesen der Lieferanten-Mail-Konfiguration: {e}")

    return eintraege


def erkenne_lieferant_aus_mail(absender_email: str, absender_name: str) -> str:
    text = f"{absender_email} {absender_name}".lower()
    for eintrag in lade_lieferanten_mail_config():
        for wert in eintrag["werte"]:
            if wert in text:
                logging.info(f"Lieferant aus Mail erkannt: {eintrag['name']} über {wert}")
                return eintrag["name"]
    return ""


def lade_verarbeitete_ids() -> set[str]:
    if not VERARBEITET_DATEI.exists():
        return set()
    try:
        return set(
            zeile.strip()
            for zeile in VERARBEITET_DATEI.read_text(encoding="utf-8").splitlines()
            if zeile.strip()
        )
    except Exception as e:
        logging.error(f"Fehler beim Lesen der verarbeiteten Mail-IDs: {e}")
        return set()


def speichere_verarbeitete_id(entry_id: str):
    try:
        with open(VERARBEITET_DATEI, "a", encoding="utf-8") as f:
            f.write(entry_id + "\n")
    except Exception as e:
        logging.error(f"Fehler beim Schreiben der verarbeiteten Mail-ID: {e}")


def bereinige_dateiname(name: str) -> str:
    name = re.sub(r'[<>:"/\\\\|?*]', "_", name)
    name = re.sub(r"\\s+", "_", name)
    return name[:180]


def hole_absender_email(mail) -> str:
    try:
        if getattr(mail, "SenderEmailAddress", ""):
            return mail.SenderEmailAddress
    except Exception:
        pass
    return ""


def schreibe_meta_datei(pdf_pfad: Path, mail, anhang_name: str):
    try:
        absender_name = getattr(mail, "SenderName", "") or ""
        absender_email = hole_absender_email(mail)
        betreff = getattr(mail, "Subject", "") or ""
        empfangen = mail.ReceivedTime.strftime("%Y-%m-%d %H:%M:%S")
        maildatum = mail.ReceivedTime.strftime("%d.%m.%Y")
        lieferant = erkenne_lieferant_aus_mail(absender_email, absender_name)

        meta_pfad = pdf_pfad.with_suffix(pdf_pfad.suffix + ".meta")

        meta_pfad.write_text(
            f"QUELLE=OUTLOOK\n"
            f"LIEFERANT={lieferant}\n"
            f"MAIL_ABSENDER_NAME={absender_name}\n"
            f"MAIL_ABSENDER_EMAIL={absender_email}\n"
            f"MAIL_BETREFF={betreff}\n"
            f"MAIL_EMPFANGEN={empfangen}\n"
            f"MAIL_DATUM={maildatum}\n"
            f"MAIL_ANHANG={anhang_name}\n",
            encoding="utf-8"
        )

        logging.info(f"Meta-Datei erzeugt: {meta_pfad}")

    except Exception as e:
        logging.error(f"Fehler beim Schreiben der Meta-Datei: {e}")


def sichere_pdf_anhaenge(mail, config: dict) -> int:
    gespeichert = 0

    absender = getattr(mail, "SenderName", "Unbekannt") or "Unbekannt"

    try:
        empfangen = mail.ReceivedTime.strftime("%Y%m%d_%H%M%S")
    except Exception:
        empfangen = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i in range(1, mail.Attachments.Count + 1):
        try:
            anhang = mail.Attachments.Item(i)
            original_name = anhang.FileName

            if config.get("NUR_PDF", "1") == "1" and not original_name.lower().endswith(".pdf"):
                logging.info(f"Anhang übersprungen, kein PDF: {original_name}")
                continue

            teile = []
            if config.get("DATEINAME_MIT_DATUM", "1") == "1":
                teile.append(empfangen)
            if config.get("DATEINAME_MIT_ABSENDER", "1") == "1":
                teile.append(absender)
            teile.append(original_name)

            ziel_name = bereinige_dateiname("_".join(teile))
            ziel_pfad = MAIL_INPUT_ORDNER / ziel_name

            zaehler = 1
            while ziel_pfad.exists():
                ziel_pfad = MAIL_INPUT_ORDNER / f"{ziel_pfad.stem}_{zaehler}{ziel_pfad.suffix}"
                zaehler += 1

            anhang.SaveAsFile(str(ziel_pfad))
            logging.info(f"PDF-Anhang gespeichert: {ziel_pfad}")

            if config.get("META_DATEI_ERZEUGEN", "1") == "1":
                schreibe_meta_datei(ziel_pfad, mail, original_name)

            gespeichert += 1

        except Exception as e:
            logging.error(f"Fehler beim Speichern eines Anhangs: {e}")

    return gespeichert


def markiere_mail(mail, config: dict):
    try:
        if config.get("NACH_EXPORT_KATEGORIE_SETZEN", "1") == "1":
            kategorie = config.get("KATEGORIE", "ecoDMS archiviert")
            bisher = getattr(mail, "Categories", "") or ""
            if kategorie not in bisher:
                mail.Categories = (bisher + ", " + kategorie) if bisher.strip() else kategorie

        if config.get("NACH_EXPORT_ALS_GELESEN_MARKIEREN", "0") == "1":
            mail.UnRead = False

        mail.Save()
    except Exception as e:
        logging.error(f"Fehler beim Markieren der Mail: {e}")



def hole_posteingaenge(outlook):
    """
    Gibt je nach Konfiguration einen oder mehrere Posteingänge zurück.
    Standard: alle Posteingänge aller Outlook-Konten.
    """
    config = lade_config()

    if config.get("ALLE_POSTEINGAENGE_PRUEFEN", "1") != "1":
        return [outlook.GetDefaultFolder(6)]

    posteingaenge = []

    try:
        for i in range(1, outlook.Folders.Count + 1):
            root = outlook.Folders.Item(i)

            try:
                inbox = root.Folders["Posteingang"]
                posteingaenge.append(inbox)
                logging.info(f"Posteingang gefunden: {root.Name} / Posteingang")
            except Exception:
                try:
                    store = root.Store
                    inbox = store.GetDefaultFolder(6)
                    posteingaenge.append(inbox)
                    logging.info(f"Posteingang gefunden über Store: {root.Name}")
                except Exception:
                    logging.info(f"Kein Posteingang gefunden für: {root.Name}")

    except Exception as e:
        logging.error(f"Fehler beim Ermitteln aller Posteingänge: {e}")

    if not posteingaenge:
        posteingaenge = [outlook.GetDefaultFolder(6)]
        logging.warning("Kein zusätzlicher Posteingang gefunden. Verwende Standard-Posteingang.")

    return posteingaenge


def beschreibe_mail(mail) -> str:
    try:
        betreff = getattr(mail, "Subject", "") or ""
    except Exception:
        betreff = ""

    try:
        empfangen = str(mail.ReceivedTime)
    except Exception:
        empfangen = ""

    try:
        anzahl = mail.Attachments.Count
    except Exception:
        anzahl = "?"

    try:
        ungelesen = mail.UnRead
    except Exception:
        ungelesen = "?"

    return f"Betreff='{betreff}' / Empfangen='{empfangen}' / Anhänge={anzahl} / Ungelesen={ungelesen}"



def pruefe_neue_mails():
    config = lade_config()

    if config.get("OUTLOOK_AKTIV", "1") != "1":
        logging.info("Outlook Watcher deaktiviert: OUTLOOK_AKTIV=0")
        return

    verarbeitet = lade_verarbeitete_ids()

    try:
        max_mails = int(config.get("MAX_MAILS_PRO_LAUF", "25"))
    except ValueError:
        max_mails = 25

    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    posteingaenge = hole_posteingaenge(outlook)

    gesamt_bearbeitet = 0
    debug_log = config.get("MAIL_DEBUG_LOG", "1") == "1"

    for inbox in posteingaenge:
        if gesamt_bearbeitet >= max_mails:
            break

        try:
            logging.info(f"Prüfe Ordner: {inbox.FolderPath}")
            items = inbox.Items
            items.Sort("[ReceivedTime]", True)

            for mail in items:
                if gesamt_bearbeitet >= max_mails:
                    break

                try:
                    if getattr(mail, "Class", None) != 43:
                        continue

                    if debug_log:
                        logging.info(f"Mail geprüft: {beschreibe_mail(mail)}")

                    entry_id = mail.EntryID

                    if entry_id in verarbeitet:
                        if debug_log:
                            logging.info("Mail übersprungen: bereits verarbeitet.")
                        continue

                    if config.get("NUR_UNGELESENE", "0") == "1" and not mail.UnRead:
                        if debug_log:
                            logging.info("Mail übersprungen: nicht ungelesen.")
                        continue

                    if mail.Attachments.Count <= 0:
                        if debug_log:
                            logging.info("Mail ohne Anhänge. Markiere als verarbeitet.")
                        speichere_verarbeitete_id(entry_id)
                        continue

                    if debug_log:
                        for i in range(1, mail.Attachments.Count + 1):
                            try:
                                anhang = mail.Attachments.Item(i)
                                logging.info(f"Anhang gefunden: {anhang.FileName}")
                            except Exception as e:
                                logging.error(f"Anhang konnte nicht gelesen werden: {e}")

                    anzahl = sichere_pdf_anhaenge(mail, config)

                    if anzahl > 0:
                        markiere_mail(mail, config)
                        logging.info(f"Mail verarbeitet: {mail.Subject} / PDF-Anhänge: {anzahl}")
                    else:
                        logging.info(f"Mail hatte Anhänge, aber keine speicherbaren PDF-Anhänge: {mail.Subject}")

                    speichere_verarbeitete_id(entry_id)
                    gesamt_bearbeitet += 1

                except Exception as e:
                    logging.error(f"Fehler bei Mailprüfung: {e}")

        except Exception as e:
            logging.error(f"Fehler beim Prüfen des Ordners: {e}")

    if gesamt_bearbeitet:
        logging.info(f"Outlook-Prüfung fertig. Mails verarbeitet: {gesamt_bearbeitet}")
    else:
        logging.info("Outlook-Prüfung fertig. Keine neuen Mails verarbeitet.")



def hauptschleife():
    logging.info(f"Outlook Mail Watcher Version {VERSION} gestartet.")
    logging.info(f"Mail-Input: {MAIL_INPUT_ORDNER}")

    while True:
        try:
            pythoncom.CoInitialize()
            pruefe_neue_mails()
            pythoncom.CoUninitialize()

            config = lade_config()
            intervall = int(config.get("INTERVALL_SEKUNDEN", "30") or "30")
            time.sleep(intervall)

        except KeyboardInterrupt:
            logging.info("Outlook Mail Watcher manuell beendet.")
            break
        except Exception as e:
            logging.error(f"Fehler in Outlook-Hauptschleife: {e}")
            time.sleep(30)


if __name__ == "__main__":
    hauptschleife()
