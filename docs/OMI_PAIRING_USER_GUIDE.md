# Omi Pairing Guide (User-Dokumentation)

Diese Anleitung erklaert fuer Endnutzer:

- wie Omi gekoppelt wird,
- wo der Sync-Status sichtbar ist,
- was mit den Daten passiert.

## Warum Omi?

Omi ist das Kern-Feature von Character-Websites: Sprachaufnahmen aus dem Alltag helfen, ein authentisches Persoenlichkeitsprofil aufzubauen. Daraus entstehen automatisch Website-Updates.

## Voraussetzungen

Bevor du startest:

- Du hast einen aktiven Character-Websites Account.
- Dein Omi Geraet ist eingerichtet und geladen.
- Du bist im gleichen Account eingeloggt, in dem deine Website erstellt wurde.

## Schritt-fuer-Schritt: Omi pairen

1. **Dashboard oeffnen**
   - Gehe zu `Settings` -> `Integrations` -> `Omi`.
2. **"Connect Omi" klicken**
   - Du wirst zur Omi-Freigabe weitergeleitet (OAuth).
3. **Zugriff bestaetigen**
   - Erlaube den Zugriff auf deine Omi-Konversationen/Aufnahmen.
4. **Zurueckleitung abwarten**
   - Du wirst automatisch zurueck in dein Character-Websites Dashboard geleitet.
5. **Pairing bestaetigen**
   - Status wechselt auf **Connected**.
   - Optional wird die Geraete-ID angezeigt.

Wenn der Status nicht auf "Connected" springt, siehe Abschnitt **Fehlerbehebung**.

## Wo sehe ich Updates?

Nach erfolgreichem Pairing gibt es drei wichtige Statusanzeigen:

### 1) Pairing-Status

- **Connected**: Omi ist korrekt verbunden.
- **Disconnected**: Verbindung getrennt oder abgelaufen.
- **Re-auth required**: Berechtigung muss erneut bestaetigt werden.

### 2) Sync-Status

- **Last sync**: Zeitpunkt des letzten erfolgreichen Uploads.
- **Recordings synced**: Anzahl uebertragener Aufnahmen.
- **Queue/Retry**: Warteschlange bei Netzwerkproblemen.

### 3) Website-Update-Status

- **Processing**: Analyse laeuft.
- **Updated**: Neue Persoenlichkeitsdaten wurden uebernommen.
- **Needs attention**: Analyse oder Upload braucht Eingriff.

## Was passiert mit meinen Daten?

Kurzfassung:

1. Omi-Aufnahme wird erkannt.
2. Aufnahme wird sicher an die Plattform uebertragen.
3. Audio wird transkribiert (falls noetig mit Fallback).
4. Akustische Merkmale (z. B. Rhythmus, Pausen, Tonlage) werden extrahiert.
5. KI erstellt/aktualisiert Persoenlichkeitsstruktur.
6. Deine Website wird mit den neuen Signalen aktualisiert.

Wichtig:

- Rohdaten sind **nicht** oeffentlich auf der Website.
- Sensible Keys (z. B. Service Keys) bleiben serverseitig.
- Zugriff auf Daten ist an Nutzerrechte und Policies gebunden.

## Datenschutz und Kontrolle

Du kannst jederzeit:

- einzelne Aufnahmen loeschen,
- alle Voice-Daten entfernen,
- den Sync pausieren/deaktivieren,
- Omi entkoppeln (Unpair).

Empfehlung: Nutze die Privacy-Optionen in `Settings` -> `Privacy` fuer regelmaessige Kontrolle.

## Fehlerbehebung

### Pairing bricht ab

- Erneut einloggen und `Connect Omi` neu starten.
- Browser-Popup-Blocker deaktivieren.
- Pruefen, ob der richtige Omi-Account verwendet wird.

### Keine neuen Aufnahmen sichtbar

- Pruefen, ob Omi verbunden ist (**Connected**).
- Internetverbindung und ggf. Offline-Queue abwarten.
- Im Dashboard `Last sync` und Fehlerstatus pruefen.

### Website aktualisiert sich nicht

- Status `Processing` abwarten.
- Bei dauerhaftem Fehler: Verbindung trennen und neu pairen.
- Support kontaktieren mit Zeitstempel des letzten Syncs.

## FAQ

### Muss Omi permanent verbunden sein?

Nein. Nach erfolgreichem Pairing laeuft die Synchronisierung im Hintergrund, solange Berechtigung und Verbindung gueltig sind.

### Werden private Gespraeche automatisch veroeffentlicht?

Nein. Roh-Audio wird nicht direkt veroeffentlicht. Die Website verwendet aufbereitete Signale/Ergebnisse, keine ungeschuetzten Originaldaten.

### Kann ich Omi spaeter erneut verbinden?

Ja. Unpair/Re-pair ist jederzeit moeglich.
