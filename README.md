# Flos Deckarchiv

Übersicht über meine Commander-Decks (Paper), mit Kartenbildern und Preisen von Scryfall, Artworkauswahl und Cardmarket-Links.

## Dateien

- `index.html`: die Seite
- `data.json`: alle Decks, Kategorien, Reihenfolge und gewählte Artworks
- `.nojekyll`: sorgt dafür, dass GitHub Pages die Dateien unverändert ausliefert

## Einrichten (einmalig)

1. Auf github.com ein neues Repository anlegen, z. B. `deckarchiv`, Sichtbarkeit **Public** (GitHub Pages ist für öffentliche Repositories gratis).
2. Im Repository auf **Add file → Upload files** klicken und `index.html`, `data.json`, `README.md` und `.nojekyll` hochladen, dann **Commit changes**.
   Tipp: `.nojekyll` ist eine versteckte Datei. Falls dein Dateimanager sie nicht anzeigt, kannst du sie auf GitHub mit **Add file → Create new file** und dem Namen `.nojekyll` leer anlegen.
3. **Settings → Pages**: bei *Source* „Deploy from a branch“, Branch `main`, Ordner `/ (root)` wählen und speichern.
4. Nach etwa einer Minute ist die Seite erreichbar unter `https://<benutzername>.github.io/deckarchiv/`.

## Speichern auf GitHub (einmal pro Gerät)

Änderungen (Reihenfolge, Kategorien, Namen, Artworks, neue Decks) landen zuerst im Browser. Oben erscheint dann „Ungespeicherte Änderungen“.

Damit „Auf GitHub speichern“ funktioniert:

1. GitHub → Profilbild → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
2. *Repository access*: „Only select repositories“ → `deckarchiv`.
3. *Permissions → Contents*: „Read and write“.
4. Token kopieren, auf der Seite unten links „GitHub-Verbindung“ öffnen, einfügen, „Verbindung testen“, „Speichern“.

Benutzername und Repository werden auf GitHub Pages automatisch erkannt. Der Token bleibt nur im Browser des jeweiligen Geräts.

Ohne Token geht es auch: „data.json herunterladen“ und die Datei im Repository ersetzen (**Add file → Upload files**).
