# Anki to SQLite Export

Exports cards from specified Anki decks to a local SQLite database for LLM agent access.

## Setup
1. Ensure Python 3 is installed.
2. Edit `export_anki_to_sqlite.py` if your Anki profile path differs from `~/Library/Application Support/Anki2/User 1/`.

## Usage
Run the script to sync latest Anki progress:
```bash
python3 export_anki_to_sqlite.py
```
This creates/updates `anki_export.db`.

## Database Schema (`anki_export.db`)
Table: `notes`
- `characters`: Primary text (Kanji/Word).
- `status`: New, Learning, Young, Mature, Suspended.
- `fields`: Full card data as JSON.
- `deck_name`: Name of the source deck.
- `interval`: Days until next review.
- `tags`: Card tags.

## Query Example
```sql
SELECT characters, status FROM notes WHERE status = 'Mature' LIMIT 5;
```

