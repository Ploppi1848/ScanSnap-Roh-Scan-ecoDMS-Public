# Sprint 5E-B - Lieferantenentscheidung Guard

## Ziel

Die Lieferantenentscheidung wird gegen schwache spaete Gewinner stabilisiert.

Aus Sprint 5E-A:

- 42 Dokumente mit Abweichung im Feld `Neuer Dateiname`
- groesster Ursachencluster: falscher oder instabiler Lieferant
- typische falsche Gewinner: `Amtsgericht Bochum`, `Telekom`, `Amazon`, `LVM`, `Sparda-Bank West eG`, E-Mail-Adressen und OCR-Fragmente

## Umsetzung

In `_service/ecodms_scan_service.py` wurde ein kleiner isolierter Schluss-Guard ergaenzt:

- Block `SCAN-SERVICE 6.7 - SUPPLIER GUARD GEGEN SCHWACHE SPAETE GEWINNER`
- zentrale Anwendung: `_apply_supplier_guard_670(...)`
- Logging-Marker: `SUPPLIER_GUARD`

Der Guard greift erst am Ende der bisherigen Pipeline und veraendert keine Dateinamen direkt.

## Schutzmechanismus

Der Guard prueft:

1. Ist der finale Lieferant ein bekannter schwacher spaeter Gewinner oder ein Fragment?
2. Hat dieser Lieferant im Dateinamen oder Dokumentkopf einen starken Eigenkontext?
3. Gibt es im Dokument einen staerkeren konfigurierten Lieferantenkandidaten?
4. Ist dieser Kandidat deutlich plausibler als der aktuelle schwache Endwert?

Nur dann wird der Lieferant ersetzt.

Wenn kein staerkerer Kandidat gefunden wird, bleibt der aktuelle Wert unveraendert. Es wird nichts geraten und kein Lieferant hart gesetzt.

## Abgesicherte echte Kontexte

Echte Dokumente sollen weiterhin ihren Lieferanten behalten:

- Telekom: `Telekom Deutschland`, `Deutsche Telekom`, `telekom.de`, `Festnetz-Rechnung`, `Kundencenter`
- Amazon: `amazon.de`, Amazon Services/Payments, `Verkauft von Amazon`, Amazon-Bestellnummernformat
- Amtsgericht: Amtsgericht im Dateinamen oder echter Justiz-/Grundbuch-/Zahlstellen-Kontext im Kopfbereich
- LVM: LVM im Dateinamen oder echter LVM-Briefkopf/Kontext
- Sparda: Sparda im Dateinamen oder echter Sparda-Briefkopf/Kontext

## Nicht umgesetzt

- keine Dateinamen-Hartkorrekturen
- keine Einzelregeln pro Dokument
- keine WebUI-Aenderungen
- keine Referenzdaten
- keine Sollwertaenderungen
- kein Refactoring der gesamten Lieferantenpipeline

## Risiken

- Der Guard kann nur eingreifen, wenn ein staerkerer Kandidat aus der vorhandenen Lieferantenkonfiguration gefunden wird.
- Fehlende oder zu schwache Konfigurationstreffer bleiben weiterhin offen.
- Bei zu breiten Konfigurationssuchwoertern koennte ein falscher Kandidat gewinnen; deshalb wird zusaetzlich Score und Eigenkontext geprueft.

## Pruefung

Syntaxpruefung:

```text
python -m py_compile _service\ecodms_scan_service.py
```

Ergebnis: erfolgreich.

## Erwarteter Nutzen

Der naechste Buildvergleich sollte zeigen, ob weniger Dateinamenfehler durch falsche Lieferanten entstehen, besonders bei:

- Amtsgericht-Fallbacks in fremden Dokumenten
- Telekom-Fallbacks in fremden Dokumenten
- Amazon-Fallbacks in fremden Dokumenten
- LVM-/Sparda-Kontexttreffern ausserhalb echter LVM-/Sparda-Dokumente
- E-Mail- und OCR-Fragmenten als Lieferant
