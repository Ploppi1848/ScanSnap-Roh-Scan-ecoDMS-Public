# Changelog WebUI 4.0

## Sprint 5D - Generische Label/Wert-Blockerkennung fuer Nummernfelder

Status: getestet und abgeschlossen

Ziel:

- Generische Erkennung von Label/Wert-Bloecken fuer Nummernfelder
- Fokus auf `RECHNR` und `KUNDENNR`
- Bonprix als Testgruppe, ohne Bonprix-Hartcodierung

Buildvergleich:

- Verbessert: 2 Dokumente
- Verschlechtert: 1 Dokument
- Unveraendert: 117 Dokumente
- Neu auffaellig: 0
- Nicht mehr auffaellig: 8
- `RECHNR` verbessert: 9
- `KUNDENNR` verbessert: 9

Einzige Verschlechterung:

- Lowenstein Medical - Neuer Dateiname

Einordnung:

- Sprint 5D brachte deutliche Feldverbesserungen bei Rechnungsnummer und Kundennummer.
- Es gab keine neu auffaelligen Dokumente.
- Die einzige Regression betrifft den neuen Dateinamen bei Lowenstein Medical und sollte separat bewertet werden.
