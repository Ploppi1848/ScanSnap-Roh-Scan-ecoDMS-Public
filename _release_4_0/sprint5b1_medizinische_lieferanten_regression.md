# Sprint 5B.1 - Regression medizinische Lieferantenlogik

## Ausgangslage

Sprint 5B brachte im Buildvergleich:

- Verbesserung: `Lowenstein Medical Anderes 07.11.2025.pdf`
- neue Auffaelligkeit: `Heinz-Georg Hepp Information 24.04.2026.pdf`
- neue Auffaelligkeit: `LVM Versicherungen Anderes 02.03.2020.pdf`

Damit war Sprint 5B noch nicht commitfaehig. Ziel von Sprint 5B.1 ist eine engere, generische Eingrenzung der medizinischen Kopfbereichslogik ohne neue Einzelfall-Kaskade.

## Ursache der zwei neuen Auffaelligkeiten

### Heinz-Georg Hepp Information 24.04.2026.pdf

OCR-Kopfbereich:

- `Dr. med. U. Neukirchen Ruesenacker 1 44799 Bochum`
- `Dr. med. Uta Neukirchen`
- `Fachaerztin fuer Orthopaedie`

Ursache:

Die neue 6.5-Logik bewertete die erste Zeile zu stark. Diese Zeile enthaelt zwar einen medizinischen Kandidaten, aber auch Adresse und Postleitzahl. Dadurch entstand als Lieferant:

`Dr. med. U. Neukirchen Ruesenacker 1 44799 Bochum`

Das war fachlich schlechter als der erwartete Praxisname.

Korrektur:

- Kopfzeilen mit Postleitzahl oder Strassen-/Adressmustern werden fuer medizinische Lieferanten verworfen.
- Wenn ein sauberer `Dr.`-Name mit angrenzender orthopaedischer Facharztzeile gefunden wird, wird generisch ein vollstaendiger Praxisname gebildet:
  - `Orthopädische Facharztpraxis <Dr.-Name>`
- Bereits vorhandene starke medizinische Lieferanten werden nicht mehr per Force ersetzt.

### LVM Versicherungen Anderes 02.03.2020.pdf

OCR-Kopfbereich:

- `LVM Landwirtschaftlicher Versicherungsverein Muenster a.G.`
- `Aufsichtsratsvorsitzender: ..., Vorstand: Dr. Mathias Kleuker ...`
- weitere Vorstands-/Register-/Versicherungszeilen

Ursache:

Die 6.5-Logik sah `Dr.` in einer Vorstandszeile und behandelte diese Zeile faelschlich als medizinischen Kandidaten. Dabei war bereits `LVM Versicherung` ein plausibler starker Nicht-Medizin-Lieferant.

Korrektur:

- Vorstands-, Aufsichtsrats-, Geschaeftsfuehrer-, Register-, USt-, Versicherungs-, Bank- und BaFin-Kontexte werden fuer medizinische Kandidaten verworfen.
- Medizinische Logik darf nicht ueber einen plausiblen starken Lieferanten gewinnen, nur weil irgendwo ein `Dr.` im Formular-/Fliesstext steht.

## Geaenderte Eingrenzung der Medizinlogik

Geaendert in `_service/ecodms_scan_service.py`:

- `_med_line_bad_650(...)`
  - verwirft nun zusaetzlich:
    - Postleitzahl-/Adresszeilen
    - Strassen-/Ring-/Weg-/Platz-/Gasse-Muster
    - Vorstand / Aufsichtsratsvorsitzender / Geschaeftsfuehrer
    - Registergericht / HR B / USt-ID
    - Versicherungsverein / Versicherung / Versicherungs-AG
    - Sparkasse / SWIFT / BaFin
- `_med_line_has_marker_650(...)`
  - kurze Marker wie `dr`, `mvz`, `prof` muessen als Wort vorkommen, nicht nur als beliebiger Teilstring.
- `_med_enrich_candidate_650(...)`
  - bildet generisch aus `Dr.-Name` plus benachbarter orthopaedischer Facharztzeile einen vollstaendigeren Praxisnamen.
- `_med_should_force_650(...)`
  - erzwingt keinen Ersatz mehr, wenn bereits ein starker vollstaendiger medizinischer Lieferant vorhanden ist.

## Warum Lowenstein weiterhin funktionieren sollte

Der Lowenstein-Fall bleibt vom Fix bewusst unberuehrt:

- OCR-Kopfbereich enthaelt eine klare Zeile `Loewenstein Medical`.
- Diese Zeile ist kein Patient, keine Empfaengerzeile, keine Vorstands-/Versicherungszeile und keine Adresse.
- `Medical` bleibt als medizinisches Kopfbereichssignal erlaubt, wenn es Teil eines vollstaendigen Namens ist.
- Die neue Adressfilterung trifft erst Zeilen mit PLZ/Strassenmustern, nicht die eigentliche Lieferantenzeile.

Damit sollte `Lowenstein Medical Anderes 07.11.2025.pdf` verbessert bleiben.

## Risiken

- Bei Dokumenten, deren einziger Lieferantenhinweis nur in einer kombinierten Namens-/Adresszeile steht, kann die neue Adressfilterung zu streng sein.
- Die generische Bildung `Orthopädische Facharztpraxis <Dr.-Name>` ist bewusst eng an orthopaedische Facharztkontexte gebunden, sollte aber im Buildvergleich beobachtet werden.
- Versicherungen mit medizinischem Inhalt bleiben heikel, weil sie medizinische Begriffe enthalten koennen, ohne medizinischer Leistungserbringer zu sein.

## Testhinweise

Im naechsten 128er Buildvergleich gezielt pruefen:

- `Lowenstein Medical Anderes 07.11.2025.pdf`
  - Lieferant soll `Löwenstein Medical` bleiben.
- `Heinz-Georg Hepp Information 24.04.2026.pdf`
  - keine Adresszeile als Lieferant.
  - erwarteter Lieferant: `Orthopädische Facharztpraxis Dr. med. Uta Neukirchen`.
- `LVM Versicherungen Anderes 02.03.2020.pdf`
  - Lieferant soll `LVM Versicherung` bleiben.
  - keine Vorstandszeile als Lieferant.

Zusätzlich im Log nach `SUPPLIER_DECISION` suchen:

- medizinische Kopfzeile wegen Patient/Empfaenger verworfen
- medizinisches Fragment verworfen
- medizinischer Kandidat gefunden
- medizinischer Kandidat bevorzugt

## Pruefung

Durchgefuehrt:

- `python -m py_compile _service\ecodms_scan_service.py`
- zusaetzliche AST-Syntaxpruefung ohne Bytecode-Artefakt

Nicht durchgefuehrt:

- Kein 128er Regressionstest, damit keine Massentestdaten veraendert werden.
- Keine Referenzdaten geaendert.
- Keine Git-Befehle ausgefuehrt.

## Bewusst nicht geaendert

- Keine WebUI.
- Keine Massentestdaten.
- Keine Referenzdaten.
- Keine OCR.
- Keine Git-Befehle.
- Keine Behoerdenlogik.
- Keine Bankenlogik.
- Keine Aliaslisten.
- Keine Einzelfall-Kaskade.
