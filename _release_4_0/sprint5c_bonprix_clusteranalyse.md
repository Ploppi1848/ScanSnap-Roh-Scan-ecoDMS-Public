# Sprint 5C - Bonprix Clusteranalyse

## Kurzfazit

Aktueller Massenteststand nach Sprint 5B.1:

- Bonprix-Dokumente insgesamt: 9
- Davon fehlerhaft: 8
- Abweichungen im Bonprix-Cluster: 25
- Ein Bonprix-Dokument ist bereits korrekt: `Lieferadresse Rechnung 22.09.2025.pdf`

Das Cluster zerfaellt in zwei technische Untergruppen:

1. Klassische Bonprix-PDF-Rechnungen: 7 Dokumente, je 3 Abweichungen.
   - Lieferant ist korrekt `Bonprix`.
   - Gesamtbetrag ist korrekt.
   - RECHNR und KUNDENNR stehen im OCR-Text, bleiben aber leer.
   - Neuer Dateiname ist nur Folgefehler, weil die Rechnungsnummer fehlt.

2. Bonprix-App-/Screenshot-Rechnung: 1 Dokument.
   - `Heinz-Georg Hepp Rechnung 23.08.2025.pdf`
   - Bonprix steht im OCR-Text.
   - Rechnungnummer steht im OCR-Text.
   - Lieferant kippt trotzdem auf `Amazon`.
   - Betrag wird als Gesamtsumme `95,86` statt offener Betrag `68,87` erkannt.
   - RECHNR wird falsch als `26` erkannt.

Die wichtigste Ursache ist nicht die Bonprix-Lieferantenerkennung im Allgemeinen. Bei 7 von 8 fehlerhaften Bonprix-Dokumenten ist der Lieferant bereits korrekt. Der groesste Hebel fuer Sprint 5D ist die RECHNR-/KUNDENNR-Erkennung aus Label-Wert-Bloecken.

## Tabelle aller Bonprix-Dokumente

| Dokument | Soll Lieferant | Ist Lieferant | Soll/Ist RECHNR | Soll/Ist KUNDENNR | Soll/Ist Betrag | Soll/Ist neuer Dateiname | Abw. |
|---|---|---|---|---|---|---|---:|
| bonpdx Handelagm. mbH Rechnung 23.08.2025.pdf | Bonprix | Bonprix | 8401588910 / leer | 321658393 / leer | 95,86 / 95,86 | 2025_08_23_Bonprix_8401588910.pdf / 2025_08_23_Bonprix.pdf | 3 |
| bonprix Handeisges Rechnung 23.08.2025.pdf | Bonprix | Bonprix | 8401588910 / leer | 321658393 / leer | 95,86 / 95,86 | 2025_08_23_Bonprix_8401588910.pdf / 2025_08_23_Bonprix.pdf | 3 |
| bonprix Handelsges. mbH Rechnung 02.07.2025.pdf | Bonprix | Bonprix | 8398099852 / leer | 321658393 / leer | 140,91 / 140,91 | 2025_07_02_Bonprix_8398099852.pdf / 2025_07_02_Bonprix.pdf | 3 |
| bonprix Handelsges. mbH Rechnung 05.07.2025 (2) .pdf | Bonprix | Bonprix | 8398321250 / leer | 321658393 / leer | 19,99 / 19,99 | 2025_07_05_Bonprix_8398321250.pdf / 2025_07_05_Bonprix.pdf | 3 |
| bonprix Handelsges. mbH Rechnung 05.07.2025.pdf | Bonprix | Bonprix | 8398320687 / leer | 321658393 / leer | 19,99 / 19,99 | 2025_07_05_Bonprix_8398320687.pdf / 2025_07_05_Bonprix.pdf | 3 |
| bonprix Handelsges. mbH Rechnung 30.11.2024.pdf | Bonprix | Bonprix | 8383995199 / leer | 52407820 / leer | 193,73 / 193,73 | 2024_11_30_Bonprix_8383995199.pdf / 2024_11_30_Bonprix.pdf | 3 |
| bonprix Handelsgesellschaft mbH Rechnung 13.05.2025.pdf | Bonprix | Bonprix | 8393971997 / leer | 321658393 / leer | 103,96 / 103,96 | 2025_05_13_Bonprix_8393971997.pdf / 2025_05_13_Bonprix.pdf | 3 |
| Heinz-Georg Hepp Rechnung 23.08.2025.pdf | Bonprix | Amazon | 8401588910 / 26 | leer / leer | 68,87 / 95,86 | 2025_08_23_Bonprix_8401588910.pdf / 2025_08_23_Amazon_26.pdf | 4 |
| Lieferadresse Rechnung 22.09.2025.pdf | Bonprix | Bonprix | 8403318814 / 8403318814 | 321658393 / 321658393 | 190,90 / 190,90 | 2025_09_22_Bonprix_8403318814.pdf / 2025_09_22_Bonprix_8403318814.pdf | 0 |

## OCR-/Feldbefund

### Klassische Bonprix-PDF-Rechnungen

Betroffene Dokumente:

- `bonpdx Handelagm. mbH Rechnung 23.08.2025.pdf`
- `bonprix Handeisges Rechnung 23.08.2025.pdf`
- `bonprix Handelsges. mbH Rechnung 02.07.2025.pdf`
- `bonprix Handelsges. mbH Rechnung 05.07.2025 (2) .pdf`
- `bonprix Handelsges. mbH Rechnung 05.07.2025.pdf`
- `bonprix Handelsges. mbH Rechnung 30.11.2024.pdf`
- `bonprix Handelsgesellschaft mbH Rechnung 13.05.2025.pdf`

OCR-Befund:

- `bonprix` steht im OCR-Text, teils mit OCR-Varianten wie `bonpdx`, `bonpnx`, `bonprlx`.
- `Kunden-Nr.` steht im OCR-Text.
- `Rechnungs-Nr.` steht im OCR-Text.
- Die Werte stehen sichtbar in der Naehe der Labels, aber nicht immer in derselben Zeile.
- Hauefiges Layout:

```text
Kunden-Nr.:
321658393
Rechnungs-Nr.:
8398321250
Rechnungs-Datum:
05.07.2025
```

Oder als zweispaltiger Block:

```text
Ihre Rechnung
Kunden-Nr.:
Rechnungs-Nr.:
Rechnungs-Datum:
321658393
8398099852
02.07.2025
```

Feldbefund:

- Lieferant: korrekt.
- Dokumenttyp: korrekt.
- Dokumentdatum: korrekt.
- Gesamtbetrag: korrekt.
- RECHNR: leer.
- KUNDENNR: leer.
- Neuer Dateiname: Folgefehler, weil RECHNR fehlt.

Interpretation:

Die Nummern gehen nicht verloren, weil sie im OCR fehlen. Sie gehen verloren, weil die Nummernextraktion die Bonprix-Label/Wert-Bloecke nicht robust aufloest.

### Bonprix-App-/Screenshot-Rechnung

Dokument:

- `Heinz-Georg Hepp Rechnung 23.08.2025.pdf`

OCR-Ausschnitt:

```text
bonprix.
Rechnung vom 23.08.2025
Rechnungsdetails
Offener Betrag:
68,87 EUR
Gesamtsumme:
95,86 EUR
Rechnungs-N r.:
8401588910
Bestell-Nr.:
621654913
Buchungen zu dieser Rechnung
Retourengutschrift
26,99 EUR
Rechnungsadresse
Heinz-Georg Hepp
...
bonprix.de
```

Feldbefund:

- Bonprix steht im OCR-Text.
- Rechnungsnummer `8401588910` steht im OCR-Text.
- Kundennummer steht in diesem App-/Screenshot-Text nicht sichtbar im OCR.
- Lieferant wird trotzdem `Amazon`.
- RECHNR wird `26`, vermutlich aus dem Retourengutschrift-Betrag `26,99`.
- Gesamtbetrag wird `95,86`, obwohl Sollwert `68,87` ist.

Interpretation:

Das ist kein klassisches Bonprix-PDF-Labelproblem. Es ist ein App-/Screenshot-Layout mit anderen Prioritaeten:

- Bonprix-Lieferant muss gegen Amazon-Fallback geschuetzt werden.
- `Rechnungsdetails` darf nicht automatisch Amazon bedeuten.
- `Offener Betrag` ist fuer dieses Dokument fachlich relevanter als `Gesamtsumme`.
- `Retourengutschrift 26,99` darf nicht als RECHNR dienen.

### Bereits korrektes Bonprix-Dokument

Dokument:

- `Lieferadresse Rechnung 22.09.2025.pdf`

Befund:

- Lieferant, RECHNR, KUNDENNR, Betrag und neuer Dateiname sind korrekt.
- Im Code existiert bereits eine gezielte Restfalllogik fuer dieses Dokument bzw. dieses Datum.
- Diese Logik beweist, dass die benoetigten Werte aus dem OCR grundsaetzlich extrahierbar sind.

## Gemeinsame Ursachen

### 1. Bonprix wird meist erkannt, aber Nummern fehlen

Bei 7 von 8 fehlerhaften Bonprix-Dokumenten ist `Bonprix` bereits der Ist-Lieferant. Lieferantenschutz allein wuerde diese 21 Abweichungen nicht beheben.

### 2. RECHNR/KUNDENNR stehen im OCR, aber im Blocklayout

Die klassischen Rechnungen zeigen wiederkehrend:

- Label und Wert in getrennten Zeilen.
- Mehrere Labels direkt untereinander, danach mehrere Werte.
- OCR verschiebt Spalten in eine lineare Reihenfolge.
- Adresszeilen stehen zwischen Labelblock und Wertblock.

Das ist ein typisches Tabellen-/Blocklayoutproblem.

### 3. Dateiname ist Folgefehler

Der Soll-Dateiname nutzt die Rechnungsnummer:

```text
YYYY_MM_DD_Bonprix_<RECHNR>.pdf
```

Wenn RECHNR leer ist, entsteht:

```text
YYYY_MM_DD_Bonprix.pdf
```

Der neue Dateiname ist daher bei den klassischen Bonprix-Dokumenten kein eigenes Primaerproblem.

### 4. Der App-/Screenshot-Fall ist ein eigener Untertyp

`Heinz-Georg Hepp Rechnung 23.08.2025.pdf` hat:

- andere Textstruktur
- keine sichtbare KUNDENNR
- `Offener Betrag` statt klassischem Rechnungsbetrag
- `Rechnungsdetails`, was alte Amazon-Fallbacks triggern kann

Dieser Fall sollte nicht mit derselben Regel wie klassische Bonprix-PDF-Rechnungen erzwungen werden.

### 5. Sollwerte wirken ueberwiegend konsistent

Die Sollwerte der klassischen Bonprix-Rechnungen sind konsistent:

- Lieferant immer `Bonprix`
- Dokumenttyp `Rechnung`
- RECHNR 10-stellig
- KUNDENNR 8- oder 9-stellig
- Betrag stimmt bereits

Kein primaerer Hinweis auf Sollwert-/Aliasproblem.

## Top-Hebel

| Prioritaet | Hebel | Betroffene Dokumente | Erwarteter Gewinn | Risiko |
|---:|---|---:|---|---|
| 1 | Generische Label/Wert-Blockerkennung fuer RECHNR/KUNDENNR | 7 | ca. 14 Feldtreffer + 7 Dateinamen | mittel |
| 2 | Bonprix-Dateiname nach erfolgreicher RECHNR-Erkennung automatisch korrekt | 7 | 7 Dateinamen als Folge | niedrig |
| 3 | Bonprix-App-/Screenshot gegen Amazon-Fallback schuetzen | 1 | Lieferant + Dateiname | mittel |
| 4 | App-/Screenshot-Betragsprioritaet: `Offener Betrag` vor `Gesamtsumme` | 1 | Gesamtbetrag | mittel |
| 5 | Retourengutschrift-/Betragswerte nicht als RECHNR verwenden | 1 | RECHNR | niedrig bis mittel |
| 6 | Bonprix-spezifische Hartwerte wie bei 22.09.2025 ausbauen | 7 | kurzfristig hoch | hoch als Wartungsrisiko |

## Empfehlung fuer Sprint 5D

Sprint 5D sollte zuerst das Blocklayout loesen, nicht den Lieferanten.

Empfohlene Reihenfolge:

1. Generische Label/Wert-Blockerkennung fuer Nummernfelder bauen:
   - Labels sammeln: `Kunden-Nr.`, `Rechnungs-Nr.`, `Rechnungs-Datum`
   - Werte in den naechsten Zeilen oder im parallelen Wertblock zuordnen
   - nur in passendem Rechnungskontext anwenden
   - nicht Bonprix-hart, aber mit Bonprix als erste Testgruppe

2. Bonprix-Kontext als Schutz fuer die Zuordnung verwenden:
   - `bonprix` oder OCR-Varianten im Kopfbereich
   - `Ihre Rechnung`
   - `Kunden-Nr.`
   - `Rechnungs-Nr.`

3. Nach erfolgreicher RECHNR-Erkennung Dateiname automatisch verbessern:
   - kein eigener Dateiname-Fix noetig
   - Dateiname profitiert von validierter RECHNR

4. App-/Screenshot-Fall separat, aber generisch behandeln:
   - `Rechnungsdetails` allein darf kein Amazon-Signal sein
   - wenn `bonprix` und `bonprix.de` vorhanden sind, Amazon nicht setzen
   - `Offener Betrag` als moeglicher fachlicher Zahlbetrag priorisieren
   - `Retourengutschrift`-Kontext fuer RECHNR sperren

Nicht empfohlen:

- Nur weitere Bonprix-Einzelfallwerte wie die vorhandene 22.09.2025-Logik nachtragen.
- Blind den Dateinamen reparieren, ohne RECHNR/KUNDENNR sauber zu erkennen.
- Amazon pauschal blockieren, da Amazon echte Rechnungen bleiben koennen.

## Risiken

- Eine generische Label/Wert-Blocklogik kann bei anderen Rechnungen falsche Werte zuordnen, wenn mehrere Labels und Werte dicht beieinander stehen.
- `Kunden-Nr.` und `Rechnungs-Nr.` koennen in OCR vertauscht oder durch Adresszeilen unterbrochen sein.
- Bonprix-App-/Screenshot und klassische Bonprix-PDF-Rechnung sind unterschiedliche Layouttypen und sollten nicht mit einer einzigen harten Regel vermischt werden.
- Der Verwendungszweck enthaelt oft Kundennummer + Rechnungsnummer zusammengesetzt. Das kann hilfreich sein, darf aber nicht unkontrolliert als eine einzelne Nummer uebernommen werden.

## Erwartung nach Sprint 5D

Wenn Sprint 5D die Label/Wert-Blockerkennung sauber loest, sind realistisch:

- 7 klassische Bonprix-Dokumente: RECHNR korrigiert.
- 7 klassische Bonprix-Dokumente: KUNDENNR korrigiert.
- 7 klassische Bonprix-Dokumente: neuer Dateiname korrigiert.

Das waeren bis zu 21 der 25 Bonprix-Abweichungen.

Die restlichen 4 Abweichungen liegen im App-/Screenshot-Fall und sollten danach separat gemessen werden.
