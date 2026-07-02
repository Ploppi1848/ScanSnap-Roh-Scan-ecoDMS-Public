# Sprint 5B - Medizinische Lieferanten

## Ausgangslage

Sprint 5A hat medizinische/Praxis-Dokumente als groessten zusammenhaengenden Lieferantenfehler-Cluster identifiziert.

Betroffene Beispiele:

- Dr. med. Fahim Ayami
- Dr. med. dent. Axel Vieler
- St. Josef-Hospital Bochum
- Loewenstein Medical
- Tierarztpraxis Judith Schoenenstein
- Tibisco Haustierservice

Gemeinsame Ursache:

Praxis-, Klinik- und Arztnamen stehen haeufig im Briefkopf, werden aber nur als Fragmente erkannt oder verlieren gegen generische medizinische Begriffe.

## Neue generische Erkennung

In `_service/ecodms_scan_service.py` wurde eine kleine, isolierte Schicht ergaenzt:

`SCAN-SERVICE 6.5 - MEDIZINISCHE LIEFERANTEN GENERISCH`

Die neue Logik laeuft nach der bestehenden Erkennung und sucht nur in medizinischem Kontext nach starken Lieferantenkandidaten im Kopfbereich.

Kernfunktionen:

- `_med_header_supplier_candidate_650(...)`
- `_med_candidate_score_650(...)`
- `_med_line_bad_650(...)`
- `_med_is_fragment_650(...)`
- `_apply_medizinische_lieferanten_650(...)`

Die bestehende `safe_set_meta(...)`-Logik wird weiterverwendet. Damit bleiben Lieferantenwechsel nachvollziehbar und laufen durch `SUPPLIER_DECISION`.

## Erkannte medizinische Muster

Als medizinische Kopfbereichssignale werden generisch bewertet:

- Praxis
- Gemeinschaftspraxis
- Klinik
- Krankenhaus
- Hospital
- Medical
- Medizin
- MVZ
- Dr.
- Dres.
- Professor / Prof.
- Zahnarzt / Zahnmedizin
- Facharzt
- Tierarzt / Tierarztpraxis
- Haustier
- Physiotherapie
- Ergotherapie
- Therapie
- Labor
- Orthopaedie / Orthopaed

Ein Kandidat wird nur uebernommen, wenn er im oberen Dokumentbereich ausreichend stark ist und nicht wie Patient, Empfaenger, Kontaktzeile oder reines Fragment wirkt.

## Fragmentbehandlung

Nicht als Endwert bevorzugt werden generische Fragmente wie:

- Praxis
- Gemeinschaftspraxis
- Tierarztpraxis
- Medical
- Krankenhaus
- Klinik
- Hospital
- Medizin
- MVZ
- Dr.
- Dres.
- Professor
- Zahnarzt
- Tierarzt
- Therapie
- Labor

Wenn ein laengerer vollstaendiger Name im Kopfbereich vorhanden ist, darf dieser gegen solche Fragmente gewinnen.

Beispielprinzip:

- nicht: `Tierarztpraxis`
- besser: `Tierarztpraxis <vollstaendiger Name>`

Es wurden keine neuen Einzelfallregeln wie `if "Axel Vieler"` oder `if "Ayami"` eingebaut.

## Patient / Empfaenger

Patienten- und Empfaengerzeilen werden ausdruecklich abgewertet bzw. verworfen.

Abgewertete Muster:

- Heinz-Georg Hepp
- H.-G. Hepp
- Simone Hepp
- Patient / Patientin
- Versicherter / Versicherte
- Geburtsdatum / Geb. / Geb. am
- Anschrift / Adresse
- Empfaenger
- Rechnungsempfaenger
- Lieferadresse
- Kunden-/Versicherungsnummer
- Telefon / Fax / E-Mail / Web / IBAN / BIC

Damit sollen Patient, Versicherter oder Rechnungsempfaenger nicht als Lieferant gesetzt werden.

## Logging

Das bestehende `SUPPLIER_DECISION`-Logging wurde fuer medizinische Entscheidungen erweitert.

Neue Logmeldungen:

- medizinischer Kandidat gefunden
- medizinische Kopfzeile wegen Patient/Empfaenger verworfen
- medizinisches Fragment verworfen
- medizinischer Kandidat bevorzugt

Damit ist sichtbar, ob der Kopfbereich gegriffen hat und ob ein Fragment bewusst nicht als Endwert uebernommen wurde.

## Risiken

- Medizinische Dokumente enthalten oft mehrere fachliche Rollen: Patient, Praxis, Klinik, Labor, Versicherung und Leistungserbringer.
- Ein starkes Kopfbereichsmuster kann in Einzelfaellen auch eine Klinik, ein Labor oder eine Versicherung bevorzugen, obwohl die Praxis fachlich gemeint ist.
- OCR-Logo-Faelle bleiben begrenzt loesbar, wenn der vollstaendige Name gar nicht als Text vorhanden ist.
- Die neue Logik ist bewusst generisch und ersetzt keine spaetere Kandidaten-/Konfidenzarchitektur.

## Erwarteter Qualitaetsgewinn

Erwartet werden Verbesserungen bei medizinischen Dokumenten, besonders wenn:

- der vollstaendige Praxis-/Klinikname im Kopfbereich steht,
- bisher nur ein Fragment wie `Tierarztpraxis` erkannt wurde,
- der Lieferant bisher leer blieb,
- der neue Dateiname durch den fehlenden Lieferanten falsch wurde.

Da fast jeder Lieferantenfehler auch einen Dateinamensfolgefehler erzeugt, sollte eine Verbesserung in diesem Cluster automatisch auch den neuen Dateinamen verbessern.

## Pruefung

Durchgefuehrt:

- `python -m py_compile _service\ecodms_scan_service.py`
- zusaetzliche AST-Syntaxpruefung ohne Bytecode-Artefakt

Nicht durchgefuehrt:

- Kein 128er Regressionstest, damit keine Massentestdaten veraendert werden.
- Keine Referenzdaten geaendert.
- Keine WebUI geaendert.
- Keine Git-Befehle ausgefuehrt.

## Bewusst nicht geaendert

- Keine WebUI-Dateien.
- Keine Massentestdaten.
- Keine Referenzdaten.
- Keine OCR-Umstellung.
- Keine Aliaslisten.
- Keine Behoerdenlogik.
- Keine Bankenlogik.
- Keine Einzelfall-Kaskade fuer einzelne Namen.
