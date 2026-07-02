# Sprint 5E-A - Analyse Neuer Dateiname

## Ziel

Analyse der Dokumente, bei denen das Feld `Neuer Dateiname` im aktuellen Massenteststand abweicht.

Dies ist ein reiner Analyse-Sprint.

Nicht geaendert:

- keine Codeaenderungen
- keine WebUI-Aenderungen
- keine Refactoring-Arbeiten
- keine Referenzdaten
- keine Sollwerte
- keine automatische Uebernahme von Referenzen

## Datenbasis

Ausgewertet:

- `_massentest/ergebnisse/massentest_ergebnisse.json`
- `_massentest/ergebnisse/snapshots/quality_snapshot_20260702_180942_128991_4_0_0_alpha_build_16.json`
- `_release_4_0/CHANGELOG.md`
- bestehende Analyseberichte aus Sprint 5C und Sprint 5D

Snapshot-Stand:

- Dokumente gesamt: 128
- `Neuer Dateiname`: 86 ok, 42 abweichend
- `Lieferant`: 35 Abweichungen
- `Dokumenttyp`: 34 Abweichungen
- `RECHNR`: 12 Abweichungen
- `KUNDENNR`: 8 Abweichungen
- `GESAMTBETRAG`: 20 Abweichungen

Hinweis:

Direkter Soll/Ist-Vergleich des Dateinamens findet 44 unterschiedliche Werte. Fachlich aktiv als `Neuer Dateiname`-Abweichung markiert sind 42 Dokumente. Diese 42 Dokumente bilden die Grundlage dieser Analyse.

## Kurzfazit

Die Dateinamenfehler sind ueberwiegend Folgefehler.

Wichtigste Hauptursache:

1. Falscher oder instabiler Lieferant/Absender.
2. Danach folgen fehlende oder falsch priorisierte Nummernfelder.
3. Einige Dateinamenfehler entstehen durch Datums-Fallback auf das Testdatum.
4. Reine Dateinamenlogik ist nur selten das Primaerproblem.

Sprint 5E-B sollte daher nicht zuerst die Dateinamensbildung selbst umbauen, sondern die Eingangsfelder stabilisieren, aus denen der Dateiname erzeugt wird.

## Betroffene Dokumente

| Nr. | Dokument | Soll-Dateiname | Ist-Dateiname | Hauptursache |
|---:|---|---|---|---|
| 1 | 29032026__Alarmanlagen Videoueberwachnung _Tresore Wertschutzschr.pdf | 2026_07_02_Wiedemann_Sicherheitstechnik_251145.pdf | 2026_07_02_Handwerksbetrieb_Kend_251145.pdf | Lieferant / Dokumenttyp |
| 2 | Allianz Lebensversicherungs-AG Information 22.08.2022.pdf | 2022_08_22_Allianz_Lebensversicherungs-AG_AL-0040705725.pdf | 2022_08_22_Allianz_Lebensversicherungs-AG.pdf | Versicherungsnummer nicht dateinamensfaehig erkannt |
| 3 | Amtsgericht Anderes 26.02.2020.pdf | 2020_02_26_Grundbuchbezirk_Altenbochum.pdf | 2020_02_26_LVM_X704929513529X.pdf | Lieferant / Dokumenttyp / falscher Kontext |
| 4 | Bausparkasse Schwaebisch Hall AG Information 01.12.2019.pdf | 2019_12_01_Bausparkasse_Schwaebisch_Hall_AG.pdf | 2019_12_01_Sparda-Bank_West_eG.pdf | Lieferant / Dokumenttyp |
| 5 | Bausparkasse Schwaebisch Hall AG Information 05.02.2020.pdf | 2020_02_05_Bausparkasse_Schwaebisch_Hall_AG.pdf | 2020_02_05_Sparda-Bank_West_eG.pdf | Lieferant |
| 6 | Bongardstr. 31 Information 20.02.2025.pdf | 2025_02_20_Anwaltskanzlei_Messler_&_Messler.pdf | 2025_02_20_megi_mobility_GmbH.pdf | Lieferant / Dokumenttyp |
| 7 | BRN94DDF8539961_000810.pdf | 2026_07_02_Sparda_Bank.pdf | 2026_07_02_Unbekannt.pdf | Lieferant / Dokumenttyp |
| 8 | D ul Rechnung 04.03.2024.pdf | 2024_03_04_Dipl._Psych._Tobis_Vielhaber_2024-03-00364.pdf | 2024_03_04_Unbekannt_2024-03-00364.pdf | Lieferant |
| 9 | Deutsche Post AG Vertrag 10.10.2022.pdf | 2022_10_10_Deutsche_Post_AG_4242019764628012.pdf | 2022_10_10_Deutsche_Post_AG.pdf | Aktenzeichen / Nummernfeld fehlt im Dateinamen |
| 10 | DKV Deutsche Krankenversicherung AG Information 16.02.2026.pdf | 2026_02_16_DKB_Deutsche_Kreditbank.pdf | 2026_02_16_Deutsche_Kreditbank_AG.pdf | Lieferant / Aliasnormalisierung |
| 11 | Dr. med. Fahim Ayami Rechnung 06.05.2026.pdf | 2026_05_06_Dr._med._Fahim_Ayami_14511.pdf | 2026_05_06_Unbekannt_DE31.pdf | Lieferant / RECHNR |
| 12 | Dr. med.dent.Axel Rechnung 15.04.2026.pdf | 2026_04_15_Dr._med._dent._Axel_Vieler_31940.pdf | 2026_07_02_Dr._med._dent._Axel_Vieler.pdf | Dokumentdatum / RECHNR |
| 13 | Dr. med.dent.Axel Rechnung 26.08.2025.pdf | 2025_08_26_Dr._med._dent._Axel_Vieler_31154.pdf | 2026_07_02_Dr._med._dent._Axel_Vieler.pdf | Dokumentdatum / RECHNR |
| 14 | Flascheral Norge sch Kassenzettel.pdf | 2026_07_02_Fleischrei_Norbert_Hirsch.pdf | 2026_07_02_Waage.pdf | Lieferant / OCR-Fragment |
| 15 | Franke GmbH _ Co. KG Anderes 04.02.2024.pdf | 2024_02_04_Gartenbau_und_Floristik_Franke_GmbH_&_Co._KG_PR2-2024_605377.pdf | 2024_02_04_Amtsgericht_Bochum_PR1-2024.pdf | Lieferant / RECHNR / KUNDENNR |
| 16 | Franke GmbH _ Co. KG Anderes 23.07.2023.pdf | 2023_07_23_Gartenbau_und_Floristik_Franke_GmbH_&_Co._KG_PR2-2023_604394.pdf | 2023_07_23_Amtsgericht_Bochum_PR2-2023.pdf | Lieferant / RECHNR / KUNDENNR |
| 17 | Franke GmbH _ Co. KG Kassenzettel 15.02.2026.pdf | 2026_02_15_Gartenbau_und_Floristik_Franke_GmbH_&_Co._KG_PR1-2026_607096.pdf | 2026_02_15_Amtsgericht_Bochum_PR1-2026.pdf | Lieferant / RECHNR / KUNDENNR |
| 18 | Franke GmbH _ Co. KG Rechnung 16.02.2025.pdf | 2025_02_16_Gartenbau_und_Floristik_Franke_GmbH_&_Co._KG_PR1-2025_606095.pdf | 2025_02_16_Amtsgericht_Bochum_PR1-2025.pdf | Lieferant / RECHNR / KUNDENNR |
| 19 | Franke GmbH _ Co. KG Rechnung 20.07.2025.pdf | 2025_07_20_Gartenbau_und_Floristik_Franke_GmbH_&_Co._KG_PR2-20251606374.pdf | 2025_07_20_Ft_anke_GmbH_PR2-20251606374.pdf | Lieferant / OCR-Stoerung |
| 20 | Gebers Kassenzettel 18.07.2025.pdf | 2025_07_18_Traumschloss_die_grosse_Bettenmarke_5050.pdf | 2025_07_18_Unbekannt.pdf | Lieferant / RECHNR |
| 21 | Hanse Merkur Information 30.06.2025.pdf | 2025_05_21_HanseMerkur_Speziale_Krankenversicherung_AG_009975903827.pdf | 2026_07_02_HanseMerkur_Speziale_Krankenversicherung_AG.pdf | Dokumentdatum / Versicherungsnummer |
| 22 | HanseMerkur Speziale Krankenversicherung AG Information 30.03.2021.pdf | 2021_03_30_Hanse_Merkur_Speziale_Krankenversicherung_AG_009913958852.pdf | 2021_03_30_Speziale_Krankenversicherung_AG_009913958852SehrgeehrterHerrHepp.pdf | Lieferant / Versicherungsnummer ueberlang |
| 23 | HAPPYsize Anderes 21.08.2023.pdf | 2023_08_21_Happy_Size_700072.pdf | 2023_08_21_Unbekannt_700072.pdf | Lieferant / Dokumenttyp |
| 24 | Haufe Service Center GmbH Rechnung 14.05.25.pdf | 2025_05_14_Lexware_0665799255.pdf | 2025_05_14_Lexware_97460212.pdf | RECHNR / KUNDENNR Prioritaet |
| 25 | Heinz-Georg Hepp Rechnung 23.08.2025.pdf | 2025_08_23_Bonprix_8401588910.pdf | 2025_08_23_Amazon_8401588910.pdf | Lieferant / Amazon-Fallback |
| 26 | Hepp, Simone Information 14.09.2017.pdf | 2017_09_14_St._Josef-Hospital_Bochum.pdf | 2026_07_02_Klinik_Tecklenburger_Land.pdf | Lieferant / Dokumenttyp / Datum |
| 27 | Kraftfahrt-Bundesamt Information 14.09.2016.pdf | 2016_09_14_Kraftfahrt-Bundesamt.pdf | 2016_09_14_Unbekannt.pdf | Lieferant / Dokumenttyp |
| 28 | Kraftfahrt-Bundesamt Information 21.09.2016.pdf | 2016_09_21_Kraftfahrt-Busndesamt.pdf | 2016_09_21_Unbekannt.pdf | Lieferant / Dokumenttyp |
| 29 | Lehner und Kollegen Rechnung 03.07.2025.pdf | 2025_07_03_Lehner_und_Kollegen.pdf | 2025_07_03_Telekom.pdf | Lieferant / Telekom-Fallback |
| 30 | Lehner und Kollegen Rechnung 12.02.2025.pdf | 2025_02_12_Lehner_&_Kollegen_2500099.pdf | 2025_02_12_Telekom.pdf | Lieferant / RECHNR / Aktenzeichen |
| 31 | Lieferadresse Anderes 23.03.2025.pdf | 2025_03_23_Genius_6873154.pdf | 2025_03_23_Amazon_6873154.pdf | Lieferant / Amazon-Fallback |
| 32 | Lowenstein Medical Anderes 07.11.2025.pdf | 2026_07_02_Lowenstein_Medical.pdf | 2026_07_02_Lowenstein_Medical_2896345.pdf | KUNDENNR faelschlich im Dateinamen |
| 33 | Name Vertrag 03.06.2019.pdf | 2019_06_03_Allgemeiner_deutscher_Fahrradclub.pdf | 2019_06_03_Stadt_Bochum.pdf | Lieferant / falscher Kontext |
| 34 | Rathaus Bochum Anderes 04.01.2019.pdf | 2019_01_04_Stadt_Bochum_9000619877147.pdf | 2019_01_04_Amtsgericht_Bochum_900061987714704.pdf | Lieferant / RECHNR Laenge |
| 35 | Santander Consumer Bank AG Rechnung 15.07.2022.pdf | 2022_07_15_Ofen.de_AA_Kaminwelt_394733.pdf | 2022_07_15_Santander_Consumer_Bank_AG_394733.pdf | Lieferant / Dokumenttyp |
| 36 | Simone Hepp Rechnung 20.06.2023.pdf | 2023_06_20_Tierarztpraxis_Judith_Schoenenstein_20231370.pdf | 2023_06_20_info@tierarzt-schoenenstei_n.de_20231370.pdf | Lieferant / E-Mail als Fragment |
| 37 | Sparda-Bank West eG Anderes 30.01.2020.pdf | 2008_12_02_Sparda_Bank.pdf | 2008_12_02_Sparda-Bank_West_eG.pdf | Lieferant / Aliasnormalisierung |
| 38 | Sparda-Bank West eG Information 11.12.2019.pdf | 2019_12_11_Sparda_Bank_912417.pdf | 2019_12_11_LVM.pdf | Lieferant / Dokumenttyp / KUNDENNR |
| 39 | Sparda-Bank West eG Kontoauszug 03.09.2019.pdf | 2019_10_02_Sparda_Bank.pdf | 2019_10_02_Sparda-Bank_West_eG.pdf | Lieferant / Aliasnormalisierung |
| 40 | Stadtwerke Bochum Netz GmbH Information 05.01.2024.pdf | 2024_01_05_Maingau_Energie.pdf | 2024_01_05_Amtsgericht_Bochum.pdf | Lieferant / falscher Amtsgericht-Fallback |
| 41 | Tibisco Haustierservice Information 26.02.2024.pdf | 2026_07_02_Tibisco_Haustierservice.pdf | 2026_07_02_Unbekannt.pdf | Lieferant / Dokumenttyp |
| 42 | U_you Bochum-Weitmar _ Rechnung 07.07.25.pdf | 2025_07_07_U_&_you_Bochum-Weitmar_16236.pdf | 2025_07_07_U_you_Bochum-Weitmar_16236.pdf | Lieferant / Schreibweise |

## Ursachencluster

### 1. Lieferant / Absenderentscheidung

Betroffen: ca. 35 der 42 Dateinamenabweichungen.

Typische Muster:

- schwacher spaeter Gewinner ersetzt den eigentlichen Absender
- `Amtsgericht Bochum`, `Telekom`, `Amazon`, `LVM`, `Sparda-Bank West eG` gewinnen in fremdem Kontext
- Empfaenger-, E-Mail-, OCR-Fragment- oder Kontaktzeilen werden als Lieferant verwendet
- Lieferantenalias ist fachlich gleich, aber Dateiname weicht ab

Beispiele:

- Franke wird zu Amtsgericht Bochum
- Lehner wird zu Telekom
- Bonprix-App/Screenshot wird zu Amazon
- Sparda/Bausparkasse-Kontext kippt zu Sparda-Bank West eG
- Tierarzt wird zu E-Mail-Adresse

Bewertung:

Das ist der groesste Hebel. Die Dateinamensbildung selbst arbeitet hier meist konsequent mit dem falschen Lieferantenwert.

### 2. Nummernfelder / Prioritaet

Betroffen: mindestens 11 `RECHNR`-Faelle, 7 `KUNDENNR`-Faelle, 4 Versicherungsnummern-Faelle und 2 Aktenzeichen-Faelle innerhalb der 42 Dokumente.

Typische Muster:

- Nummer fehlt, obwohl sie fuer den Soll-Dateinamen benoetigt wird
- falsche Nummer gewinnt gegen die fachlich relevante Nummer
- ueberlange OCR-Anhaenge werden Teil der Versicherungsnummer
- Kundennummer wird aufgenommen, obwohl sie fuer diesen Dokumenttyp nicht in den Dateinamen gehoert

Beispiele:

- Lowenstein Medical: Kundennummer `2896345` verschlechtert den Dateinamen
- Haufe/Lexware: falsche Nummernprioritaet
- Allianz/HanseMerkur: Versicherungsnummer fehlt oder ist ueberlang
- Deutsche Post: Aktenzeichen fehlt im Dateinamen

### 3. Dokumentdatum / Testdatum-Fallback

Betroffen: 3 bis 4 Dokumente als sichtbare Hauptursache.

Typische Muster:

- echtes Dokumentdatum wird nicht erkannt
- Dateiname faellt auf aktuelles Testdatum `2026_07_02` zurueck

Beispiele:

- beide Axel-Vieler-Rechnungen
- HanseMerkur Information 30.06.2025
- St. Josef-Hospital / Klinik-Kontext

### 4. Dokumenttyp als Folgeverstaerker

Betroffen: haeufig gemeinsam mit Lieferant.

Typische Muster:

- falscher Dokumenttyp entscheidet, ob eine Nummer im Dateinamen auftaucht
- Nicht-Rechnung wird als Rechnung oder Versicherung erkannt
- Rechnung/Information/Vertrag/Kontoauszug werden vermischt

Der Dokumenttyp ist selten alleinige Ursache, verstaerkt aber Lieferanten- und Nummernfehler.

### 5. OCR-Stoerung / Fragmente

Betroffen: kleinere, aber sichtbare Gruppe.

Typische Muster:

- fragmentierter Lieferant
- E-Mail-Adresse als Lieferant
- OCR-Reste wie `Waage` oder `Ft_anke`

Beispiele:

- Fleischerei Norbert Hirsch wird zu `Waage`
- Franke wird zu `Ft_anke GmbH`
- Tierarztpraxis wird zu `info@...`

## Prioritaeten fuer Sprint 5E-B

| Prioritaet | Massnahme | Betroffene Dokumente | Potenzial | Risiko |
|---:|---|---:|---|---|
| 1 | Lieferantenentscheidung gegen schwache spaete Gewinner stabilisieren | bis ca. 35 | sehr hoch | mittel |
| 2 | Lieferantenalias fuer Dateinamen kanonisieren | ca. 5 bis 8 | mittel | niedrig |
| 3 | Nummernverwendung im Dateinamen je Dokumenttyp pruefen | ca. 10 bis 15 | hoch | mittel |
| 4 | Versicherungsnummern/Aktenzeichen vor OCR-Ueberlauf schuetzen | ca. 4 bis 6 | mittel | mittel |
| 5 | Datumserkennung vor Testdatum-Fallback verbessern | ca. 3 bis 4 | mittel | niedrig bis mittel |
| 6 | OCR-Fragmente als Lieferant blockieren | ca. 4 bis 6 | mittel | niedrig |

## Empfohlene Reihenfolge Sprint 5E-B

1. Keine Dateinamen-Hartkorrekturen bauen.
2. Zuerst Lieferantenwert stabilisieren, besonders gegen `Amtsgericht`, `Telekom`, `Amazon`, `LVM`, `Sparda` in schwachem Kontext.
3. Danach eine kleine Kanonisierung fuer Dateinamen-relevante Lieferantenschreibweisen pruefen.
4. Danach Nummernfelder fuer Dateinamen nach Dokumenttyp validieren.
5. Lowenstein Medical separat pruefen: Kundennummer darf dort offenbar nicht automatisch im Dateinamen landen.
6. Erst nach diesen Schritten Dateinamensbildung selbst anfassen, falls dann noch echte Dateinamenlogik-Fehler uebrig bleiben.

## Risiken

- Lieferantenstabilisierung kann echte Bank-/Amazon-/Telekom-Dokumente verschlechtern, wenn Kontextregeln zu hart werden.
- Aliasnormalisierung kann fachlich gewollte Schreibweisen veraendern.
- Nummernregeln koennen korrekte Rechnungsnummern blockieren, wenn sie zu dokumenttypspezifisch werden.
- Datumskorrekturen koennen bei Dokumenten ohne echtes Datum falsche Werte erzwingen.

## Ergebnis

Die 42 Dateinamenabweichungen sind fachlich gruppiert.

Die beste Sprint-5E-B-Strategie ist:

- keine direkte Dateinamenreparatur
- zuerst bessere Eingangsfelder
- danach gezielte Dateinamen-Normalisierung
