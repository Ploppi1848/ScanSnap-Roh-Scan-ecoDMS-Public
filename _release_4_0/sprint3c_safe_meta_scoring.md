# Sprint 3C - Safe Meta Scoring

## Ausgangslage Buildvergleich Sprint 3B

Sprint 3B brachte eine erste Schutzschicht gegen stille Ueberschreibungen und pauschales Leeren.

Buildvergleich:

- Verbessert: 6
- Verschlechtert: 5
- Neu auffaellig: 12
- Unveraendert: 105

Feldwirkung:

- `GESAMTBETRAG` verbessert: 4
- `LIEFERANT` verschlechtert: 13
- `DOKUMENTTYP` verschlechtert: 12
- `NEUER DATEINAME` verschlechtert: 11
- `RECHNR` verschlechtert: 1

Fazit: Der Betragsschutz war hilfreich, aber die Safe-Set-Logik fuer Lieferant und Dokumenttyp war zu streng und blockierte sinnvolle spaetere Korrekturen.

## Geaenderte Bewertungslogik

`safe_set_meta(...)` entscheidet jetzt differenzierter:

### Lieferant

Spaetere Lieferantenwerte werden erlaubt, wenn sie plausibel besser sind:

- konfigurierter Lieferant ersetzt nicht-konfigurierten Kandidaten
- laengerer plausibler Firmen-/Institutionsname ersetzt kurzes Fragment
- normalisierte Lieferantenvarianten duerfen uebernommen werden
- OCR-Fragmente, Labels und Satzteile bleiben blockiert

Die Bewertung nutzt eine kleine Score-Funktion mit:

- Lieferantenkonfiguration
- Firmen-/Institutionsmerkmalen
- Wort-/Laengenplausibilitaet
- Fragment- und Label-Abwertung

### Dokumenttyp

Die Dokumenttyp-Regeln wurden entschaerft:

- spezifischer Nicht-Rechnungs-Typ darf `Rechnung` ersetzen
- `Rechnung` darf spezifische Typen nicht ohne starken Grund ersetzen
- spezifische Typen duerfen generische Typen wie `Information`, `Schreiben`, `Dokument` oder `Unbekannt` ersetzen

### Gesamtbetrag

Der Sprint-3B-Schutz bleibt bewusst weitgehend erhalten:

- plausible Betraege werden nicht pauschal geleert
- keine neue Betragsextraktion
- keine neue Betragsheuristik

### RECHNR / KUNDENNR

Nur konservativer Schutz:

- leere Werte duerfen plausible vorhandene Werte nicht loeschen
- keine neue Nummernextraktion
- keine Umverteilung zwischen RECHNR, KUNDENNR und AKTENZEICHEN

## Adressierte Verschlechterungen

Die Nachschaerfung zielt auf Verschlechterungen durch zu strenges Blockieren spaeter Korrekturen, besonders bei:

- Bausparkasse Schwaebisch Hall
- Sparda-Bank
- Stadt Bochum / Rathaus Bochum
- Skyline Therapie
- Amtsgericht
- Lieferadresse / Bonprix-aehnliche Faelle

Diese Faelle wurden nicht als neue Einzelregeln umgesetzt. Stattdessen wurde die allgemeine Bewertung in `safe_set_meta(...)` verbessert.

## Erwarteter Nutzen

- Verbesserungen beim `GESAMTBETRAG` aus Sprint 3B bleiben erhalten.
- Lieferant und Dokumenttyp koennen wieder sinnvoll durch spaete Wrapper korrigiert werden.
- Der neue Dateiname sollte weniger Folgeverschlechterungen durch blockierte Lieferant-/Typ-Korrekturen zeigen.
- SAFE_META-Logs erklaeren Entscheidungen genauer.

## Risiken

- Ein spaeter Kandidat mit hohem Score kann einen fruehen plausiblen Wert wieder ersetzen.
- Die Bewertung ist noch kein vollstaendiges Kandidaten-/Konfidenzmodell.
- Der echte Nettoeffekt muss im naechsten 128er Buildvergleich gemessen werden.

## Testhinweise

Empfohlene Kontrolle im naechsten Buildvergleich:

- Lieferant: Verschlechterungen gegen Sprint 3B deutlich reduziert?
- Dokumenttyp: Rechnung-Fallbacks weiterhin blockiert, aber spezifische Korrekturen erlaubt?
- Gesamtbetrag: Verbesserungen aus Sprint 3B stabil?
- Neuer Dateiname: weniger Folgeverschlechterungen durch Lieferant/Dokumenttyp?

## Nicht geaendert

- Keine WebUI-Layoutaenderung.
- Keine Massentest-Datenstruktur.
- Keine Referenzdaten.
- Keine produktiven Aktionen.
- Keine Git-Befehle.
- Keine neue Erkennungsengine.
