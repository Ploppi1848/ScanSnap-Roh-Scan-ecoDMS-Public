# Sprint 5A - Clusteranalyse Lieferantenfehler

## Kurzfazit

Sprint 4C hat die Pipeline messbar stabilisiert:

- Lieferant: 40 -> 38 exakte Abweichungen
- Neuer Dateiname: 52 -> 50 Abweichungen
- keine Verschlechterungen
- keine neuen auffaelligen Dokumente

Die aktuelle Datei `_massentest/ergebnisse/massentest_ergebnisse.json` enthaelt 38 exakte Lieferantenabweichungen. Normalisiert auf Satzzeichen und einfache Schreibvarianten sind es 37, weil `U&you Bochum-Weitmar` gegen `U you Bochum-Weitmar` fachlich nur ein Alias-/Schreibweisenfall ist.

Die wichtigsten Ursachencluster:

| Cluster | Anzahl | Hauptursache |
|---|---:|---|
| Arzt/Praxis/medizinische Dokumente | 7 | Praxis-/Institutionsnamen fehlen als robuste Kandidaten oder werden nur als Fragment erkannt. |
| Behoerden-/Amtsgericht-Fehlgewichtung | 6 | Amtsgericht/Stadt/Behoerdenkontext gewinnt oder der eigentliche Absender wird nicht stark genug gehalten. |
| Sparda/Banken/Bausparkasse-Alias | 6 | Bankkontext, Aliasfragen und Bausparkasse/Sparda-Verwechslung. |
| Franke/Gartenbau gegen Amtsgericht/OCR-Fragment | 5 | Franke ist im Text vorhanden, aber Amtsgericht oder OCR-Fragment gewinnt. |
| Spaeter schwacher Gewinner / Wrapper-Priorisierung | 4 | Telekom, Santander, megi mobility oder andere spaete Kandidaten verdraengen den fachlichen Absender. |
| OCR-/Logo-/Fragmentproblem | 4 | Soll-Lieferant ist nicht stabil als Text vorhanden oder OCR liefert nur Bruchstuecke. |
| Alias-/Schreibweisenproblem | 3 | Erkennung fachlich nah, aber Soll/Ist-Schreibweise nicht normalisiert. |
| Amazon/Lieferadresse/Plattformkontext | 2 | Plattform-/Lieferadresskontext gewinnt gegen fachlichen Lieferanten. |
| Sonstige Restfaelle | 1 | Richtiger Lieferant im Text, aber ein fachfremder Kandidat gewinnt. |

Wichtigster Befund: 37 von 38 Lieferantenabweichungen erzeugen auch eine Abweichung beim neuen Dateinamen. Jede Verbesserung bei Lieferant wirkt daher fast immer direkt auf den Dateinamen.

## Datengrundlage

Gelesene Quellen:

- `_massentest/ergebnisse/massentest_ergebnisse.json`
- `_massentest/ergebnisse/massentest_sollwerte.json`
- `_debug_text/*_text.txt`
- `_config/lieferanten_konfiguration.txt`
- `_release_4_0/sprint4a_lieferantenerkennung.md`
- `_release_4_0/sprint4b_lieferanten_kandidatenanalyse.md`
- `_release_4_0/sprint4c_lieferantenentscheidung_stabilisieren.md`

Es wurden keine Programmdateien, WebUI-Dateien, Referenzdaten oder Massentestdaten geaendert.

## Feldwirkung innerhalb der Lieferantenfehler

| Feld | Abweichungen innerhalb der 38 Lieferantenfaelle |
|---|---:|
| Lieferant | 37 normalisiert / 38 exakt |
| Neuer Dateiname | 37 |
| Dokumenttyp | 20 |
| RECHNR | 11 |
| Gesamtbetrag | 9 |
| Kundennummer | 7 |
| Dokumentdatum | 3 |
| Versicherungsnummer | 2 |
| Aktenzeichen | 1 |

Typische falsche Gewinner:

| Ist-Lieferant | Anzahl |
|---|---:|
| leer | 11 |
| Amtsgericht Bochum | 6 |
| Sparda-Bank West eG | 4 |
| LVM | 2 |
| Amazon | 2 |
| Telekom | 2 |
| weitere Einzelgewinner | 11 |

## Einzeldokumente mit Lieferantenabweichung

| Dokument | Soll | Ist | Typ | Weitere betroffene Felder | OCR | Konfig |
|---|---|---|---|---|---|---|
| 29032026__Alarmanlagen Videoueberwachnung _Tresore Wertschutzschr.pdf | Wiedemann Sicherheitstechnik | Handwerksbetrieb Kend | Angebot | dokumenttyp, neuer_dateiname | ja | nein |
| Amtsgericht Anderes 26.02.2020.pdf | Grundbuchbezirk Altenbochum | LVM | Versicherung | dokumenttyp, neuer_dateiname, kundennr, gesamtbetrag | ja | nein |
| Bausparkasse Schwaebisch Hall AG Information 01.12.2019.pdf | Bausparkasse Schwaebisch Hall AG | Sparda-Bank West eG | Darlehensvertrag | dokumenttyp, neuer_dateiname, versicherungsnr | ja | ja |
| Bausparkasse Schwaebisch Hall AG Information 05.02.2020.pdf | Bausparkasse Schwaebisch Hall AG | Sparda-Bank West eG | Informationsschreiben | neuer_dateiname | ja | ja |
| Bongardstr. 31 Information 20.02.2025.pdf | Anwaltskanzlei Messler & Messler | megi mobility GmbH | Versicherung | dokumenttyp, neuer_dateiname, gesamtbetrag | ja | nein |
| BRN94DDF8539961_000810.pdf | Sparda Bank | leer | Gutschrift | dokumenttyp, neuer_dateiname | ja | ja |
| D ul Rechnung 04.03.2024.pdf | Dipl. Psych. Tobis Vielhaber | leer | Rechnung | neuer_dateiname | teilweise | nein |
| DKV Deutsche Krankenversicherung AG Information 16.02.2026.pdf | DKB Deutsche Kreditbank | Deutsche Kreditbank AG | Versicherung | dokumenttyp, neuer_dateiname | teilweise | teilweise |
| Dr. med. Fahim Ayami Rechnung 06.05.2026.pdf | Dr. med. Fahim Ayami | leer | Rechnung | neuer_dateiname, rechnr, gesamtbetrag | nein | ja |
| Dr. med.dent.Axel Rechnung 15.04.2026.pdf | Dr. med. dent. Axel Vieler | leer | Rechnung | dokumentdatum, neuer_dateiname, rechnr, gesamtbetrag | ja | nein |
| Dr. med.dent.Axel Rechnung 26.08.2025.pdf | Dr. med. dent. Axel Vieler | leer | Rechnung | dokumentdatum, neuer_dateiname, rechnr, gesamtbetrag | ja | nein |
| Flascheral Norge sch Kassenzettel.pdf | Fleischrei Norbert Hirsch | Waage | Kassenbon | neuer_dateiname, gesamtbetrag | nein | nein |
| Franke GmbH _ Co. KG Anderes 04.02.2024.pdf | Gartenbau und Floristik Franke GmbH & Co. KG | Amtsgericht Bochum | Behoerde | dokumenttyp, neuer_dateiname, rechnr, kundennr | ja | teilweise |
| Franke GmbH _ Co. KG Anderes 23.07.2023.pdf | Gartenbau und Floristik Franke GmbH & Co. KG | Amtsgericht Bochum | Behoerde | dokumenttyp, neuer_dateiname, rechnr, kundennr | ja | teilweise |
| Franke GmbH _ Co. KG Kassenzettel 15.02.2026.pdf | Gartenbau und Floristik Franke GmbH & Co. KG | Amtsgericht Bochum | Behoerde | dokumenttyp, neuer_dateiname, rechnr, kundennr | ja | teilweise |
| Franke GmbH _ Co. KG Rechnung 16.02.2025.pdf | Gartenbau und Floristik Franke GmbH & Co. KG | Amtsgericht Bochum | Behoerde | dokumenttyp, neuer_dateiname, rechnr, kundennr | ja | teilweise |
| Franke GmbH _ Co. KG Rechnung 20.07.2025.pdf | Gartenbau und Floristik Franke GmbH & Co. KG | Ft"anke GmbH | Rechnung | neuer_dateiname, kundennr | ja | teilweise |
| Gebers Kassenzettel 18.07.2025.pdf | Traumschloss die grosse Bettenmarke | leer | Kassenbon | neuer_dateiname, rechnr | ja | nein |
| HanseMerkur Speziale Krankenversicherung AG Information 30.03.2021.pdf | Hanse Merkur Speziale Krankenversicherung AG | Speziale Krankenversicherung AG | Versicherung | dokumenttyp, neuer_dateiname, versicherungsnr | teilweise | ja |
| HAPPYsize Anderes 21.08.2023.pdf | Happy Size | leer | Rechnung | dokumenttyp, neuer_dateiname | ja | nein |
| Heinz-Georg Hepp Rechnung 23.08.2025.pdf | Bonprix | Amazon | Rechnung | neuer_dateiname, rechnr, gesamtbetrag | ja | ja |
| Hepp, Simone Information 14.09.2017.pdf | St. Josef-Hospital Bochum | Klinik Tecklenburger Land | Medizinischer Fragebogen | dokumenttyp, dokumentdatum, neuer_dateiname | teilweise | nein |
| Kraftfahrt-Bundesamt Information 14.09.2016.pdf | Kraftfahrt-Bundesamt | leer | Rechnung | dokumenttyp, neuer_dateiname | ja | nein |
| Kraftfahrt-Bundesamt Information 21.09.2016.pdf | Kraftfahrt-Busndesamt | leer | Rechnung | dokumenttyp, neuer_dateiname | nein | nein |
| Lehner und Kollegen Rechnung 03.07.2025.pdf | Lehner und Kollegen | Telekom | Rechnung | neuer_dateiname | ja | nein |
| Lehner und Kollegen Rechnung 12.02.2025.pdf | Lehner & Kollegen | Telekom | Rechnung | neuer_dateiname, rechnr, aktenzeichen | ja | nein |
| Lieferadresse Anderes 23.03.2025.pdf | Genius | Amazon | Bestellbestaetigung | neuer_dateiname | ja | ja |
| Lowenstein Medical Anderes 07.11.2025.pdf | Loewenstein Medical | leer | Rechnung | dokumenttyp, neuer_dateiname | ja | nein |
| Name Vertrag 03.06.2019.pdf | Allgemeiner deutscher Fahrradclub | Stadt Bochum | Kaufvertrag | neuer_dateiname, gesamtbetrag | teilweise | ja |
| Rathaus Bochum Anderes 04.01.2019.pdf | Stadt Bochum | Amtsgericht Bochum | Hundesteuerbescheid | neuer_dateiname, rechnr | ja | ja |
| Santander Consumer Bank AG Rechnung 15.07.2022.pdf | Ofen.de AA Kaminwelt | Santander Consumer Bank AG | Finanzierung | dokumenttyp, neuer_dateiname, gesamtbetrag | teilweise | ja |
| Simone Hepp Rechnung 20.06.2023.pdf | Tierarztpraxis Judith Schoenenstein | Tierarztpraxis | Rechnung | neuer_dateiname | ja | nein |
| Sparda-Bank West eG Anderes 30.01.2020.pdf | Sparda Bank | Sparda-Bank West eG | Darlehensvertrag | dokumenttyp, neuer_dateiname | ja | ja |
| Sparda-Bank West eG Information 11.12.2019.pdf | Sparda Bank | LVM | Versicherung | dokumenttyp, neuer_dateiname, kundennr | ja | ja |
| Sparda-Bank West eG Kontoauszug 03.09.2019.pdf | Sparda Bank | Sparda-Bank West eG | Kontoauszug | neuer_dateiname | ja | ja |
| Stadtwerke Bochum Netz GmbH Information 05.01.2024.pdf | Maingau Energie | Amtsgericht Bochum | Zaehlerstandserfassung | neuer_dateiname | ja | ja |
| Tibisco Haustierservice Information 26.02.2024.pdf | Tibisco Haustierservice | leer | Medizinischer Fragebogen | dokumenttyp, neuer_dateiname | teilweise | nein |
| U_you Bochum-Weitmar _ Rechnung 07.07.25.pdf | U&you Bochum-Weitmar | U you Bochum-Weitmar | Rechnung | keine normalisierte Feldabweichung | ja | nein |

## Detailanalyse je Cluster

### 1. Arzt/Praxis/medizinische Dokumente

Betroffene Dokumente: 7

- Dr. med. Fahim Ayami
- Dr. med. dent. Axel Vieler, 2 Dokumente
- St. Josef-Hospital Bochum
- Loewenstein Medical
- Tierarztpraxis Judith Schoenenstein
- Tibisco Haustierservice

Typische falsche Gewinner:

- leer
- Klinik Tecklenburger Land
- Tierarztpraxis als Fragment

OCR-/Konfigurationslage:

- Soll-Lieferant im OCR-Text: haeufig ja oder teilweise.
- Konfiguration: meist nein; Fahim Ayami ist konfiguriert, aber OCR/Dateiname liefert offenbar nicht den benoetigten stabilen Treffer.

Gemeinsame Ursache:

Praxis-, Arzt- und Kliniknamen erscheinen oft als Briefkopfzeile, E-Mail/Webhinweis oder Teilfragment. Die aktuelle Logik erkennt generische medizinische Hinweise, aber nicht konsequent den vollstaendigen fachlichen Absender.

Vermuteter technischer Hebel:

- medizinische Briefkopf-Kandidaten staerker als Kandidatenquelle behandeln
- Praxis-/Klinik-/Medical-Namensmuster generisch erkennen
- Fragmentwerte wie `Tierarztpraxis` nicht als Endwert akzeptieren, wenn ein laengerer Name im Kopfbereich steht

Risiko:

Mittel. Medizinische Dokumente koennen Patient, Einrichtung, Versicherung und behandelnde Praxis enthalten. Empfaenger-/Patientenzeilen duerfen nicht gewinnen.

Erwarteter Nutzen:

Bis zu 5-7 Lieferanten- und Dateinamensverbesserungen, wenn generisch geloest.

### 2. Behoerden-/Amtsgericht-Fehlgewichtung

Betroffene Dokumente: 6

- Grundbuchbezirk Altenbochum
- Kraftfahrt-Bundesamt, 2 Dokumente
- Allgemeiner deutscher Fahrradclub
- Stadt Bochum
- Maingau Energie / Stadtwerke Bochum Netz

Typische falsche Gewinner:

- Amtsgericht Bochum
- LVM
- Stadt Bochum
- leer

OCR-/Konfigurationslage:

- Soll-Lieferant im OCR-Text: meistens ja oder teilweise.
- Konfiguration: gemischt; Stadt Bochum, Maingau und ADFC sind vorhanden, KBA/Grundbuchbezirk nicht stabil.

Gemeinsame Ursache:

Behoerden- und Amtsgerichtssignale sind starke Dokumenttyp-/Kontextsignale. In einigen Dokumenten werden sie aber als Lieferant uebergewichtet oder ein anderer fachlicher Absender wird nicht ausreichend gehalten.

Vermuteter technischer Hebel:

- Amtsgericht nur als Lieferant setzen, wenn Amtsgericht wirklich Absender/Kopfbereich ist
- `Grundbuchbezirk`, `Kraftfahrt-Bundesamt`, `Maingau` und `Stadt Bochum` als Kopfbereichs-/Dateiname-Kandidaten sauber trennen
- Lieferant und Dokumenttyp entkoppeln: Behoerden-Dokumenttyp darf nicht automatisch Amtsgericht-Lieferant bedeuten

Risiko:

Mittel. Amtsgericht ist in einigen Dokumenten echter Lieferant. Eine zu harte Blockade wuerde echte Gerichts-/Grundbuchfaelle verschlechtern.

Erwarteter Nutzen:

Etwa 4-6 Lieferantenverbesserungen plus Dateiname.

### 3. Sparda/Banken/Bausparkasse-Alias

Betroffene Dokumente: 6

- Bausparkasse Schwaebisch Hall AG, 2 Dokumente
- Sparda Bank leer/Gutschrift
- Sparda-Bank West eG, 3 Dokumente

Typische falsche Gewinner:

- Sparda-Bank West eG
- LVM
- leer

OCR-/Konfigurationslage:

- Soll-Lieferant im OCR-Text: ja.
- Konfiguration: ja.

Gemeinsame Ursache:

Hier liegt weniger ein Kandidatenmangel vor, sondern eine Prioritaets- und Aliasfrage. `Sparda Bank` und `Sparda-Bank West eG` sind fachlich nahe, werden aber exakt als Abweichung bewertet. Bei Bausparkasse-Dokumenten gewinnt Sparda weiterhin in falschem Bankkontext.

Vermuteter technischer Hebel:

- Aliasnormalisierung fuer Sparda-Kurz-/Langform
- Bausparkasse-Kopfbereich gegen Sparda-Fuss-/Bankkontext staerken
- LVM darf nicht aus Versicherungs-/Beteiligtenkontext gegen Sparda-Kopfbereich gewinnen

Risiko:

Niedrig bis mittel. Aliasnormalisierung ist risikoarm; Bankkontext-Umgewichtung ist riskanter, weil echte Bankdokumente erhalten bleiben muessen.

Erwarteter Nutzen:

3-6 Lieferanten-/Dateinamensverbesserungen, je nachdem ob Aliasfaelle als fachlich bestanden gelten duerfen.

### 4. Franke/Gartenbau gegen Amtsgericht/OCR-Fragment

Betroffene Dokumente: 5

- Franke/Gartenbau, 5 Dokumente

Typische falsche Gewinner:

- Amtsgericht Bochum, 4 Dokumente
- `Ft"anke GmbH`, 1 Dokument

OCR-/Konfigurationslage:

- Soll-Lieferant im OCR-Text: ja.
- Konfiguration: teilweise; offenbar reichen Suchwoerter/Aliase nicht stabil.

Gemeinsame Ursache:

Der richtige Gartenbau-/Franke-Absender ist vorhanden, aber in vier Faellen gewinnt Amtsgericht Bochum. Ein Fall zeigt ein OCR-Fragment als Ist-Lieferant. Das ist ein sauberer Cluster mit hohem Wiederholungsnutzen.

Vermuteter technischer Hebel:

- Franke/Gartenbau-Kopfbereich oder Dateiname gegen Amtsgericht-Folgekontext schuetzen
- OCR-Fragment `Ft"anke GmbH` gegen vollstaendigen Namen normalisieren
- Amtsgericht nur setzen, wenn Amtsgericht im Kopfbereich oder Dateiname wirklich dominiert

Risiko:

Mittel. Zu breite Franke-Regeln waeren unerwuenscht; besser ist eine generische Regel: vollstaendiger Firmenname/Kopfbereich gewinnt gegen spaeten Amtsgericht-Kontext.

Erwarteter Nutzen:

Bis zu 5 Lieferanten- und Dateinamensverbesserungen.

### 5. Spaeter schwacher Gewinner / Wrapper-Priorisierung

Betroffene Dokumente: 4

- Anwaltskanzlei Messler & Messler vs megi mobility GmbH
- Lehner und Kollegen vs Telekom, 2 Dokumente
- Ofen.de AA Kaminwelt vs Santander Consumer Bank AG

Typische falsche Gewinner:

- Telekom
- Santander Consumer Bank AG
- megi mobility GmbH

OCR-/Konfigurationslage:

- Soll-Lieferant im OCR-Text: ja oder teilweise.
- Konfiguration: meist nein; Santander ist konfiguriert, aber als Finanzierungs-/Bankkontext wahrscheinlich falscher fachlicher Lieferant.

Gemeinsame Ursache:

Spaete Wrapper oder Kontexttreffer greifen fachlich zu stark. Telekom, Santander und aehnliche Kandidaten koennen echte Lieferanten sein, sind hier aber Zahlungs-, Finanzierungs-, Text- oder Kontextbestandteile.

Vermuteter technischer Hebel:

- `SUPPLIER_DECISION`-Logs aus Sprint 4C auswerten
- schwache spaete Gewinner nur erlauben, wenn sie im Kopfbereich oder Dateiname klar belegt sind
- Finanzierungs-/Zahlungspartner nicht automatisch als Lieferant setzen

Risiko:

Mittel. Telekom/Santander koennen in anderen Dokumenten echte Lieferanten sein.

Erwarteter Nutzen:

2-4 Verbesserungen.

### 6. OCR-/Logo-/Fragmentproblem

Betroffene Dokumente: 4

- Dipl. Psych. Tobis Vielhaber
- Fleischrei Norbert Hirsch
- Traumschloss die grosse Bettenmarke
- Happy Size

Typische falsche Gewinner:

- leer
- Waage

OCR-/Konfigurationslage:

- Soll-Lieferant im OCR-Text: nein, teilweise oder nur schwach.
- Konfiguration: nein, ausser indirekte Einzelfaelle.

Gemeinsame Ursache:

Der Lieferant steht vermutlich als Logo, stark verrauschtes OCR, Kassenbonkopf oder nur als Domain/Fragment im Text. Allgemeine Priorisierung kann hier wenig ausrichten, solange kein brauchbarer Kandidat entsteht.

Vermuteter technischer Hebel:

- vorsichtige Dateiname-Kandidatenquelle fuer leere Lieferanten
- Konfigurationspflege fuer wiederkehrende Kassenbon-/Logo-Lieferanten
- spaeter eventuell OCR-/Layoutverbesserung, aber nicht als schneller Build-5B-Hebel

Risiko:

Mittel bis hoch, wenn Dateiname blind als Lieferant verwendet wird.

Erwarteter Nutzen:

1-3 Verbesserungen kurzfristig; mehr erst mit OCR/Layout- oder Konfigurationsarbeit.

### 7. Alias-/Schreibweisenproblem

Betroffene Dokumente: 3

- DKB/Deutsche Kreditbank bei DKV-Dokumentname
- Hanse Merkur Speziale Krankenversicherung AG vs Speziale Krankenversicherung AG
- U&you Bochum-Weitmar vs U you Bochum-Weitmar

Typische falsche Gewinner:

- Deutsche Kreditbank AG
- Speziale Krankenversicherung AG
- U you Bochum-Weitmar

OCR-/Konfigurationslage:

- Soll-Lieferant im OCR-Text: teilweise bis ja.
- Konfiguration: teilweise bis ja.

Gemeinsame Ursache:

Diese Faelle wirken weniger wie klassische Erkennungsfehler und mehr wie Sollwert-/Alias-/Normalisierungsprobleme. U&you ist normalisiert kein echter Fehler. DKV/DKB wirkt sogar wie ein moeglicher Sollwert- oder Dateiname-Konflikt.

Vermuteter technischer Hebel:

- Aliasnormalisierung im Vergleich oder in Lieferanten-Normalisierung
- Sollwertpruefung fuer DKV/DKB und Schreibfehler
- HanseMerkur-Langform gegen Teilfragment normalisieren

Risiko:

Niedrig, wenn Aliaslisten eng und nachvollziehbar bleiben.

Erwarteter Nutzen:

1-3 bereinigte Lieferantenabweichungen ohne Risiko fuer OCR/Extraktion.

### 8. Amazon/Lieferadresse/Plattformkontext

Betroffene Dokumente: 2

- Bonprix vs Amazon
- Genius vs Amazon

Typische falsche Gewinner:

- Amazon

OCR-/Konfigurationslage:

- Soll-Lieferant im OCR-Text: ja.
- Konfiguration: ja.

Gemeinsame Ursache:

Amazon-/Lieferadress-/Plattformkontext gewinnt gegen den eigentlichen fachlichen Lieferanten. Sprint 4C hat allgemeine spaete Amazon-Gewinner begrenzt; die verbleibenden Faelle brauchen vermutlich eine genauere Trennung zwischen Plattform, Lieferadresse und verkauftem/fachlichem Anbieter.

Vermuteter technischer Hebel:

- Empfaenger-/Lieferadressbloecke weiter abwerten
- `Verkauft von`/Plattformtext nur dann Lieferant, wenn kein besserer fachlicher Kopfbereichs- oder Konfigurationstreffer existiert
- Bonprix/Genius-Konfig-Treffer gegen Amazon-Kontext schuetzen

Risiko:

Mittel. Amazon kann echter Lieferant sein; Plattformregeln duerfen Amazon-Rechnungen nicht verschlechtern.

Erwarteter Nutzen:

2 Verbesserungen, plus potenziell bessere Stabilitaet fuer Plattformdokumente.

### 9. Sonstige Restfaelle

Betroffene Dokumente: 1

- Wiedemann Sicherheitstechnik vs Handwerksbetrieb Kend

Typische falsche Gewinner:

- Handwerksbetrieb Kend

OCR-/Konfigurationslage:

- Soll-Lieferant im OCR-Text: ja.
- Konfiguration: nein.

Gemeinsame Ursache:

Der richtige Lieferant steht im Text, aber ein Angebots-/Handwerkskontext zieht auf Kend. Das ist fachlich aehnlich zur spaeten Wrapper-Priorisierung, aber als einzelner Fall nicht gross genug fuer eine eigene Code-Kaskade.

Vermuteter technischer Hebel:

- allgemeiner Schutz: vollstaendiger Firmenname aus Kopf-/Signaturbereich gegen anderen Handwerkskandidaten
- Konfigurationspflege fuer Wiedemann

Risiko:

Niedrig bei Konfigurationspflege, mittel bei generischer Handwerksregel.

Erwarteter Nutzen:

1 Verbesserung.

## Top-Hebel

| Prioritaet | Massnahme | Betroffene Dokumente | Erwarteter Qualitaetsgewinn | Risiko | Empfohlener Sprint |
|---:|---|---:|---|---|---|
| 1 | Medizinische/Praxis-Kopfbereichserkennung generisch verbessern | 7 | hoch fuer Lieferant und Dateiname | mittel | Sprint 5B |
| 2 | Behoerden-/Amtsgericht-Priorisierung entkoppeln | 6 | hoch, besonders Amtsgericht-Fehlgewinner | mittel | Sprint 5B |
| 3 | Sparda/Bausparkasse/Bank-Aliasnormalisierung und Kontextschutz | 6 | mittel bis hoch | niedrig bis mittel | Sprint 5B |
| 4 | Franke/Gartenbau gegen Amtsgericht/OCR-Fragment schuetzen | 5 | hoch innerhalb eines stabilen Clusters | mittel | Sprint 5C |
| 5 | Spaete Gewinner Telekom/Santander/megi per SUPPLIER_DECISION-Trace auswerten | 4 | mittel | niedrig bis mittel | Sprint 5C |
| 6 | Alias-/Schreibweisenbereinigung im Soll/Ist-Vergleich | 3 | niedrig bis mittel, aber risikoarm | niedrig | Sprint 5B oder 5C |
| 7 | Amazon/Lieferadresse/Plattformkontext gezielt trennen | 2 | niedrig bis mittel | mittel | Sprint 5C |
| 8 | OCR-/Logo-/Fragmentfaelle ueber Konfiguration/Dateiname vorsichtig behandeln | 4 | begrenzt kurzfristig | mittel bis hoch | Beta/LTS oder separater Mini-Sprint |

## Empfehlung fuer Sprint 5B

Sprint 5B sollte nicht breit optimieren, sondern drei risikoarme bis mittlere Hebel kombinieren:

1. Alias-/Normalisierungsschicht fuer offensichtliche Lieferantenvarianten:
   - `U&you` vs `U you`
   - `Sparda Bank` vs `Sparda-Bank West eG`
   - `Hanse Merkur` vs `HanseMerkur`
   - moegliche Sollwertpruefung fuer DKV/DKB separat dokumentieren

2. Medizinische/Praxis-Kandidaten generisch verbessern:
   - laengere Praxis-/Klinik-/Medical-Namen im Kopfbereich bevorzugen
   - generische Fragmente wie `Tierarztpraxis` nur als schwache Kandidaten
   - Patient-/Empfaengerzeilen weiter abwerten

3. Behoerden-/Amtsgericht-Kontext entkoppeln:
   - Dokumenttyp `Behoerde` darf nicht automatisch `Amtsgericht Bochum` als Lieferant bedeuten
   - Amtsgericht nur bei starkem Kopfbereich/Dateiname
   - Stadt/KBA/Maingau/Grundbuchbezirk als eigene Lieferantenkandidaten halten

Franke/Gartenbau ist ebenfalls attraktiv, sollte aber als Sprint 5C folgen, wenn 5B die generische Kopfbereichs- und Behoerdenlogik stabilisiert hat.

## Risiken

- Medizinische Dokumente enthalten haeufig Patient, Praxis, Klinik, Versicherung und Labor. Eine zu breite Kopfbereichsregel kann falsche Empfaenger uebernehmen.
- Behoerden- und Amtsgerichtsdokumente brauchen saubere Trennung zwischen Dokumenttyp, Institution, Register-/Grundbuchtext und echtem Absender.
- Bankdokumente sind heikel: Sparda, Santander und LVM koennen echte Lieferanten oder nur Zahlungs-/Finanzierungs-/Beteiligtenkontext sein.
- Dateiname als Kandidatenquelle bleibt riskant, weil er alte Fehler fortschreiben kann.
- Aliasnormalisierung darf echte juristische Unterschiede nicht verdecken, sollte aber offensichtliche Schreibvarianten entschärfen.

## Schlussfolgerung

Die verbleibenden Lieferantenfehler sind nicht gleichmaessig verteilt. Die groessten 3-5 Ursachen sind:

1. medizinische/Praxis-Absender
2. Behoerden-/Amtsgericht-Fehlgewichtung
3. Sparda/Bausparkasse/Bank-Alias und Bankkontext
4. Franke/Gartenbau gegen Amtsgericht/OCR-Fragment
5. spaete schwache Gewinner wie Telekom, Santander, Amazon und LVM

Der naechste Sprint sollte daher nicht allgemeine Scoringwerte drehen, sondern gezielt an Kopfbereich, Aliasnormalisierung und Lieferant/Dokumenttyp-Entkopplung arbeiten.
