# Open-Source-Preparation Report

## Ziel

Das private Arbeitsrepository wurde auf sensible Inhalte geprueft und fuer eine moegliche spaetere Public-Struktur vorbereitet.

Es wurden keine Programmdateien, keine WebUI-Funktionen, keine OCR-/Erkennungslogik und keine Referenzdaten veraendert.

## Ergebnis der Sicherheitsanalyse

Das bestehende private Repository darf nicht direkt oeffentlich geschaltet werden.

Gefundene sensible Bereiche:

- `_config/`
  - enthaelt private Konfigurationswerte.
  - in `benachrichtigung_konfiguration.txt` wurden SMTP-/E-Mail-Zugangsdaten und echte E-Mail-Adressen gefunden.
  - Lernlisten und Lieferantenkonfigurationen enthalten echte Lieferanten, Dokumentnamen und Arbeitshistorie.
- `_web_test/`
  - enthaelt echte PDF-Testdokumente.
  - `.pdf.testmeta`, `_expected/`, `_status/` und `_reports/` enthalten echte Dokumentnamen, Sollwerte, Nummern und Statusdaten.
- `_massentest/ergebnisse/`
  - enthaelt `massentest_ergebnisse.json`, `massentest_sollwerte.json`, Fortschritt, CSVs und Snapshots.
  - Daten enthalten echte Dokumentnamen, erkannte Felder, Sollwerte, Abweichungen und Statusinformationen.
- `_projektcenter/aufgaben.json`
  - enthaelt Aufgaben mit OCR-/Debug-Auszug, Namen, Anschriften, Telefonnummern, IBAN/BIC, Kundennummern und Versicherungsnummern.
- `_release_4_0/`
  - enthaelt Analyseberichte und CSV-/Vergleichsdaten mit echten Dokumentnamen, Lieferanten, Feldwerten und Fehlerbildern.
  - Backups unter `_release_4_0/*backup*` enthalten Massentest-Ergebnisse und Sollwerte.
- `_logo/`
  - enthaelt PNG-Dateien, darunter eine Datei mit ChatGPT-Erzeugungsnamen.
  - Fuer Public sollte geklaert werden, ob Logo-Dateien freigegeben sind. Bis dahin wird `_logo/` ignoriert.

Typische Trefferklassen:

- persoenliche Namen
- E-Mail-Adressen
- Telefonnummern
- Anschriften
- IBAN/BIC
- Kundennummern
- Versicherungsnummern
- Rechnungs-/Auftragsnummern
- echte Dokumentnamen
- OCR-/Debugtexte
- SMTP-Zugangsdaten

## Erstellte Public-Beispielstruktur

Angelegt wurde `_config_example/` mit anonymisierten Beispielkonfigurationen:

- `benachrichtigung_konfiguration.example.txt`
- `box_konfiguration.example.txt`
- `dateiname_konfiguration.example.txt`
- `dokumentfilter_konfiguration.example.txt`
- `dokumenttypen_konfiguration.example.txt`
- `etiketten_konfiguration.example.txt`
- `felder_konfiguration.example.txt`
- `import_optionen_konfiguration.example.txt`
- `lieferanten_konfiguration.example.txt`
- `meta_konfiguration.example.txt`
- `outlook_konfiguration.example.txt`
- `zaehler.example.txt`
- `README.md`

Zusatz-READMEs:

- `_web_test/README.md`
- `_massentest/README.md`

## Gitignore-Anpassung

Die `.gitignore` wurde fuer Public-Sicherheit ergaenzt:

- private Konfiguration: `_config/`
- lokale Testdaten: `_web_test/*`
- Massentest-Ergebnisse: `_massentest/ergebnisse/`
- Projektcenter-Daten: `_projektcenter/`
- Debug/Logs: `_debug_text/`, `_logs/`
- lokale Dokumente und Medien: `*.pdf`, `*.jpg`, `*.jpeg`, `*.png`
- Metadaten/Logs/CSV: `*.meta`, `*.log`, `*.csv`, `*.testmeta`
- `_config_example/`, `_web_test/README.md` und `_massentest/README.md` bleiben als Public-Hinweise vorgesehen.

## Nicht durchgefuehrt

- keine Git-Historie bereinigt
- kein `filter-branch`
- kein `filter-repo`
- kein BFG
- kein Force Push
- keine Loeschung echter Daten aus dem Arbeitsrepo
- keine Codeaenderungen
- keine WebUI-Aenderungen
- keine Scan-Service-/OCR-/Erkennungslogik geaendert

## Empfehlung

Das private Arbeitsrepo bleibt privat.

Fuer eine oeffentliche Version sollte ein neues, leeres Public-Repository erstellt werden. Dorthin wird nur ein bereinigter Stand ohne private Historie, ohne echte Dokumente, ohne Massentestdaten und ohne Zugangsdaten kopiert.

Vor einer Veroeffentlichung zusaetzlich pruefen:

- keine echten Daten in Markdown-Berichten
- keine echten Daten in Beispieldateien
- keine echten Logos oder nicht freigegebenen Bilddateien
- keine sensible Git-Historie im Public-Repo
