# WebUI 4.0 Final - Architekturplan

Stand: WebUI 4.0.0-alpha Build 16

Quelle der Analyse: `_webservice/ecodms_webui/ecodms_webui.py`

Wichtig: Dies ist nur ein Architektur- und Zielbildbericht. Es wurden keine Programmdateien, keine Scan-Service-Dateien, keine Extraktionslogik und keine Massentest-Daten geaendert.

## 1. Ist-Zustand

Die WebUI ist funktional stark gewachsen und umfasst inzwischen:

- Dashboard
- Projektcenter
- Testcenter / Einzeltest / Regression
- Qualitaetscenter / Massentest
- fachliche Schnellpruefung
- Sollwertbearbeitung
- Abweichungsansichten
- Konfiguration
- Lernlisten
- Logs
- Vorbereitung Produktivbetrieb / Regressionen

Technische Eckdaten:

- Datei: `_webservice/ecodms_webui/ecodms_webui.py`
- Groesse: ca. 433 KB
- Umfang: ca. 6.900 Zeilen
- Top-Level-Funktionen: ca. 260
- FastAPI-Routen: 81
- GET-Routen: 28
- POST-Routen: 53
- Routen unter `/test`: 43
- Routen unter `/test/massentest`: 30

Die WebUI ist aktuell eine grosse monolithische Datei. HTML, CSS, JavaScript, Datenzugriff, Statuslogik, Aufgabenlogik und Workflowsteuerung liegen eng beieinander. Das war fuer schnelle Alpha-Iterationen praktisch, erschwert aber WebUI 4.0 Final.

## 2. Routen- und Seitenuebersicht

### Dashboard

- `/`
- Funktion: `status()` bei ca. Zeile 665
- Aufgabe: Systemstatus, Scan-Service, Outlook-Watcher, Lernlisten, Projektcenter, Regressionstest, Massentest, Ordnerstatus.
- Layout: globale `layout()`-Shell, viele direkte `metric`-Kacheln.

### Projektcenter

- `/projekt`
- `/projekt/neu`
- `/projekt/status`
- `/projekt/delete`
- `/projekt/cleanup-orphans`
- `/projekt/aus-regression`
- `/projekt/regression-passed`
- zentrale Aufgabenquelle: `projekt_lade_aufgaben()` bei ca. Zeile 6510
- Darstellung: `projekt_task_html()` bei ca. Zeile 6725
- Aufgabe: allgemeine Aufgabenverwaltung, Regressionstest-Aufgaben, Massentest-Aufgaben, Ruecksprung zur fachlichen Pruefung.

### Testcenter / Regression

- `/test`
- `/test/einzeltest`
- `/test/upload`
- `/test/delete`
- `/test/open-pdf`
- `/test/expected`
- `/test/expected/from-actual`
- `/test/expected/generate-missing`
- `/test/run`
- `/test/run-all`
- `/test/mark-passed`
- `/regression`
- Aufgabe: Einzeltest, Regression, Sollwerte, Delta-Berichte, Produktivfreigabe-Vorstufe.

### Qualitaetscenter / Massentest

- `/test/massentest`
- alter Alias: `/massentest`
- Upload/Run/Reset/Rebuild/Clear-Routen
- `/test/massentest/result/{row_id}`
- `/test/massentest/fachlich/{row_id}`
- `/test/massentest/detail/{row_id}`
- `/test/massentest/quality`
- `/test/massentest/pdf/{row_id}`
- `/test/massentest/pdf-view/{row_id}`
- `/test/massentest/validate/{row_id}`
- `/test/massentest/fachlich-nicht-korrekt/{row_id}`
- `/test/massentest/sonderfall/{row_id}`
- Aufgabe: Altarchiv-Massentest, technische Pruefung, fachliche Validierung, Nacharbeit, Sonderfaelle, Sollwerte.

### Konfiguration

- `/config`
- `/config-form/box`
- `/config-form/import_optionen`
- `/config-form/dateiname`
- `/config-form/benachrichtigung`
- `/ablage`
- Aufgabe: Textkonfiguration plus formularbasierte Hauptoptionen.

### Lernlisten

- `/learning`
- `/learning/{kind}/add`
- `/learning/{kind}/{index}/accept`
- `/learning/{kind}/{index}/ignore`
- `/learning/{kind}/{index}/delete`
- Aufgabe: Lieferanten- und Dokumenttypen-Lernlisten.

### Logs

- `/logs`
- Aufgabe: zentrale Logansicht inklusive Massentest-Log.

### Export / ChatGPT

- `/test/chatgpt-active`
- Funktion: `chatgpt_active_regressions()` bei ca. Zeile 7369
- Aufgabe: Kopiervorlage fuer Regressionstest- und Massentest-Aufgaben.

## 3. Erkannte Doppelungen

### Statusdarstellungen

Aehnliche oder gleiche Statusdarstellungen existieren mehrfach:

- Dashboard-Kacheln in `status()`
- Testcenter-Kacheln in `testcenter_overview()` und `test_page()`
- Massentest-Gesamtuebersicht in `massentest_page()`
- Qualitaetscenter-Arbeitsnavigation in `massentest_page()` und `massentest_quality_center()`
- Projektcenter-Kacheln in `projektcenter()`
- Regression-Kacheln in `regression_page()`
- Export-Kacheln in `chatgpt_active_regressions()`

Zentrale Massentest-Statusfunktionen sind vorhanden:

- `massentest_row_status()` bei ca. Zeile 2475
- `massentest_load_view_rows()` bei ca. Zeile 2500
- `massentest_validation_stats()` bei ca. Zeile 2545
- `massentest_quality_stats()` bei ca. Zeile 2696
- `massentest_overview_status()` bei ca. Zeile 3671

Bewertung:

Die fachliche Richtung ist gut, aber die Darstellung wird noch an mehreren Stellen manuell gebaut. Fuer Final sollte die Statusberechnung zentral bleiben und die Anzeige ueber gemeinsame Komponenten laufen.

### Buttons / Aktionen

Wiederkehrende Aktionsmuster werden direkt in HTML-Blöcken gebaut:

- `btn`, `btn2`, `success`, `warn`, `danger`
- Formularbloecke fuer Speichern, Pruefen, Loeschen, Aufgabe anlegen, Ist-Werte uebernehmen
- Confirm-Attribute (`data-confirm-title`, `data-confirm-message`, `data-confirm-kind`)
- Working-Overlay-Attribute (`data-working`, `data-progress`)

Betroffene Seiten:

- Massentest-Pruefliste: `massentest_row_html()`
- alte Massentest-Ergebnisansicht: `massentest_result()`
- fachliche Schnellpruefung: `massentest_fachlich_view()`
- Sollwertbearbeitung: `massentest_detail()`
- Einzeltestliste: `render_test_overview_rows()`
- Einzeltestergebnis: `run_test()`
- Projektcenter-Aufgabe: `projekt_task_html()`

Bewertung:

Die Buttons sind funktional, aber nicht als fachliche Aktionstypen modelliert. Fuer Final sollten Aktionen wie `primaer`, `sekundaer`, `entscheidung_ok`, `entscheidung_warnung`, `gefahr`, `navigation_zurueck` zentral gerendert werden.

### Statuskarten / Kennzahlen

Karten mit Zahlen werden mehrfach manuell erzeugt:

- `.metric` im Dashboard
- `.metric` im Testcenter
- `.metric` in Regression
- `.card`-Kacheln im Projektcenter
- `.hint`/`count-badge` im Qualitaetscenter

Bewertung:

Nicht jede Wiederholung ist fachlich falsch, aber die visuelle Grammatik ist uneinheitlich: mal Statistik, mal Navigation, mal Hinweis. Final braucht eine klare Trennung:

- Statistik-Karte
- Arbeitsnavigation-Karte
- Statushinweis
- Warn-/Gefahrenhinweis

### PDF-Viewer

PDFs werden mehrfach unterschiedlich eingebunden:

- alte Massentest-Ergebnisansicht: `.massentest-detail-preview` mit iframe unten bei ca. Zeile 4669
- alte/normale Massentest-Sollwertansicht: `.massentest-detail-preview` mit iframe unten bei ca. Zeile 5265
- grosse Browser-Vorschau: `/test/massentest/pdf-view/{row_id}` bei ca. Zeile 4911
- neue fachliche Schnellpruefung: `.qc-fast-pdf` zweispaltig bei ca. Zeile 5056
- neue fachliche Sollwertbearbeitung: `.qc-fast-pdf` zweispaltig bei ca. Zeile 5207
- Einzeltest: PDF wird ueber `/test/open-pdf` extern geoeffnet, kein gemeinsames Panel.

Bewertung:

Das ist eine der groessten UI-Doppelungen. Final sollte ein einziges `render_pdf_panel()` verwenden, mit Varianten:

- `mode="inline"`
- `mode="fast_review"`
- `mode="large"`
- `allow_pan=True`
- `open_external=True`

### Soll/Ist-Tabellen

Soll/Ist-Vergleiche werden mehrfach gebaut:

- `massentest_result_values_html()`
- `massentest_fachlich_view()`
- `massentest_detail()`
- `run_test()`
- `run_all_tests()`
- `edit_expected()`

Bewertung:

Die Tabellen unterscheiden sich in Spalten, Statussymbolen, Scrollverhalten und Feldnamen. Final sollte ein gemeinsames `render_soll_ist_table()` bekommen, das Einzeltest und Massentest mit derselben Felddefinition bedienen kann.

### Qualitaetscenter / Massentest / Testcenter-Ueberlappung

Ueberlappungen:

- Dashboard zeigt Massentest-Kurzstatus.
- Testcenter zeigt Einzeltest und Massentest.
- Massentest-Seite enthaelt Qualitaetscenter, Massentest-Manager, Arbeitsablauf und Pruefliste.
- `/test/massentest/quality` dupliziert Teile der Arbeitsnavigation aus `/test/massentest`.
- `/regression` ist Produktivfreigabe-Vorstufe, haengt aber optisch am Testcenter.

Bewertung:

Fachlich sind das unterschiedliche Arbeitsbereiche, aber die Navigation fuehrt noch nicht klar genug:

- Testcenter = technische Testumgebung
- Qualitaetscenter = fachliche Qualitaetssicherung
- Projektcenter = Aufgaben
- Produktivcenter = kontrollierte Freigabe und echter Betrieb

### Hotfix-Kaskaden / nachtraegliche Wrapper

Am Dateiende existieren nachtraegliche Stabilisierungsschichten:

- `WEBUI 3.7.0 - FEHLERBEREICH & PRUEFSTATUS`
- `WEBUI 3.8.2 - ARBEITSSTAND / STABILISIERUNG`
- nachtraegliche Erweiterung von `MASSTEST_FIELDS`
- nachtraeglicher Wrapper fuer `massentest_write_results()`
- nachtraegliche Neudefinition von `massentest_validate_row()`

Bewertung:

Das ist fuer Alpha nachvollziehbar, aber fuer Final riskant. Besonders kritisch: Wenn eine FastAPI-Route bereits registriert wurde, kann eine spaetere Python-Neudefinition der Funktion die tatsaechlich registrierte Route nicht zwingend ersetzen. Dadurch kann Code im Dateiende anders aussehen als das, was FastAPI tatsaechlich ausliefert.

Empfehlung:

Diese Hotfix-Kaskaden im ersten Architektur-Sprint nicht sofort entfernen, aber im Zielbild als Konsolidierungsaufgabe festhalten:

- Wrapper aufloesen
- finale Funktion an Originalstelle integrieren
- Route und Implementierung eindeutig machen
- keine nachtraeglichen Monkey-Patches mehr

## 4. Alt-/Neu-Layouts

### Neue Layouts

Neuere, bessere Layouts:

- fachliche Schnellpruefung: `massentest_fachlich_view()`
- fachliche Sollwertbearbeitung mit `source=fachlich`: `massentest_detail()`
- Massentest-Pruefliste als gruppierte Karten: `massentest_grouped_overview_html()`
- Qualitaetscenter als Arbeitsnavigation in `massentest_page()`

Merkmale:

- zweispaltiges PDF/Werte-Layout
- sticky rechte Entscheidungsspalte
- getrennte technische und fachliche Statusanzeige
- Gruppenlogik: Abweichung, Offen, Nachzubearbeiten, Sonderfaelle, technisch bestanden / offen, technisch bestanden / validiert

### Alte Layouts

Alte oder abweichende Layouts:

- `massentest_result()` zeigt PDF unten und Werte oben.
- normale `massentest_detail()`-Ansicht ohne `source=fachlich` zeigt alte Sollwertbearbeitung mit PDF unten.
- `run_test()` im Einzeltest nutzt eigene Ergebnisstruktur mit `result-grid`.
- `edit_expected()` im Einzeltest nutzt eigene Sollwertmaske.
- `run_all_tests()` erzeugt eigene Tabellen und Metriken.
- Projektcenter-Aufgabenkarten nutzen eigene Struktur.

Bewertung:

Final sollte nicht versuchen, alle Seiten gleichzeitig neu zu bauen. Zuerst sollten die Dokumentansichten vereinheitlicht werden, weil dort die meiste praktische Reibung entsteht.

## 5. Empfohlene Zielnavigation

Der vorgeschlagene Navigationsrahmen ist sinnvoll, sollte aber leicht geschaerft werden.

Empfohlene Hauptnavigation fuer WebUI 4.0 Final:

1. Dashboard
2. Arbeitscenter
3. Projektcenter
4. Testcenter
5. Qualitaetscenter
6. Produktivcenter
7. Konfiguration
8. Lernlisten
9. Logs
10. System / Wartung

Begruendung:

- Dashboard bleibt Ueberblick, keine Detailarbeit.
- Arbeitscenter kann langfristig die alltaegliche Startflaeche werden, muss aber nicht sofort gebaut werden.
- Projektcenter bleibt Aufgabenverwaltung.
- Testcenter bleibt technische Regression / Einzeltest.
- Qualitaetscenter bleibt Massentest / fachliche Pruefung.
- Produktivcenter trennt echte Ablage, Produktivfreigabe und Betriebsfunktionen sichtbar vom Testbetrieb.
- Konfiguration, Lernlisten, Logs und System/Wartung sind administrative Bereiche.

Alternative, wenn weniger Hauptpunkte gewuenscht sind:

1. Dashboard
2. Arbeit
3. Tests
4. Qualitaet
5. Produktiv
6. Verwaltung

Fuer die naechsten Sprints ist die erste, explizitere Variante besser, weil sie weniger neue Begriffe einfuehrt.

## 6. Vorgeschlagene gemeinsame Komponenten

### `render_page_shell()`

Aktuell:

- `layout()` bei ca. Zeile 157 erzeugt Header, Navigation, CSS, JS, Working-Overlay und Confirm-Modal in einem Block.

Profitierende Seiten:

- alle Seiten

Risiko:

- Mittel bis hoch, weil jede Route betroffen ist.

Empfehlung:

- Erst extrahieren, wenn CSS/JS nicht mehr bei jedem kleinen Layoutthema mitveraendert werden muessen.
- Vorher nur Zielstruktur dokumentieren.

### `render_navbar()`

Aktuell:

- Navigation ist hart in `layout()` definiert.
- Aktive Bereiche werden nicht zentral markiert.
- Produktivcenter / System / Wartung fehlen als eigene Punkte.

Profitierende Seiten:

- alle Seiten

Risiko:

- Niedrig bis mittel.

Empfehlung:

- Erster sinnvoller Umsetzungsschritt in Sprint 1A.

### `render_status_card()`

Aktuell:

- `.metric`, `.card`, `.hint`, `.count-badge` werden mehrfach manuell genutzt.

Profitierende Seiten:

- Dashboard
- Projektcenter
- Testcenter
- Massentest
- Regression
- Exportseite

Risiko:

- Mittel, weil viele Texte/Kennzahlen betroffen sind.

Empfehlung:

- Zuerst nur neue Hilfsfunktion einfuehren und auf einer Seite testen, danach schrittweise migrieren.

### `render_work_card()`

Zweck:

- Arbeitsnavigation ohne Statistik-Dashboard-Charakter.

Aktuell:

- Qualitaetscenter nutzt `hint`-Links mit `count-badge`.
- Dashboard/Testcenter nutzen dagegen `metric`.

Profitierende Seiten:

- Qualitaetscenter
- Testcenter
- Projektcenter
- spaeter Arbeitscenter

Risiko:

- Niedrig bis mittel.

### `render_button_group()`

Aktuell:

- Button-Gruppen werden in vielen HTML-Strings direkt gebaut.
- Confirm- und Working-Attribute sind verstreut.

Profitierende Seiten:

- Massentest-Pruefliste
- fachliche Pruefung
- Sollwertbearbeitung
- Einzeltest
- Projektcenter

Risiko:

- Mittel, weil Formular-Aktionen erhalten bleiben muessen.

Empfehlung:

- Nicht mit Datenlogik koppeln. Nur HTML fuer bekannte Aktionen zentralisieren.

### `render_document_view()`

Zweck:

- Gemeinsames Grundlayout fuer Dokumentpruefung: links PDF, rechts Status/Werte/Aktionen.

Aktuell:

- neue fachliche Schnellpruefung ist schon nah am Ziel.
- alte Ergebnis- und Sollwertseiten haben noch PDF unten.

Profitierende Seiten:

- fachliche Schnellpruefung
- Abweichungsansicht
- Nacharbeit
- Sonderfall
- Sollwerte bearbeiten
- Einzeltest-Ergebnis

Risiko:

- Mittel bis hoch.

Empfehlung:

- Sprint 1B, nicht Sprint 1A.

### `render_pdf_panel()`

Aktuell:

- PDF-iframe unten, links, gross, extern und Reader-Button sind separat gebaut.

Profitierende Seiten:

- Massentest Ergebnis
- fachliche Pruefung
- Sollwerte bearbeiten
- grosse Vorschau
- Einzeltest

Risiko:

- Mittel.

Empfehlung:

- Als erstes Dokument-Komponenten-Element herausziehen, da klar abgrenzbar.

### `render_field_table()`

Aktuell:

- Ist-Werte-Tabellen werden mehrfach gebaut.

Profitierende Seiten:

- fachliche Schnellpruefung
- Massentest-Ergebnis
- Einzeltest-Ergebnis
- Sollwertbearbeitung

Risiko:

- Mittel.

### `render_decision_panel()`

Aktuell:

- Pruefentscheidung gibt es in `massentest_result()`, `massentest_fachlich_view()`, `massentest_detail()`, `run_test()` mit unterschiedlichen Buttons und Texten.

Profitierende Seiten:

- alle Dokumentpruefseiten

Risiko:

- Mittel bis hoch, weil jeder Button Workflow ausloest.

Empfehlung:

- Zuerst nur visuelle Struktur vereinheitlichen, Endpunkte unveraendert lassen.

### `render_soll_ist_table()`

Aktuell:

- Massentest und Einzeltest bauen Soll/Ist-Tabellen getrennt.

Profitierende Seiten:

- Massentest
- Testcenter
- Regression
- Build-Vergleich

Risiko:

- Mittel bis hoch, weil Statussymbole und Feldlisten fachlich relevant sind.

Empfehlung:

- Erst nach Sprint 1B, sobald Dokumentansicht stabil ist.

### `render_message_box()`

Aktuell:

- `flash`, `hint`, Fehlerkarten, Warnhinweise, Blocker/Hinweis-Texte sind direkt eingebettet.

Profitierende Seiten:

- alle Seiten

Risiko:

- Niedrig.

Empfehlung:

- Gute kleine Einstiegskomponente.

## 7. Test-/Produktivtrennung

### Eindeutig Testbereich

- `_web_test`
- `_web_test/_expected`
- `_web_test/_reports`
- `_web_test/_status`
- `_massentest`
- `_massentest/ergebnisse/massentest_ergebnisse.json`
- `_massentest/ergebnisse/massentest_sollwerte.json`
- `/test`
- `/test/einzeltest`
- `/test/massentest`
- `/test/run`
- `/test/run-all`
- `/test/chatgpt-active`

### Produktivnahe / Produktivbereich

- `ecodms_scan_input`
- `mail_input`
- `_arbeit`
- `_erledigt`
- `_fehler`
- `_gefiltert`
- `zaehler.txt`
- `box_konfiguration.txt`
- `import_optionen_konfiguration.txt`
- `dateiname_konfiguration.txt`
- Scan-Service- und Outlook-Watcher-Status im Dashboard
- `/regression` als Produktivfreigabe-Vorstufe

### Potenzielle Verwechslungen

- Dashboard zeigt Test- und Produktivzahlen nebeneinander.
- Testcenter zeigt Produktiv-Ablage und Test-Ablage gemeinsam.
- Dateiname-Konfiguration enthaelt Produktiv- und Testarchiv in einer Maske.
- `/regression` heisst technisch Regression, ist aber als Produktivfreigabe-Seite beschrieben.
- Qualitaetscenter/Massentest ist Testbereich, fuehlt sich aber durch fachliche Pruefung wie Produktionsvorbereitung an.

### Empfohlene sichtbare Kennzeichnungen

Zentrale Badges:

- `TEST`
- `PRODUKTIV`
- `ALPHA`
- `Regression`
- `Massentest`
- `Referenzbestand`
- `Produktivfreigabe`

Regel:

- Jede Seite soll oben genau einen Bereichsstatus zeigen.
- Testseiten duerfen niemals wie Produktivseiten wirken.
- Produktivseiten muessen optisch ruhiger und sicherheitsbetonter sein.
- Gefahrenbereiche bleiben eingeklappt und klar beschriftet.

## 8. Priorisierte Sprintplanung

### Sprint 1A - WebUI-Grundlayout

Ziel:

Navigation, Page-Shell, Header, einheitliche Karten/Buttons.

Umfang:

- `render_navbar()` vorbereiten.
- Bereichskennung einfuehren: TEST / PRODUKTIV / ALPHA / Massentest / Regression.
- `render_message_box()` einfuehren.
- Button-Varianten definieren, aber noch nicht alle Seiten migrieren.
- Dashboard nicht inhaltlich umbauen, nur Layoutregeln klaeren.

Nicht tun:

- keine Statuslogik aendern
- keine Routen entfernen
- keine Massentestdaten migrieren
- keine Extraktionslogik

Risiko:

- Niedrig bis mittel.

### Sprint 1B - Dokumentansicht

Ziel:

Fachliche Pruefung, Abweichung, Nacharbeit und Sollwerte auf gemeinsames Layout bringen.

Umfang:

- `render_pdf_panel()`
- `render_document_view()`
- `render_decision_panel()`
- alte Massentest-Ergebnisansicht `massentest_result()` auf neues zweispaltiges Layout bringen.
- normale Sollwertansicht in `massentest_detail()` vereinheitlichen.
- Einzeltest-Ergebnis als spaeteren Kandidaten vorbereiten.

Nicht tun:

- keine neue Fachlogik
- keine Statusaenderungen
- keine neuen Workflows

Risiko:

- Mittel bis hoch.

### Sprint 1C - Center-Struktur

Ziel:

Projektcenter, Testcenter, Qualitaetscenter und Produktivcenter sauber trennen und vereinheitlichen.

Umfang:

- Testcenter nur technische Tests / Regression.
- Qualitaetscenter nur fachliche Massentest-Arbeit.
- Projektcenter nur Aufgaben.
- Produktivcenter als sichtbare, aber sichere Vorbereitungsseite.
- `/regression` entweder ins Produktivcenter einordnen oder klar als Regression/Freigabe kennzeichnen.

Risiko:

- Mittel.

### Sprint 1D - Produktivvorbereitung

Ziel:

Produktivworkflow sichtbar, aber sicher getrennt vom Testbetrieb vorbereiten.

Umfang:

- Produktivcenter mit Status, Freigabehinweisen, Scan-Service/Outlook-Zustand.
- Klare Abgrenzung zu Testcenter und Massentest.
- Keine echten produktiven Aktionen ohne ausdrueckliche Sicherheitsabfrage.

Risiko:

- Mittel.

### Sprint 2 - Qualitaetsanalyse

Ziel:

Delta-Berichte, Build-Vergleich und automatische Statistik.

Umfang:

- Build-zu-Build-Vergleich.
- Feldstatistik automatisch erzeugen.
- nur veraenderte/problematische Dokumente manuell pruefen.
- Berichte aus Massentest-Soll/Ist-Daten ableiten.

Risiko:

- Niedrig bis mittel, solange rein auswertend.

### Sprint 3 - Extraktionsqualitaet

Ziel:

Feldlogik, Bonprix, Behoerden, Dokumenttyp, Nummern, Betraege.

Umfang:

- RECHNR/KUNDENNR/Betrag/Dateiname verbessern.
- Bonprix-Labelbloecke.
- Dokumenttyp-Prioritaet.
- pauschales Feld-Clearing entschaerfen.
- AKTENZEICHEN als Service-Metafeld sauber loesen.

Risiko:

- Hoch.

Voraussetzung:

- 128er Regressionstest.
- Delta-Bericht.
- klare manuelle Pruefliste nur fuer veraenderte/problematische Dokumente.

## 9. Risiken

### Monolithische Datei

`ecodms_webui.py` enthaelt UI, Datenzugriff, Workflow, Statuslogik, CSS und JavaScript. Jede Aenderung hat potentiell groesseren Seiteneffekt.

### Nachtraegliche Funktionsueberschreibungen

Wrapper und Neudefinitionen am Dateiende koennen vom tatsaechlich registrierten FastAPI-Endpunkt abweichen. Das erschwert Debugging und war bereits praktisch relevant.

### Uneinheitliche Dokumentansichten

Alte und neue Ansichten koennen unterschiedliche Navigation, PDF-Position, Buttons und Statusanzeige haben.

### Doppelte Statusvisualisierung

Statusberechnung ist teilweise zentralisiert, aber Statusanzeige nicht. Dadurch koennen neue Begriffe wieder doppelt oder widerspruechlich erscheinen.

### Test/Produktiv-Mischung

Testdaten, Referenzen, Regression und Produktivfreigabe liegen in der Navigation nahe beieinander. Fuer Anwender muss jederzeit klar sein, ob sie Testdaten oder echte Produktivablaeufe sehen.

### Direktes HTML in Python-Strings

Grosse f-Strings erschweren Wiederverwendung und Tests. Kleine Layoutaenderungen koennen Syntaxfehler oder unerwartete HTML-Strukturprobleme erzeugen.

## 10. Empfohlener erster Umsetzungsschritt

Empfohlener Start: Sprint 1A, aber sehr klein beginnen.

Erster konkreter Schritt:

1. `render_message_box()` und `render_navbar()` als kleine, reine HTML-Helfer vorbereiten.
2. Navigation um klare Bereichsstruktur erweitern, aber bestehende Routen beibehalten.
3. Aktive Bereichskennung einfuehren: `TEST`, `PRODUKTIV`, `ALPHA`, `Massentest`, `Regression`.
4. Keine Dokumentansichten in Sprint 1A anfassen, bis die Shell stabil ist.

Warum dieser Schritt zuerst:

- geringes fachliches Risiko
- hohe sichtbare Wirkung
- schafft Basis fuer spaetere Komponenten
- beruehrt keine Erkennung, keine Massentestdaten, keine Aufgabenlogik

Danach:

- Sprint 1B mit `render_pdf_panel()` und gemeinsamer Dokumentansicht.
- Erst danach Center-Struktur und Produktivcenter konsolidieren.

## 11. Zielbild WebUI 4.0 Final

WebUI 4.0 Final sollte sich nicht mehr wie eine Sammlung einzelner Werkzeuge anfuehlen, sondern wie eine zusammenhaengende lokale Arbeitsoberflaeche.

Zielprinzipien:

- eine Navigation
- eine Page-Shell
- ein Buttonsystem
- ein PDF-Panel
- eine Dokumentansicht
- eine Soll/Ist-Tabelle
- eine Aufgabenquelle
- klare Trennung von Test und Produktiv
- keine nachtraeglichen Hotfix-Wrapper als Dauerarchitektur
- keine doppelte Statusdarstellung

Kurzform:

Dashboard zeigt den Zustand.
Arbeitscenter fuehrt durch den Alltag.
Projektcenter verwaltet Aufgaben.
Testcenter prueft Technik.
Qualitaetscenter prueft fachlich.
Produktivcenter bereitet echte Freigabe sicher vor.
