# Build 16C - Extraktionsqualitaet Plan

## 1. Ziel Build 16C

Build 16C soll kein Feature-Build werden, sondern ein kontrollierter Qualitaetsbuild fuer die Extraktionslogik.

Ziel ist, die strukturellen Ursachen der Erkennungsfehler gezielt und nachvollziehbar zu verbessern, ohne neue Workflows, neue Statusmodelle oder grosse Architekturumbauten einzufuehren.

Im Mittelpunkt stehen:

- stabile Feldextraktion
- weniger nachgelagerte Feldueberschreibungen
- nachvollziehbare Prioritaeten fuer Lieferant und Dokumenttyp
- bessere Trennung von Nummernfeldern
- reproduzierbare Regressionstests mit den bestehenden 128 Referenzdokumenten

## 2. Nicht aendern

Fuer Build 16C sollen ausdruecklich nicht umgesetzt werden:

- keine grosse Architekturaenderung
- keine neue Entscheidungsmaschine
- keine Layoutanalyse
- keine Template-Erkennung
- keine breiten Sonderregeln
- keine produktive Logikaenderung ohne Regressionstest
- keine neuen Statusmodelle
- keine neuen WebUI-Workflows
- keine Aenderungen am Scan-Service ausser gezielten, freigegebenen Qualitaetskorrekturen

## 3. Kandidaten fuer risikoarme Massnahmen

Moegliche risikoarme Massnahmen fuer Build 16C:

- Feldfluss-Auswertung je Problemfeld verbessern
- AKTENZEICHEN als Service-Metafeld verankern
- pauschales Nummern-Clearing entschaerfen
- Dokumenttyp-Prioritaet verbessern: Behoerde, Info, Bescheid und Register vor Rechnung
- Label-Wert-Bloecke fuer Nummern verbessern
- Regressionstest mit denselben 128 Referenzdokumenten erzwingen

Wichtig:
Jede Massnahme soll einzeln bewertet, umgesetzt und gegen die 128 Referenzdokumente getestet werden. Erst wenn die Trefferquote und die Regressionsliste bewertet sind, darf die naechste Massnahme folgen.

## 4. Betroffene Problemfelder

Die wichtigsten Problemfelder aus der bisherigen Alpha-Auswertung:

- Neuer Dateiname
- KUNDENNR
- GESAMTBETRAG
- RECHNR
- Lieferant
- Dokumenttyp
- AKTENZEICHEN

Einordnung:

- Neuer Dateiname ist ein Folgefeld und buendelt Fehler aus Datum, Lieferant und Nummernlogik.
- KUNDENNR und RECHNR sind besonders anfaellig fuer Label-Wert-Bloecke und nachgelagertes Clearing.
- GESAMTBETRAG haengt stark vom Dokumenttyp ab.
- Lieferant und Dokumenttyp erzeugen viele Folgefehler.
- AKTENZEICHEN ist in WebUI und Massentest vorhanden, aber noch nicht sauber als Service-Metafeld verankert.

## 5. Risiken

Wesentliche Risiken bei Build 16C:

- Verbesserungen an Wrappern koennen andere Lieferanten verschlechtern.
- Entschaerftes Feld-Clearing kann den Schutz vor Fehltreffern reduzieren.
- Dokumenttyp-Aenderungen beeinflussen Betrags- und Nummernlogik.
- AKTENZEICHEN muss sauber von RECHNR getrennt bleiben.
- Eine zu breite Korrektur von Rechnungserkennung kann echte Rechnungen verschlechtern.
- Eine zu starke Lieferantenpriorisierung aus dem Kopfbereich kann Empfaenger, Bankverbindungen oder Registerinformationen falsch als Lieferant uebernehmen.
- Label-Wert-Verbesserungen duerfen keine Tabellenwerte aus Artikelpositionen als Nummern uebernehmen.

## 6. Vorgehen

Empfohlene Reihenfolge fuer Build 16C:

1. Status quo sichern.
2. Feldfluss-Diagnose auswerten.
3. Eine kleine Aenderung planen.
4. Aenderung gezielt umsetzen.
5. 128er Regression laufen lassen.
6. Trefferquote vergleichen.
7. Regressionen und Verbesserungen dokumentieren.
8. Erst danach die naechste Aenderung bewerten.

Pflicht fuer jede Aenderung:

- Vorher-/Nachher-Vergleich je Feld
- Liste verbesserter Dokumente
- Liste verschlechterter Dokumente
- Bewertung, ob die Aenderung allgemein oder nur ein Einzelfall ist
- Entscheidung, ob die Aenderung bleiben darf

Build 16C soll damit eine saubere Entscheidungsgrundlage fuer gezielte Extraktionsverbesserungen schaffen, ohne die Alpha durch unkontrollierte Erkennungsregeln zu destabilisieren.
