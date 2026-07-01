# WebUI 4.0.0-alpha Build 16 Vorbereitung

## Ausgangslage

Alpha Build 15 ist abgeschlossen und dient als stabiler Teststand.

Build 16 wird als stabilisierter Alpha-Korrekturbuild vorbereitet. Build 16C bleibt separat fuer die Extraktionsqualitaet und wird nicht mit diesem WebUI-/Workflow-Korrekturbuild vermischt.

## Ziel Build 16

Build 16 ist kein Feature-Build und kein Extraktionsqualitaets-Build.

Zulaessig sind:

- Bugfixes
- kleine UX-Verbesserungen
- Layoutkorrekturen
- Workflow-Stabilisierung

Nicht Bestandteil von Build 16:

- neue Funktionen
- neue Statusmodelle
- neue Erkennungsregeln
- Aenderungen an der Extraktionslogik
- Build-16C-Themen

## Umgesetzte Bugfixes

- Versionsanzeige auf `WebUI 4.0.0-alpha Build 16` gesetzt.
- Sichtbare Versionsanzeige laeuft weiter ueber `APP_VERSION`.
- Fachliche Entscheidungswege bleiben auf der gemeinsamen Weiterleitungsroutine `massentest_redirect_next_fachlich()`.
- Nacharbeitsdokumente bleiben durch die bestehende Queue-Filterung von der normalen fachlichen Pruefung ausgeschlossen.
- Nach Speichern/Entscheidung wird weiterhin direkt das naechste offene fachliche Pruefdokument gesucht.
- Sollwertspeicherung im fachlichen Workflow bewertet den Datensatz danach erneut.
- `soll_neuer_dateiname` bleibt im zentralen Soll/Ist-Vergleich enthalten.
- Einzeldokument-Speicherformulare deaktivieren die alte Massenfortschrittsanzeige, damit nicht mehr sinngemaess "128 von 128 gespeichert" im Einzeldokument-Kontext erscheint.

## Umgesetzte UX-Punkte

- Pruefentscheidungen in der fachlichen Schnellpruefung klarer gruppiert:
  - Freigabe
  - Nacharbeit / Sonderfall
  - Sollwerte
- Fachliche Entscheidungsbuttons bleiben farblich markiert, sind aber zusaetzlich durch Gruppentitel unterscheidbar.
- Button `Zur Schnellpruefung` in der Sollwertbearbeitung klarer beschriftet als `Zur fachlichen Schnellpruefung`.
- Speichermeldung im fachlichen Sollwertworkflow auf Einzeldokument-Kontext umgestellt:
  - `Sollwerte fuer dieses Dokument gespeichert.`
- Overlay bei Einzeldokument-Speicherung zeigt keine alte Massenlauf-Progressmeldung mehr.

## Bewusst nicht umgesetzte Punkte

- PDF-Vorschau per gedrueckter Maustaste verschieben:
  - nicht umgesetzt, weil die aktuelle PDF-Vorschau ueber den eingebetteten Browser-PDF-Viewer im `iframe` laeuft.
  - Ein eigener Pan-Modus waere eine neue PDF-Komponente und damit fuer Build 16 nicht risikoarm.
- Keine Aenderungen an Erkennungslogik, Nummernextraktion, Lieferantenerkennung oder Dokumenttyp-Erkennung.
- Keine Aenderungen an `_service/ecodms_scan_service.py`.

## Hinweis Build 16C

Build 16C bleibt separat fuer Extraktionsqualitaet.

Themen wie AKTENZEICHEN als Service-Metafeld, Label-Wert-Bloecke, Dokumenttyp-Prioritaeten, Nummern-Clearing und Wrapper-Auswertung werden nicht in Build 16 umgesetzt, sondern gesondert geplant und getestet.

## Pruefung

Durchzufuehren:

- Syntaxpruefung `ecodms_webui.py`
- Plausibilitaetspruefung der fachlichen Weiterleitung
- Kontrolle, dass keine Scan-Service-Dateien geaendert wurden
- Kontrolle, dass keine Extraktionslogik geaendert wurde
