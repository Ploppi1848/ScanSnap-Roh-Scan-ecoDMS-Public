# ScanSnap Roh-Scan → ecoDMS

Ein Python-Projekt zur automatisierten Verarbeitung gescannter Dokumente für ecoDMS.

## Funktionen

- Überwachung eines Scan-Eingangsordners
- OCR-Auswertung gescannter PDFs
- automatische Lieferantenerkennung
- Dokumenttyp-Erkennung
- Extraktion wichtiger Metadaten
  - Rechnungsdatum
  - Rechnungsnummer
  - Kundennummer
  - Auftragsnummer
  - Bestellnummer
  - Betrag
- QR-Code-gestützte Dokumenttrennung
- Barcode-/Ordnerverwaltung
- WebUI für Tests, Konfiguration und Qualitätsanalyse
- Regressionstests und Snapshot-Vergleiche

---

## Projektstatus

Aktuelle Entwicklung erfolgt auf Basis kleiner, nachvollziehbarer Sprints.

Schwerpunkte:

- Qualitätsanalyse
- Snapshot-Vergleich
- Lieferantenerkennung
- Scoring
- Diagnoselogging
- WebUI 4.0

---

## Voraussetzungen

- Windows
- Python 3.14
- Tesseract OCR
- ScanSnap Scanner
- ecoDMS

---

## Projektstruktur


_service
Scan-Service

_webservice
WebUI

_config_example
Beispielkonfigurationen

_release_4_0
Sprint-Dokumentation

_massentest
Regressionstests


---

## Sicherheit

Dieses Repository enthält

- keine echten Zugangsdaten
- keine produktiven Konfigurationen
- keine echten Testdokumente

Eigene Konfigurationen müssen lokal erstellt werden.

---

## Entwicklungsrichtlinien

Bitte vor Änderungen zuerst


DEVELOPMENT_GUIDELINES.md


lesen.

---

## Lizenz

Zurzeit keine Open-Source-Lizenz festgelegt.
