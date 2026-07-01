# Alpha Build 15 Qualitaetsanalyse

Version: WebUI 4.0.0-alpha Build 15 (Test-Freeze)

Quelle: C:\ScanSnap_Roh-Scan-ecoDMS\_massentest\ergebnisse\massentest_ergebnisse.json

Analyseziel: Objektive Auswertung der 128 Testdokumente vor Planung von Build 16.

## Gesamtuebersicht

Gesamtanzahl Dokumente: 128

## Verteilung nach Status

- Fachlich validiert: 55
- Abweichung: 68
- Nachzubearbeiten: 5
- Sonderfall: 0
- Offen: 0
- Technisch bestanden - noch fachlich zu pruefen: 0

Hinweis: Die Statusauswertung verwendet das aktuelle Alpha-Statusmodell mit technischer Abweichung vor fachlicher Nacharbeit. soll_neuer_dateiname wird als Soll/Ist-Feld mitbewertet.

## Feldstatistik

| Feld | Bewertbar | Treffer | Abweichungen | Trefferquote |
|---|---:|---:|---:|---:|
| Neuer Dateiname | 128 | 79 | 49 | 61.7% |
| Lieferant | 124 | 97 | 27 | 78.2% |
| GESAMTBETRAG | 64 | 40 | 24 | 62.5% |
| Dokumenttyp | 128 | 104 | 24 | 81.2% |
| RECHNR | 59 | 40 | 19 | 67.8% |
| KUNDENNR | 34 | 18 | 16 | 52.9% |
| VERSICHERUNGSNR | 15 | 9 | 6 | 60% |
| Dokumentdatum | 112 | 108 | 4 | 96.4% |
| AUFTRAGNR | 4 | 3 | 1 | 75% |
| BESTELLNR | 9 | 8 | 1 | 88.9% |
| LIEFERSCHEINNR | 3 | 2 | 1 | 66.7% |

Die CSV-Feldstatistik wurde zusaetzlich erzeugt: `alpha_build15_feldstatistik.csv`.

## Top-Lieferanten mit den meisten Abweichungen

| Lieferant | Dokumente mit Abweichung | Feldabweichungen |
|---|---:|---:|
| Gartenbau und Floristik Franke GmbH & Co. KG | 5 | 27 |
| Bonprix | 7 | 21 |
| Dr. med. dent. Axel Vieler | 2 | 10 |
| Hauptzollamt Dortmund | 5 | 9 |
| Lidl Digital Deutschland GmbH | 1 | 5 |
| Dr. med. Fahim Ayami | 1 | 4 |
| Sparda Bank | 2 | 4 |
| Sparda-Bank West eG | 2 | 4 |
| Hanse Merkur Speziale Krankenversicherung AG | 1 | 4 |
| Ofen.de AA Kaminwelt | 1 | 4 |
| Anwaltskanzlei Messler & Messler | 1 | 4 |
| Böttcher AG | 1 | 4 |

## Top-Dokumenttypen mit den meisten Abweichungen

| Dokumenttyp | Dokumente mit Abweichung | Feldabweichungen |
|---|---:|---:|
| Rechnung | 32 | 100 |
| Kündigung | 6 | 14 |
| Kraftfahrzeugsteuerbescheid | 5 | 9 |
| Kassenbon | 3 | 7 |
| Infoschreiben | 4 | 6 |
| Auskunft aus dem Fahreignungsregister | 2 | 6 |
| Lieferschein | 2 | 6 |
| OP Bericht | 1 | 4 |
| Kontoauszüge | 1 | 3 |
| Mahnung | 1 | 3 |
| Informationsschreiben | 2 | 3 |
| Wichtige Kundenmitteilung | 1 | 3 |

## Haeufigste konkrete Soll/Ist-Abweichungen

| Anzahl | Feld | Soll | Ist |
|---:|---|---|---|
| 5 | KUNDENNR | 14190 |  |
| 5 | KUNDENNR | 321658393 |  |
| 4 | Dokumenttyp | Rechnung | Behörde |
| 4 | Lieferant | Gartenbau und Floristik Franke GmbH & Co. KG | Amtsgericht Bochum |
| 2 | Neuer Dateiname | 2018_04_23_Polizeipräsidium_Bochum.pdf | 2018_04_23_Polizeipräsidium_Bochum_2081001526524.pdf |
| 2 | Dokumenttyp | Auskunft aus dem Fahreignungsregister | Rechnung |
| 2 | Dokumenttyp | Kündigung | Bescheinigung |
| 2 | Lieferant | Dr. med. dent. Axel Vieler |  |
| 1 | Dokumenttyp | Lieferschein | Rechnung |
| 1 | Neuer Dateiname | 2020_06_30_Westdeutsche_Allgemeine_Zeitung.pdf | 2020_06_30_Westdeutsche_Allgemeine_Zeitung_stellung.pdf |
| 1 | Lieferant | U&you Bochum-Weitmar | U you Bochum-Weitmar |
| 1 | LIEFERSCHEINNR | 201649010_1 |  |
| 1 | KUNDENNR | 912417 |  |
| 1 | Neuer Dateiname | 2023_07_23_Gartenbau_und_Floristik_Franke_GmbH_&_Co._KG_PR2_2023_604394.pdf | 2023_07_23_Amtsgericht_Bochum.pdf |
| 1 | Neuer Dateiname | 2025_07_05_Bonprix_8398321250.pdf | 2025_07_05_Bonprix.pdf |
| 1 | Lieferant | Lehner & Kollegen | Telekom |
| 1 | RECHNR | 8398321250 |  |
| 1 | Neuer Dateiname | 2023_08_21_Happy_Size_700072.pdf | 2023_08_21_Unbekannt_700072.pdf |
| 1 | VERSICHERUNGSNR | KFZFK1208936902510012022 | K120.8936.9025 |
| 1 | Neuer Dateiname | 2026_04_15_Dr._med._dent._Axel_Vieler_31940.pdf | 2026_06_28_Unbekannt.pdf |

## Auffaellige Muster

- Die meisten Feldabweichungen konzentrieren sich auf: Neuer Dateiname, Lieferant, GESAMTBETRAG.
- Die stabilsten bewertbaren Felder sind: Dokumentdatum (96.4%), BESTELLNR (88.9%), Dokumenttyp (81.2%).
- Dateinamensabweichungen sind fachlich relevant, weil ein falscher Zielname trotz korrekter Metadaten zu falscher Ablage fuehren kann.
- Leere Sollwerte werden nicht als Fehler gezaehlt, sondern als nicht bewertbar. Dadurch beziehen sich Trefferquoten je Feld nur auf Dokumente mit vorhandenem Sollwert.
- Lieferanten und Dokumenttypen mit wenigen Dokumenten koennen in den Top-Listen stark erscheinen, wenn ein einzelnes Dokument mehrere Feldabweichungen enthaelt.

## Einordnung fuer Build 16

Diese Analyse sollte fuer Build 16 vor allem zur Priorisierung genutzt werden:

- Felder mit niedriger Trefferquote zuerst stabilisieren.
- Lieferanten mit vielen Feldabweichungen gezielt nach Mustern pruefen.
- Wiederkehrende konkrete Soll/Ist-Abweichungen als Regressionstest-Kandidaten vormerken.
- UX-Korrekturen im fachlichen Workflow getrennt von Erkennungslogik bewerten.


