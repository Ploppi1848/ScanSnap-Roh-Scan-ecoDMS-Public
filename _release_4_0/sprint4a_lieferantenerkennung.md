# Sprint 4A - Lieferantenerkennung

## Ausgangslage

Die Qualitaetsanalyse zeigte:

- Lieferant: 40 abweichende Dokumente
- Neuer Dateiname: 52 abweichende Dokumente

Viele Dateinamensfehler sind Folgefehler falscher Lieferanten. Sprint 4A verbessert deshalb die fruehe und stabile Lieferantenerkennung, ohne neue breite Sonderfall-Kaskaden aufzubauen.

## Geaenderte Lieferantenlogik

Die bisherige Konfigurationssuche nahm den ersten passenden Suchworttreffer. Das war riskant, weil Treffer in Fusszeilen, Bankverbindungen, Empfaenger-/Lieferadressbereichen oder Kontaktzeilen gegen den eigentlichen Dokumentkopf gewinnen konnten.

Neu:

- Alle Treffer aus `lieferanten_konfiguration.txt` werden als Kandidaten gesammelt.
- Jeder Kandidat wird bewertet.
- Der beste Kandidat gewinnt.
- Schwache oder unplausible Treffer werden verworfen.
- Wenn nur schwache Roh-Treffer existieren, wird kein Lieferant gesetzt, statt den alten ersten Treffer zu uebernehmen.

## Neue Bewertungs-/Kandidatenregeln

Bewertet wird generisch nach:

- Kopfbereich: Treffer in den ersten Zeilen erhalten hohes Gewicht.
- Vollstaendigkeit: laengere plausible Firmen-/Institutionsnamen werden bevorzugt.
- Konfigurationsquelle: nur Treffer aus der bestehenden Lieferantenkonfiguration werden bewertet.
- Firmen-/Institutionsmerkmale: z. B. GmbH, AG, Bank, Sparkasse, Bausparkasse, Amtsgericht, Stadt, Rathaus, Versicherung, Therapie, Praxis.
- Suchwortlaenge: spezifische Suchwoerter sind staerker als kurze generische Treffer.

Abgewertet oder verworfen werden:

- Empfaenger-/Lieferadresszeilen
- Namen wie Heinz-Georg Hepp / Simone Hepp
- Orts-, Strassen-, Kontakt- und Fusszeilen
- IBAN/BIC/Bankverbindungszeilen
- reine kurze Fragmente
- generische Label wie Rechnung, Kundennummer, Datum, Auftrag

## Geschuetzte Problemgruppen

Ohne neue Einzelfallkaskaden wurden generische Schutzmechanismen fuer diese Gruppen verbessert:

- Bonprix / Lieferadresse: Lieferadresse und Empfaengerzeilen werden abgewertet.
- Banken / Sparda / Bausparkasse: Banknamen werden nur bei passendem Bankkontext oder Kopfbereich stark bewertet.
- Stadt / Rathaus / Behoerden: institutionelle Kopfbereichsmuster wurden erweitert.
- Amtsgericht: institutioneller Kopfbereich kann als Lieferant erkannt werden, Fuss-/Beteiligtenkontext gewinnt nicht automatisch.
- Skyline Therapie / Gartenbau / Fachbetriebe: vollstaendige Fach-/Firmenbezeichnungen werden im Kopfbereich bevorzugt.

## Risiken

- Eine strengere Kandidatenbewertung kann einzelne bisherige Treffer verwerfen, wenn sie nur in schwachem Kontext vorkommen.
- Die Verbesserung ist noch kein vollstaendiges Kandidaten-/Konfidenzmodell.
- Der echte Effekt muss im naechsten 128er Buildvergleich gemessen werden.

## Testhinweise

Im naechsten Buildvergleich besonders pruefen:

- Lieferant verbessert oder mindestens nicht schlechter.
- Neuer Dateiname verbessert durch stabilere Lieferanten.
- Keine massiven neuen Verschlechterungen bei Dokumenttyp, Betrag oder Nummern.
- Problemgruppen Bonprix, Banken, Bausparkasse, Stadt/Rathaus, Amtsgericht und Skyline gezielt kontrollieren.

## Erwarteter Nutzen

- Weniger Lieferanten aus Fusszeilen, Bankverbindungen und Empfaengeradressen.
- Stabilere Auswahl vollstaendiger Firmen-/Institutionsnamen.
- Weniger Folgefehler im neuen Dateinamen.

## Nicht geaendert

- Keine WebUI-Layoutaenderung.
- Keine Massentest-Datenstruktur.
- Keine Referenzdaten.
- Keine produktiven Aktionen.
- Keine Git-Befehle.
- Keine OCR-Umstellung.
- Keine komplette neue Erkennungsengine.
