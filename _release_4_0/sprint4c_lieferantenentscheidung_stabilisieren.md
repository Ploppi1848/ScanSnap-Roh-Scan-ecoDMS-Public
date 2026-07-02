# Sprint 4C - Lieferantenentscheidung stabilisieren

## Ausgangslage aus Sprint 4B

Sprint 4B zeigte:

- Aktueller Massenteststand: 39 Lieferantenabweichungen.
- In 27 Faellen ist der Soll-Lieferant im OCR-/Debugtext vorhanden, gewinnt aber nicht.
- Wiederkehrende spaete Gewinner sind unter anderem:
  - Amtsgericht Bochum
  - Telekom
  - Amazon
  - LVM
  - Santander Consumer Bank AG
  - Sparda-Bank West eG

Fazit: Der richtige Lieferant wird haeufig erkannt, aber spaeter durch andere Kandidaten verdraengt. Sprint 4C stabilisiert deshalb die Lieferantenentscheidung, ohne eine neue Erkennungsengine oder neue breite Sonderfallkaskaden einzubauen.

## Geaenderte Lieferantenentscheidungslogik

Geaendert wurde ausschliesslich `_service/ecodms_scan_service.py`.

### Zentrale Schutzlogik erweitert

Die bestehende `safe_set_meta(...)`-Logik wurde erweitert:

- Neue Liste schwacher spaeter Gewinner:
  - `Amtsgericht Bochum`
  - `Telekom`
  - `Amazon`
  - `LVM`
  - `LVM Versicherung`
  - `Santander`
  - `Santander Consumer Bank`
  - `Santander Consumer Bank AG`
  - `Sparda Bank`
  - `Sparda-Bank West eG`
- Wenn bereits ein plausibler Lieferant vorhanden ist, darf ein solcher spaeter Kandidat ihn nicht mehr ohne Weiteres ersetzen.
- Erlaubt bleiben:
  - leeres/schwaches Feld fuellen
  - normalisierte Varianten
  - plausible Lieferantenvarianten, z. B. Langform/Kurzform desselben Namens
  - klar bessere Kandidaten aus der Lieferantenkonfiguration

### Plausible Varianten bleiben moeglich

Damit Sprint 3C nicht wieder zu streng wird, blockiert die Logik nicht pauschal jeden Wechsel. Varianten werden weiterhin erlaubt, wenn der bestehende und der neue Wert normalisiert zusammenpassen.

Beispiele:

- `Santander Consumer Bank` zu `Santander Consumer Bank AG`
- Schreibvarianten, bei denen ein Wert den anderen enthaelt

### Spaete direkte Setzer angebunden

Einige spaete Wrapper hatten `LIEFERANT` noch direkt geschrieben. Diese Pfade wurden risikoarm an `safe_set_meta(...)` angebunden:

- `6.1 Lieferantenoffensive`
- `6.3 Aktenzeichen-Kontext` fuer Staatsanwaltschaft
- `6.4.1 Tintenfass-Stabilisierung`
- `6.4.1 Vorwerk-Stabilisierung`

Damit laufen diese spaeten Aenderungen ebenfalls durch die zentrale Lieferantenentscheidung und erzeugen Diagnose-Logging.

## Begrenzte spaete Gewinner

Gezielt begrenzt wurden schwache/spaete Ueberschreibungen durch:

- Amtsgericht Bochum
- Telekom
- Amazon
- LVM / LVM Versicherung
- Santander / Santander Consumer Bank / Santander Consumer Bank AG
- Sparda Bank / Sparda-Bank West eG

Wichtig: Diese Lieferanten sind nicht verboten. Sie duerfen weiterhin gesetzt werden, wenn das Feld leer/schwach ist oder wenn es sich um einen plausiblen echten Kontext handelt. Blockiert wird nur der Fall, dass ein bereits plausibler Lieferant ohne ausreichend starke Begruendung verdraengt wuerde.

## Logging / Diagnose

Neu ist Logging mit Praefix:

`SUPPLIER_DECISION`

Pro Entscheidung werden protokolliert:

- erlaubt oder blockiert
- alter Wert
- neuer Wert
- Quelle / Funktion ueber den `reason`-Text
- Grund der Entscheidung

Beispiele fuer Gruende:

- `leerem/schwachem Ausgangswert`
- `normalisierter Variante`
- `plausible Lieferantenvariante`
- `besserer Kandidat aus Lieferanten-Konfiguration`
- `spaeter schwacher Gewinner wuerde plausiblen Lieferanten ersetzen`

Zusatz: Bestehende `SAFE_META`-Logs bleiben erhalten.

## Risiken

- Ein tatsaechlich richtiger spaeter Kandidat aus der schwachen Gewinnerliste koennte blockiert werden, wenn vorher bereits ein plausibler, aber falscher Lieferant gesetzt wurde.
- Die Entscheidung kennt noch keinen vollstaendigen Quellenkontext wie konkrete Zeilennummer, Kopfbereich oder Fusszeile.
- Direkte Altzuweisungen in sehr alten Wrappern koennen weiterhin existieren. Sprint 4C bindet die spaetesten und aktuell kritischsten Pfade an die Schutzlogik an, ohne eine breite Umbauwelle zu starten.
- Der Nettoeffekt muss im Buildvergleich gemessen werden.

## Testhinweise

Empfohlene Kontrolle im naechsten 128er Regressionstest:

- Bausparkasse Schwaebisch Hall AG vs Sparda-Bank West eG
- Stadt Bochum vs Amtsgericht Bochum
- Bonprix vs Amazon
- Franke/Gartenbau vs Amtsgericht Bochum
- Lehner und Kollegen vs Telekom
- Santander-Finanzierung vs fachlicher Lieferant
- Sparda-Faelle: echte Bankdokumente duerfen nicht schlechter werden

Im Log gezielt nach `SUPPLIER_DECISION` suchen und pruefen:

- Wurde ein spaeter Kandidat blockiert?
- Welcher vorherige Lieferant wurde geschuetzt?
- War der Schutz fachlich korrekt?
- Gibt es echte Dokumente, bei denen der spaete Kandidat haette gewinnen muessen?

## Erwarteter Nutzen

- Weniger Lieferantenabweichungen durch spaete falsche Gewinner.
- Weniger Folgefehler beim neuen Dateinamen.
- Bessere Nachvollziehbarkeit der Lieferantenwechsel.
- Keine neue Erkennungsengine, sondern kontrollierte Stabilisierung der vorhandenen Pipeline.

## Bewusst nicht geaendert

- Keine WebUI-Layoutaenderungen.
- Keine Massentest-Datenstruktur.
- Keine Referenzdaten.
- Keine produktiven Aktionen.
- Keine Git-Befehle.
- Keine OCR-Umstellung.
- Keine breite neue Sonderfall-Kaskade.
- Keine grosse Pflege von `lieferanten_konfiguration.txt`.

## Pruefung

Durchgefuehrt:

- Syntaxpruefung: `python -m py_compile _service\ecodms_scan_service.py`

Nicht durchgefuehrt:

- Kein 128er Regressionstest, damit keine Massentestdaten veraendert werden.
- Keine Referenzdaten geaendert.
