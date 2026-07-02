# Sprint 5D - Label/Wert-Blockerkennung fuer Nummernfelder

## Ausgangslage aus Sprint 5C

Der Bonprix-Cluster bestand aus 9 Bonprix-nahen Dokumenten, davon 8 mit Abweichungen.
Bei 7 klassischen Bonprix-Rechnungen waren Lieferant, Dokumentdatum und Gesamtbetrag bereits korrekt.

Hauptproblem:

- `RECHNR` leer
- `KUNDENNR` leer
- dadurch neuer Dateiname ohne Rechnungsnummer

Die Nummern standen im OCR-Text, aber haeufig als Label/Wert-Block:

```text
Kunden-Nr.:
Rechnungs-Nr.:
Rechnungs-Datum:
321658393
8398099852
02.07.2025
```

## Neue generische Blocklogik

Ergaenzt wurde im Scan-Service ein isolierter Block:

- `extract_label_value_blocks(text)`
- `_apply_label_wert_blockerkennung_660(...)`

Die Logik erkennt:

- Label und Wert in derselben Zeile
- Label in einer Zeile, Wert in der Folgezeile
- mehrere Labels untereinander mit mehreren Werten darunter

Sie wird am Ende der bisherigen Pipeline angewendet, damit vorhandene Klassifikation und Stabilisierungen vorher greifen.

## Erkannte Labelvarianten

Fuer `RECHNR`:

- Rechnungs-Nr.
- Rechnungs-Nr:
- Rechnungsnummer
- Rechnung Nr.
- Rechnungs-N r.
- Rechn.-Nr.

Fuer `KUNDENNR`:

- Kunden-Nr.
- Kunden-Nr:
- Kundennummer
- Kunden Nr.
- Kd.-Nr.

`RECHDATUM` wird nur zur Positionszuordnung im Block erkannt, aber in Sprint 5D nicht als neues Feld gesetzt.

## Plausibilitaetsregeln

`RECHNR`:

- bevorzugt 8 bis 12 Ziffern
- keine Datumswerte
- keine Betraege
- keine Retouren-/Gutschriftwerte
- keine Einzelwerte wie `26` aus `26,99 EUR`

`KUNDENNR`:

- bevorzugt 6 bis 10 Ziffern
- keine Datumswerte
- keine Betraege
- keine PLZ

Vorhandene plausible Werte werden nicht ueberschrieben.

## Begrenzung und Risiken

Die Anwendung ist bewusst eng begrenzt:

- nur bei Rechnungskontext
- nur wenn passende Labels im Text vorkommen
- nur fuer `RECHNR` und `KUNDENNR`
- keine Bonprix-Hartwerte
- keine Dateinamen-Hartkorrekturen
- keine OCR-Umstellung

Risiko:

Eine generische Blocklogik kann bei Rechnungen mit sehr dichten Tabellen falsche Positionszuordnungen erzeugen. Deshalb werden nur plausible Nummernlaengen uebernommen und bestehende plausible Werte geschuetzt.

## Testhinweise

Isoliert gegen die 7 klassischen Bonprix-Debugtexte geprueft:

- `bonpdx Handelagm. mbH Rechnung 23.08.2025.pdf`
- `bonprix Handeisges Rechnung 23.08.2025.pdf`
- `bonprix Handelsges. mbH Rechnung 02.07.2025.pdf`
- `bonprix Handelsges. mbH Rechnung 05.07.2025 (2) .pdf`
- `bonprix Handelsges. mbH Rechnung 05.07.2025.pdf`
- `bonprix Handelsges. mbH Rechnung 30.11.2024.pdf`
- `bonprix Handelsgesellschaft mbH Rechnung 13.05.2025.pdf`

Ergebnis der isolierten Pruefung:

- `RECHNR` korrekt erkannt
- `KUNDENNR` korrekt erkannt

Syntaxpruefung:

```text
python -m py_compile _service\ecodms_scan_service.py
```

erfolgreich.

## Erwarteter Qualitaetsgewinn

Erwartet wird:

- 7 klassische Bonprix-Rechnungen mit erkannter `RECHNR`
- 7 klassische Bonprix-Rechnungen mit erkannter `KUNDENNR`
- 7 automatisch verbesserte neue Dateinamen als Folge der erkannten Rechnungsnummer

Der App-/Screenshot-Fall `Heinz-Georg Hepp Rechnung 23.08.2025.pdf` wurde bewusst nicht zum Hauptziel von Sprint 5D gemacht, weil dort zusaetzlich Amazon-Fallback, offener Betrag und Retourengutschrift-Kontext beteiligt sind.
