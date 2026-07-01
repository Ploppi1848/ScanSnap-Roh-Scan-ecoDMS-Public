# Alpha Build 16A Ursachenanalyse

Version: WebUI 4.0.0-alpha Build 16A Vorbereitung

Basis:

- `alpha_build15_qualitaetsanalyse.md`
- `alpha_build15_feldstatistik.csv`
- `_massentest/ergebnisse/massentest_ergebnisse.json`

Ziel: Ursachen-Gruppierung der Build-15-Qualitaetsprobleme vor gezielten Build-16B-Korrekturen.

## 1. Top-Problemfelder

| Feld | Bewertbar | Abweichungen | Trefferquote |
|---|---:|---:|---:|
| Neuer Dateiname | 128 | 49 | 61.7% |
| Lieferant | 124 | 27 | 78.2% |
| GESAMTBETRAG | 64 | 24 | 62.5% |
| RECHNR | 59 | 19 | 67.8% |
| KUNDENNR | 34 | 16 | 52.9% |

Einordnung:

- Der neue Dateiname ist das groesste sichtbare Problemfeld, weil mehrere Metadatenfehler dort kumulieren.
- Lieferant ist ein Primaerfeld: ein falscher Lieferant zieht haeufig Dateiname, Dokumenttyp und Nummernfelder mit.
- GESAMTBETRAG ist stark dokumenttypabhaengig und bei Kontoauszuegen, Schreiben und Sammelbelegen fachlich nicht immer sinnvoll.
- RECHNR und KUNDENNR leiden vor allem unter fehlender Extraktion, Verwechslung mit anderen Nummern und Kontextproblemen.

## 2. Gruppierung der Fehlerursachen

### Echte Erkennungsfehler

- Lieferant wird falsch erkannt, z. B. Gartenbau und Floristik Franke als Amtsgericht Bochum.
- Dokumenttyp wird falsch klassifiziert, z. B. Rechnung statt Auskunft aus dem Fahreignungsregister.
- Nummernfelder bleiben leer, obwohl Sollwerte vorhanden sind.

### Folgefehler durch falschen Lieferanten

- Falscher Lieferant erzeugt falschen Ziel-Dateinamen.
- Falscher Lieferant beeinflusst Dokumenttyp- und Feldheuristiken.
- Besonders sichtbar bei Gartenbau und Floristik Franke, Dr. med. dent. Axel Vieler und einzelnen Shop-/Versicherungsfaellen.

### Folgefehler durch falschen Dokumenttyp

- Dokumenttyp "Rechnung" wird zu breit verwendet.
- Behorden- und Auskunftsdokumente werden teilweise als Rechnung interpretiert.
- Falscher Dokumenttyp fuehrt dazu, dass Betrag, Rechnungsnummer oder Kundennummer erwartet werden, obwohl sie fachlich nicht passen.

### Format-/Normalisierungsfehler

- Lieferantenvarianten wie `U&you` gegen `U you`.
- Versicherungsnummern mit Punkten, Schraegstrichen oder Teilgruppen.
- Dateinamen mit Zusatznummern, Aktenzeichen oder freien Textfragmenten.
- Betragserkennung mit OCR- oder Kontextartefakten.

### Dateinamenslogik / Zusatzfelder im Dateinamen

- Zusatzfelder wie `stellung`, Aktenzeichen, Rechnungsnummern oder Kundennummern landen im Dateinamen.
- Teilweise fehlt die erwartete Nummer im Dateinamen, teilweise wird zu viel aufgenommen.
- `soll_neuer_dateiname` muss deshalb als fachlich relevantes Feld weiter mitbewertet werden.

### OCR-/Textqualitaet

- Schlechte OCR erzeugt leere Lieferanten, leere Nummern oder falsch segmentierte Betragswerte.
- Mehrseitige oder zusammen gescannte Dokumente fuehren zu gemischten Kontexten.
- Handschriftliche oder sehr dicht gesetzte Dokumente koennen Folgefehler in mehreren Feldern ausloesen.

### Konfigurations-/Lernlisten-Themen

- Lieferantenvarianten sollten gezielt normalisiert werden.
- Dokumenttyp-Regeln fuer Behorden, Versicherungen, Zeitung/Medien und Shops sollten enger werden.
- Nummernfelder brauchen feldspezifische Prioritaeten, damit Rechnungsnummer, Kundennummer, Aktenzeichen und Versicherungsnummer nicht vermischt werden.

## 3. Top-20 konkrete Korrekturkandidaten

Die folgenden Kandidaten sind als Muster zu verstehen, nicht als reine Einzelfallliste.

| Prioritaet | Muster | Betroffene Felder | Ursache | Ansatz fuer Build 16B |
|---:|---|---|---|---|
| 1 | Neuer Dateiname enthaelt Zusatztext oder falsche Nummer | Neuer Dateiname | Dateinamenslogik / Zusatzfelder | Dateiname aus validierten Sollfeldern strenger bilden |
| 2 | Lieferant Gartenbau/Franke wird Amtsgericht | Lieferant, Dokumenttyp, Dateiname | falscher Lieferant | Lieferantenregel/Lernliste fuer Gartenbau Franke |
| 3 | Bonprix-Dateien ohne oder mit falscher Nummer | Neuer Dateiname, RECHNR, KUNDENNR | Nummernextraktion | Bonprix-spezifische Nummernprioritaet pruefen |
| 4 | Kundennummer 14190 fehlt wiederholt | KUNDENNR | Nummernfeld nicht erkannt | Wiederkehrende Kundennummernkontexte auswerten |
| 5 | Kundennummer 321658393 fehlt wiederholt | KUNDENNR | Nummernfeld nicht erkannt | KUNDENNR-Regel fuer wiederkehrenden Kontext |
| 6 | Rechnung gegen Behoerde | Dokumenttyp | zu breite Rechnungsklassifikation | Behoerdenindikatoren vor Rechnungsheuristik pruefen |
| 7 | Auskunft Fahreignungsregister als Rechnung | Dokumenttyp | falsche Dokumenttypregel | Auskunft-/Register-Begriffe hoeher gewichten |
| 8 | Kuendigung als Bescheinigung | Dokumenttyp | Dokumenttyp-Abgrenzung | Kuendigungsbegriffe und Vertragskontext staerken |
| 9 | Dr. med. dent. Axel Vieler nicht erkannt | Lieferant, Dateiname | OCR/Lieferantenregel | Lieferantenalias und Praxisnamen normalisieren |
| 10 | Gesamtbetrag fehlt oder falscher Betrag | GESAMTBETRAG | Kontext/OCR | Betrag nur in passenden Dokumenttypen erzwingen |
| 11 | Hauptzollamt mit Betrag/Versicherungsnummer-Konflikten | GESAMTBETRAG, VERSICHERUNGSNR | Feldverwechslung | Steuer-/Bescheidnummern getrennt behandeln |
| 12 | Versicherungsnummer gekuerzt oder anders formatiert | VERSICHERUNGSNR | Normalisierung | Punkt-/Slash-/Gruppenvergleich verbessern |
| 13 | Lieferant `U&you` gegen `U you` | Lieferant | Normalisierung | Sonderzeichen-Normalisierung fuer Lieferanten |
| 14 | Lehner & Kollegen gegen Telekom | Lieferant | falscher Kontext | Kopf-/Absenderbereich staerker priorisieren |
| 15 | Lidl Digital Einzelabweichungen | Lieferant, Nummern, Dateiname | Shop-Belegmuster | Shop-spezifische Referenzmuster pruefen |
| 16 | Böttcher AG Einzelabweichungen | Lieferant, Nummern | Shop-Belegmuster | Rechnungs-/Kundennummernkontext pruefen |
| 17 | Lieferschein als Rechnung | Dokumenttyp, LIEFERSCHEINNR | Typ/Feld-Kontext | Lieferscheinbegriffe vor Rechnungsbegriffen |
| 18 | Medien/FUNKE Dateiname mit Zusatz `stellung` | Neuer Dateiname | Dateinamenszusatz | Freitextfragmente im Dateinamen begrenzen |
| 19 | Sammel- oder Mehrfachscan | mehrere Felder | Dokumentstruktur | Als Nacharbeit/Sonderfall statt Erkennungsfehler behandeln |
| 20 | Leere Sollwerte vs. echte Fehler | alle optionalen Felder | Bewertung/Referenz | Optionalitaet je Dokumenttyp klarer definieren |

## 4. Vorschlag fuer Build 16B

### Gezielt zu pruefende Codebereiche

- Lieferantenerkennung und Lieferanten-Normalisierung.
- Dokumenttyp-Klassifikation, besonders Behoerden, Auskunft, Kuendigung, Lieferschein und Rechnung.
- Dateinamensbildung aus Soll-/Ist-Feldern.
- Nummernextraktion fuer RECHNR, KUNDENNR, VERSICHERUNGSNR und AKTENZEICHEN.
- Betragslogik je Dokumenttyp.
- Vergleichsnormalisierung fuer Sonderzeichen, Punkt-/Slash-Gruppen und leere optionale Felder.

### Voraussichtlich groesster Effekt

- Lieferanten-Normalisierung verbessern, weil sie viele Folgefehler im Dateinamen reduziert.
- Dateinamenslogik gegen Zusatztexte stabilisieren.
- Dokumenttyp-Regeln fuer `Rechnung` enger fassen.
- Nummernfelder feldspezifisch priorisieren, damit KUNDENNR, RECHNR und VERSICHERUNGSNR nicht vermischt werden.
- GESAMTBETRAG nur dort streng bewerten, wo er fachlich erwartet wird.

### Änderungen, die vermieden werden sollten

- Keine grossflaechige Neuentwicklung der Erkennungslogik in Build 16B.
- Keine neuen Statusmodelle.
- Keine neue Aufgabenlogik.
- Keine automatischen Massenkorrekturen an Referenzdaten.
- Keine Beta-/LTS-Themen wie Arbeitscenter, Tabs oder PDF-Bearbeitung.

## Fazit

Build 16B sollte als gezielter Korrekturbuild geplant werden. Die beste Wirkung ist zu erwarten, wenn zuerst Lieferanten, Dateiname, Dokumenttyp und Nummernfelder stabilisiert werden. GESAMTBETRAG sollte dokumenttypabhaengig behandelt werden, damit fachlich irrelevante Betragsfelder nicht zu kuenstlichen Abweichungen fuehren.
