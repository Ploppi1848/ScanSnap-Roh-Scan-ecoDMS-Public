# Alpha Build 16 - Regression Startzustand

## Ziel

Vorbereitung eines frischen Build-16-Massentest-/Regressionstestlaufs auf identischer Dokumentbasis.

Keine Scan-Service-Dateien und keine Extraktionslogik wurden geaendert.

## Sicherung vor Reset

Backup-Ordner:

`_release_4_0/alpha_build16_pre_regression_massentest_backup_20260629_202900`

Gesicherter Stand:

- Massentest-Ergebnisse: 128
- Massentest-Sollwerte: 128
- Verarbeitete PDFs: 128
- Wartende PDFs: 0
- Fehler-PDFs: 0

Gesichert wurden:

- `_massentest/ergebnisse`
- `_massentest/verarbeitet`
- `_massentest/entpackt`
- `_massentest/fehler`
- `_massentest/logs`
- `_massentest/eingang_zip`

## Reset / Neuer Startbestand

Durchgefuehrt:

- 128 PDFs aus `_massentest/verarbeitet` zurueck nach `_massentest/entpackt` gelegt.
- Alte Massentest-Ergebnisdateien geloescht:
  - `massentest_ergebnisse.json`
  - `massentest_ergebnisse.csv`
  - `massentest_fortschritt.json`
- Viewer-Bestand geleert.
- Sollwerte erhalten:
  - `massentest_sollwerte.json`

Aktueller Startzustand:

- Wartende PDFs in `_massentest/entpackt`: 128
- Verarbeitete PDFs in `_massentest/verarbeitet`: 0
- Fehler-PDFs in `_massentest/fehler`: 0
- Massentest-Sollwerte: 128
- Massentest-Ergebnisse: noch nicht neu erzeugt

## Hinweis

Der eigentliche Build-16-Regressionstest wurde noch nicht gestartet.

Der Bestand ist vorbereitet, damit dieselben 128 Referenzdokumente frisch eingelesen und gegen die vorhandenen Sollwerte getestet werden koennen.
