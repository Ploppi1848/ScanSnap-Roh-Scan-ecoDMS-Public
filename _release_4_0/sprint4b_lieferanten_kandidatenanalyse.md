# Sprint 4B - Lieferanten-Kandidatenpipeline Analyse

## Kurzfazit

Sprint 4A war stabil, aber ohne messbaren Effekt. Die aktuelle Analyse bestaetigt die Vermutung: In vielen Fehlerfaellen wird der richtige Lieferant zwar im OCR-Text gefunden, gewinnt aber nicht gegen einen spaeteren oder staerker bewerteten Kandidaten.

Aktueller Stand der Datei `_massentest/ergebnisse/massentest_ergebnisse.json`:

- Untersuchte Dokumente mit Lieferantenabweichung: 39
- In 27 Faellen ist der Soll-Lieferant im OCR-/Debugtext erkennbar, gewinnt aber nicht.
- In 7 Faellen ist der Soll-Lieferant nicht exakt in der Lieferantenkonfiguration abgebildet.
- In 3 Faellen scheinen Suchwort/OCR-Schreibweise zu eng oder abweichend zu sein.
- In 1 Fall gewinnt eine Bank-/Finanzierungszeile fachlich falsch.
- In 1 Fall koennte der Dateiname helfen, der Lieferant ist im OCR-Text aber nicht erkennbar.

Der groesste Hebel fuer Sprint 4C ist daher nicht noch mehr `safe_set_meta`, sondern eine bessere Kandidatenbildung und Kandidaten-Nachvollziehbarkeit: Lieferantenkonfiguration/Aliase, Kopfbereich, Dateiname als schwache Zusatzquelle und Schutz vor spaeten Wrapper-Ueberschreibungen.

Hinweis: Fruehere Auswertungen nannten 40 Lieferantenabweichungen. Die aktuell vorliegende Ergebnisdatei enthaelt nach direktem Soll/Ist-Vergleich 39 Lieferantenabweichungen.

## Vorgehen

Gelesene Quellen:

- `_massentest/ergebnisse/massentest_ergebnisse.json`
- `_debug_text/*_text.txt`
- `_config/lieferanten_konfiguration.txt`
- `_release_4_0/sprint3a_erkennungsarchitektur.md`
- `_release_4_0/sprint3b_safe_meta_set_clear.md`
- `_release_4_0/sprint3c_safe_meta_scoring.md`
- `_release_4_0/sprint4a_lieferantenerkennung.md`

Es wurden keine Programmdateien, Referenzdaten oder Massentestdaten geaendert.

## Fehlergruppen

| Fehlergruppe | Anzahl | Interpretation |
|---|---:|---|
| Spaeterer/anderer Kandidat gewinnt trotz Solltreffer | 18 | Der richtige Lieferant ist vorhanden, wird aber durch einen anderen Kandidaten verdraengt. |
| Soll-Lieferant im OCR-Text, aber nicht als Gewinner | 9 | Kandidat ist sichtbar, wird aber nicht ausreichend stark bewertet oder nicht sauber als Lieferant erkannt. |
| Soll-Lieferant nicht exakt in Konfiguration | 7 | Konfiguration/Aliasliste deckt Sollschreibweise nicht ausreichend ab oder Sollwert ist uneinheitlich. |
| Suchwort zu eng / OCR-Schreibweise abweichend | 3 | Konfiguration existiert teilweise, aber OCR-Text oder Schreibweise passt nicht zur Suchlogik. |
| Bank-/Footer-Zeile gewinnt faelschlich | 1 | Finanzierungs-/Bankinformation wird als Lieferant uebernommen. |
| Dateiname koennte helfen, wird aber nicht genutzt | 1 | OCR liefert keinen Treffer, aber der Dateiname enthaelt einen brauchbaren Hinweis. |

## Tabelle der untersuchten Lieferantenabweichungen

| Nr. | Dokument | Soll-Lieferant | Ist-Lieferant | Dokumenttyp | Bereich / Hinweis | Fehlergruppe |
|---:|---|---|---|---|---|---|
| 1 | 29032026__Alarmanlagen Videoueberwachnung _Tresore Wertschutzschr.pdf | Wiedemann Sicherheitstechnik | Handwerksbetrieb Kend | Angebot | OCR-Zeilen enthalten `Wiedemann Sicherheitstechnik GmbH`; eher Fliesstext/Signaturbereich | Soll-Lieferant im OCR-Text, aber nicht als Gewinner |
| 2 | Amtsgericht Anderes 26.02.2020.pdf | Grundbuchbezirk Altenbochum | LVM | Versicherung | Kopfbereich enthaelt Grundbuchbezirk | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 3 | Bausparkasse Schwaebisch Hall AG Information 01.12.2019.pdf | Bausparkasse Schwaebisch Hall AG | Sparda-Bank West eG | Darlehensvertrag | Kopfbereich und Konfigurationstreffer vorhanden | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 4 | Bausparkasse Schwaebisch Hall AG Information 05.02.2020.pdf | Bausparkasse Schwaebisch Hall AG | Sparda-Bank West eG | Informationsschreiben | Kopfbereich und Konfigurationstreffer vorhanden | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 5 | Bongardstr. 31 Information 20.02.2025.pdf | Anwaltskanzlei Messler & Messler | megi mobility GmbH | Versicherung | Kopfbereich/E-Mail enthaelt Kanzlei | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 6 | BRN94DDF8539961_000810.pdf | Sparda Bank | leer | Gutschrift | Kopfbereich enthaelt `Sparda-Bank` | Soll-Lieferant im OCR-Text, aber nicht als Gewinner |
| 7 | D ul Rechnung 04.03.2024.pdf | Dipl. Psych. Tobis Vielhaber | leer | Rechnung | Kein stabiler OCR-Treffer ermittelt | Soll-Lieferant nicht exakt in Konfiguration |
| 8 | DKV Deutsche Krankenversicherung AG Information 16.02.2026.pdf | DKB Deutsche Kreditbank | Deutsche Kreditbank AG | Versicherung | Sollwert wirkt uneinheitlich zum Dokumentnamen DKV | Soll-Lieferant nicht exakt in Konfiguration |
| 9 | Dr. med. Fahim Ayami Rechnung 06.05.2026.pdf | Dr. med. Fahim Ayami | leer | Rechnung | Dateiname enthaelt Hinweis, OCR-Treffer nicht stabil | Suchwort zu eng / OCR-Schreibweise abweichend |
| 10 | Dr. med.dent.Axel Rechnung 15.04.2026.pdf | Dr. med. dent. Axel Vieler | leer | Rechnung | Kopfbereich enthaelt Arztname | Soll-Lieferant im OCR-Text, aber nicht als Gewinner |
| 11 | Dr. med.dent.Axel Rechnung 26.08.2025.pdf | Dr. med. dent. Axel Vieler | leer | Rechnung | Kopfbereich enthaelt Arztname | Soll-Lieferant im OCR-Text, aber nicht als Gewinner |
| 12 | Flascheral Norge sch Kassenzettel.pdf | Fleischrei Norbert Hirsch | Waage | Kassenbon | OCR offenbar stark gestoert | Soll-Lieferant nicht exakt in Konfiguration |
| 13 | Franke GmbH _ Co. KG Anderes 04.02.2024.pdf | Gartenbau und Floristik Franke GmbH & Co. KG | Amtsgericht Bochum | Behoerde | Lieferant spaet im Text/Fussbereich erkennbar | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 14 | Franke GmbH _ Co. KG Anderes 23.07.2023.pdf | Gartenbau und Floristik Franke GmbH & Co. KG | Amtsgericht Bochum | Behoerde | Kopfbereich enthaelt Franke | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 15 | Franke GmbH _ Co. KG Kassenzettel 15.02.2026.pdf | Gartenbau und Floristik Franke GmbH & Co. KG | Amtsgericht Bochum | Behoerde | Kopfbereich enthaelt Franke | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 16 | Franke GmbH _ Co. KG Rechnung 16.02.2025.pdf | Gartenbau und Floristik Franke GmbH & Co. KG | Amtsgericht Bochum | Behoerde | Kopfbereich enthaelt Franke | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 17 | Franke GmbH _ Co. KG Rechnung 20.07.2025.pdf | Gartenbau und Floristik Franke GmbH & Co. KG | Ft"anke GmbH | Rechnung | OCR-Fragment statt vollstaendiger Firmenname gewinnt | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 18 | Gebers Kassenzettel 18.07.2025.pdf | Traumschloss die grosse Bettenmarke | leer | Kassenbon | Kein stabiler OCR-Treffer ermittelt | Soll-Lieferant nicht exakt in Konfiguration |
| 19 | HanseMerkur Speziale Krankenversicherung AG Information 30.03.2021.pdf | HanseMerkur Speziale Krankenversicherung AG | Speziale Krankenversicherung AG | Versicherung | Teilfragment gewinnt gegen vollstaendigen Namen | Suchwort zu eng / OCR-Schreibweise abweichend |
| 20 | HAPPYsize Anderes 21.08.2023.pdf | Happy Size | leer | Rechnung | Kopfbereich enthaelt Web-/Mail-Hinweise | Soll-Lieferant im OCR-Text, aber nicht als Gewinner |
| 21 | Heinz-Georg Hepp Rechnung 23.08.2025.pdf | Bonprix | Amazon | Rechnung | Kopfbereich enthaelt Bonprix; Empfaenger-/Amazon-Kontext gewinnt | Soll-Lieferant im OCR-Text, aber nicht als Gewinner |
| 22 | Hepp, Simone Information 14.09.2017.pdf | St. Josef-Hospital Bochum | Klinik Tecklenburger Land | Medizinischer Fragebogen | Kein stabiler Solltreffer ermittelt | Soll-Lieferant nicht exakt in Konfiguration |
| 23 | Kraftfahrt-Bundesamt Information 14.09.2016.pdf | Kraftfahrt-Bundesamt | leer | Rechnung | Kopfbereich und Dateiname enthalten Hinweis | Soll-Lieferant im OCR-Text, aber nicht als Gewinner |
| 24 | Kraftfahrt-Bundesamt Information 21.09.2016.pdf | Kraftfahrt-Busndesamt | leer | Rechnung | Sollwert enthaelt vermutlich Schreibfehler | Soll-Lieferant nicht exakt in Konfiguration |
| 25 | Lehner und Kollegen Rechnung 03.07.2025.pdf | Lehner und Kollegen | Telekom | Rechnung | Kopfbereich und Dateiname enthalten Lehner | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 26 | Lehner und Kollegen Rechnung 12.02.2025.pdf | Lehner & Kollegen | Telekom | Rechnung | Mailadresse im Text, Dateiname enthaelt Hinweis | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 27 | Lieferadresse Anderes 23.03.2025.pdf | Genius | Amazon | Bestellbestaetigung | Genius erscheint spaet; Amazon/Lieferadresse dominiert | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 28 | Lowenstein Medical Anderes 07.11.2025.pdf | Loewenstein Medical | leer | Rechnung | Kopfbereich und Dateiname enthalten Hinweis | Soll-Lieferant im OCR-Text, aber nicht als Gewinner |
| 29 | Name Vertrag 03.06.2019.pdf | Allgemeiner deutscher Fahrradclub | Stadt Bochum | Kaufvertrag | Konfiguriert, aber kein stabiler OCR-Treffer gefunden | Suchwort zu eng / OCR-Schreibweise abweichend |
| 30 | Rathaus Bochum Anderes 04.01.2019.pdf | Stadt Bochum | Amtsgericht Bochum | Hundesteuerbescheid | Kopfbereich enthaelt Stadt Bochum | Soll-Lieferant im OCR-Text, aber nicht als Gewinner |
| 31 | Santander Consumer Bank AG Rechnung 15.07.2022.pdf | Ofen.de AA Kaminwelt | Santander Consumer Bank AG | Finanzierung | Bank-/Finanzierungszeile gewinnt statt Fachlieferant | Bank-/Footer-Zeile gewinnt faelschlich |
| 32 | Simone Hepp Rechnung 20.06.2023.pdf | Tierarztpraxis Judith Schoenenstein | Tierarztpraxis | Rechnung | Nur generisches Fragment gewinnt | Soll-Lieferant nicht exakt in Konfiguration |
| 33 | Skyline Therapie Bochum GmbH Anderes 21.04.2026.pdf | Skyline Therapie Bochum | Skyline Therapie Bochum GmbH | Behoerde | Vollstaendige GmbH-Schreibweise vs Soll-Alias | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 34 | Skyline Therapie Bochum GmbH Information 15.04.2026.pdf | Skyline Therapie Bochum | Skyline Therapie Bochum GmbH | Informationsschreiben | Vollstaendige GmbH-Schreibweise vs Soll-Alias | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 35 | Sparda-Bank West eG Anderes 30.01.2020.pdf | Sparda Bank | Sparda-Bank West eG | Darlehensvertrag | Vollstaendige Bankbezeichnung vs Soll-Alias | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 36 | Sparda-Bank West eG Information 11.12.2019.pdf | Sparda Bank | LVM | Versicherung | Sparda im Text/Dateiname, LVM gewinnt | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 37 | Sparda-Bank West eG Kontoauszug 03.09.2019.pdf | Sparda Bank | Sparda-Bank West eG | Kontoauszug | Vollstaendige Bankbezeichnung vs Soll-Alias | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 38 | Stadtwerke Bochum Netz GmbH Information 05.01.2024.pdf | Maingau Energie | Amtsgericht Bochum | Zaehlerstandserfassung | Kopfbereich/Mail enthaelt Maingau | Spaeterer/anderer Kandidat gewinnt trotz Solltreffer |
| 39 | Tibisco Haustierservice Information 26.02.2024.pdf | Tibisco Haustierservice | leer | Medizinischer Fragebogen | Dateiname enthaelt Hinweis, OCR nicht | Dateiname koennte helfen, wird aber nicht genutzt |

## Kandidatenpipeline - Bewertung

### Konfigurationstreffer

Konfigurationstreffer helfen, aber sie reichen aktuell nicht immer bis zur finalen Entscheidung durch. Beispiele:

- Bausparkasse Schwaebisch Hall AG wird im Kopfbereich und in der Konfiguration gefunden, verliert aber gegen Sparda-Bank.
- Bonprix wird erkannt, verliert aber gegen Amazon.
- Stadt Bochum wird erkannt, verliert aber gegen Amtsgericht Bochum.
- Maingau Energie wird erkannt, verliert aber gegen Amtsgericht Bochum.
- Skyline Therapie Bochum wird erkannt, endet aber als abweichende GmbH-Schreibweise.

Schlussfolgerung: Nicht nur die Konfiguration ist relevant, sondern auch die spaetere Priorisierung und Alias-Normalisierung.

### Kopfbereichstreffer

Viele richtige Lieferanten stehen im Kopfbereich, werden aber trotzdem nicht final uebernommen. Der Kopfbereich ist fachlich die staerkste Quelle, wird aber offenbar durch spaetere Wrapper, Dokumenttyp-Hinweise oder andere Treffer relativiert.

Typische Beispiele:

- Bausparkasse Schwaebisch Hall AG
- Dr. med. dent. Axel Vieler
- Franke GmbH & Co. KG
- Kraftfahrt-Bundesamt
- Lehner und Kollegen
- Lowenstein Medical
- Stadt Bochum
- Maingau Energie

Schlussfolgerung: Kopfbereichstreffer sollten in Sprint 4C nachvollziehbarer priorisiert werden.

### Dateiname-Hinweis

Der Dateiname enthaelt in mehreren Faellen einen brauchbaren Hinweis, wird aber nicht oder nur schwach genutzt:

- Dr. med. Fahim Ayami
- Kraftfahrt-Bundesamt
- Lehner und Kollegen
- Lowenstein Medical
- Tibisco Haustierservice
- Sparda-Bank West eG
- Skyline Therapie Bochum GmbH

Risiko: Der Dateiname ist nicht immer eine neutrale Quelle, weil er aus frueherer Erkennung oder manueller Pflege stammen kann. Als schwacher Kandidat oder Tie-Breaker ist er aber sinnvoll.

### OCR-Rohtext

Der OCR-Rohtext enthaelt oft den richtigen Lieferanten, aber nicht immer in idealer Form:

- Umlaut-/Encodingvarianten
- Bindestriche
- E-Mail-/Webadressen statt Firmenname
- OCR-Fragmente
- abgeschnittene Firmenformen
- Lieferant steht spaet im Text statt im Kopf

Schlussfolgerung: Normalisierung und Kontextbewertung sind wichtiger als reine Stringtreffer.

### Wrapper-/Sonderregeln

Auffaellig sind wiederkehrende falsche Gewinner:

- Amtsgericht Bochum
- LVM
- Telekom
- Amazon
- Sparda-Bank West eG
- Santander Consumer Bank AG

Diese Kandidaten sind nicht immer falsch, gewinnen aber in mehreren Faellen gegen fachlich passendere Kopfbereichs- oder Konfigurationstreffer.

### WebUI-/Massentest-Postprocess

Die WebUI zeigt die Abweichungen auf Basis von Soll/Ist-Daten korrekt an. Es gibt keine Hinweise, dass die WebUI die Lieferantenentscheidung selbst fachlich anders trifft. Die Ursachen liegen in der vorgelagerten Erkennung und Normalisierung sowie in Sollwert-/Alias-Unterschieden.

## Auffaellige Muster

### Alias- und Sollwert-Schreibweisen

Ein Teil der Abweichungen ist wahrscheinlich keine echte Erkennungsverschlechterung, sondern Alias-/Sollwert-Inkonsistenz:

- `Sparda Bank` vs `Sparda-Bank West eG`
- `Skyline Therapie Bochum` vs `Skyline Therapie Bochum GmbH`
- `DKB Deutsche Kreditbank` im Sollwert bei Dokumentname `DKV Deutsche Krankenversicherung AG`
- `Kraftfahrt-Busndesamt` mit Schreibfehler

Diese Faelle sollten vor aggressiven Codeaenderungen bereinigt oder ueber Alias-Normalisierung bewertet werden.

### Empfaenger-/Lieferadresse und Plattformkontext

Bonprix/Genius/Amazon zeigen, dass Empfaenger-, Lieferadress- oder Plattformzeilen einen falschen Lieferanten staerker machen koennen als den fachlichen Absender.

### Banken und Finanzierer

Banken sind kritisch, weil sie sowohl echter Lieferant als auch Zahlungs-/Finanzierungspartner sein koennen. Santander gewinnt bei einem Ofen.de/Kaminwelt-Fall; Sparda gewinnt bei Bausparkasse-Faellen.

### Behoerden und Gerichte

Amtsgericht Bochum gewinnt mehrfach in Faellen, in denen der fachlich erwartete Absender ein anderer ist. Behoerden-/Gerichtsbegriffe scheinen zu stark oder zu breit zu wirken.

### Medizinische Dokumente

Arzt-/Praxisnamen werden teils nur als Fragment erkannt oder nicht in der Konfiguration abgedeckt. Hier fehlen eher Alias-/Suchwortpflege und bessere Kopfbereichsauswertung als neue Sonderregeln.

## Top-Hebel fuer Sprint 4C

| Prioritaet | Hebel | Betroffene Faelle grob | Erwarteter Nutzen | Risiko |
|---:|---|---:|---|---|
| 1 | Kandidaten-Trace fuer Lieferant aktiv auswertbar machen | alle 39 | Erklaert, warum ein Kandidat gewinnt oder verliert | niedrig, wenn nur Diagnose |
| 2 | Lieferantenkonfiguration/Aliasliste pflegen und normalisieren | ca. 10-15 | Reduziert falsche Abweichungen und Fragmenttreffer | niedrig bis mittel |
| 3 | Kopfbereichstreffer staerker und nachvollziehbarer priorisieren | ca. 15-20 | Richtiger Absender gewinnt haeufiger | mittel, wegen Briefkopf/Empfaenger-Verwechslung |
| 4 | Spaete Wrapper-Ueberschreibungen begrenzen | ca. 18 | Verhindert, dass gute Kandidaten ersetzt werden | mittel, weil echte spaete Korrekturen erhalten bleiben muessen |
| 5 | Dateiname als schwache Kandidatenquelle/Tie-Breaker nutzen | ca. 8-10 | Hilft bei OCR-schwachen Dokumenten | mittel, weil alte Dateinamen fehlerbehaftet sein koennen |
| 6 | Bank-/Footer-/Kontaktzeilen abwerten | ca. 4-6 | Weniger falsche Banken/Partner als Lieferant | mittel, weil Banken echte Lieferanten sein koennen |

## Empfehlung fuer Sprint 4C

Sprint 4C sollte kein grosser Umbau der Erkennung werden. Empfohlen ist ein kontrollierter, messbarer Schritt:

1. Lieferanten-Kandidaten-Trace erweitern oder aus vorhandenen Daten sauber ausgeben:
   - Kandidat
   - Quelle
   - Zeile/Bereich
   - Score/Prioritaet
   - Grund fuer Gewinn oder Blockierung

2. Alias-/Konfigurationspflege pruefen:
   - Sparda Bank / Sparda-Bank West eG
   - Skyline Therapie Bochum / Skyline Therapie Bochum GmbH
   - Kraftfahrt-Bundesamt-Schreibweise
   - Dr.-/Praxisnamen
   - Franke/Gartenbau
   - Lowenstein/Loewenstein

3. Kopfbereich als Quelle staerken, aber Empfaengeradressen abgrenzen:
   - Firmen-/Institutionserkennung im Kopf
   - E-Mail/Webdomain als Zusatzsignal
   - bekannte Empfaenger-/Lieferadressnamen abwerten

4. Spaete Gewinner pruefen:
   - Amtsgericht Bochum
   - LVM
   - Telekom
   - Amazon
   - Santander Consumer Bank AG
   - Sparda-Bank West eG

5. Dateiname nur vorsichtig verwenden:
   - als Diagnosehinweis
   - als Tie-Breaker bei leerem/unsicherem Lieferanten
   - nicht als alleiniger starker Beweis

## Risiken

- Eine staerkere Kopfbereichsgewichtung kann Empfaengerzeilen faelschlich als Lieferanten uebernehmen.
- Dateiname als Kandidatenquelle kann alte Fehler fortschreiben.
- Banknamen duerfen nicht pauschal abgewertet werden, weil Kontoauszuege und Bankdokumente echte Banklieferanten haben.
- Konfigurationspflege kann Uebertreffer erzeugen, wenn Suchwoerter zu allgemein sind.
- Alias-Normalisierung kann echte juristische Unterschiede verdecken, wenn sie zu breit wird.
- OCR-/Logo-only-Faelle lassen sich ohne OCR- oder Bildanalyse nur begrenzt verbessern.

## Einordnung

Sprint 4B spricht eher fuer diese Sprint-4C-Richtung:

1. zuerst Kandidaten-Trace und Alias-/Konfigurationsbereinigung,
2. dann Kopfbereichs- und Wrapper-Priorisierung,
3. danach vorsichtige Dateiname-Quelle,
4. erst spaeter groessere Kandidatenlogik.

Eine komplette neue Erkennungsengine ist fuer den naechsten Schritt nicht erforderlich. Der groesste Nutzen liegt vermutlich darin, vorhandene gute Kandidaten sichtbar zu machen, Aliasfaelle zu normalisieren und spaete falsche Gewinner kontrolliert zu begrenzen.
