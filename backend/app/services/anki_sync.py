"""Sync Anki collection to the app database on startup."""
import sqlite3
import json
import shutil
import os
import tempfile
import logging

logger = logging.getLogger(__name__)


def get_anki_path() -> str:
    """Get Anki path from config file."""
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
    default_path = "~/Library/Application Support/Anki2/User 1/collection.anki2"

    if os.path.exists(config_file):
        try:
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
                return os.path.expanduser(config.get("anki_path", default_path))
        except:
            pass
    return os.path.expanduser(default_path)


def export_anki_to_db() -> str | None:
    """Export Anki collection to anki_export.db. Returns path to export db or None on failure."""
    anki_path = get_anki_path()

    # Destination path - in the backend directory
    dest_db = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "anki_export.db")

    if not os.path.exists(anki_path):
        logger.warning(f"Anki collection not found at {anki_path}")
        # Check if we have an existing export to use
        if os.path.exists(dest_db):
            logger.info(f"Using existing anki_export.db")
            return dest_db
        return None

    # Create temp copy to avoid locking issues
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "temp_collection.anki2")

    try:
        shutil.copy2(anki_path, temp_db)
        logger.info(f"Copied Anki database from {anki_path}")

        source = sqlite3.connect(temp_db)
        source.create_collation("unicase", lambda x, y: (x.lower() > y.lower()) - (x.lower() < y.lower()))

        dest = sqlite3.connect(dest_db)

        # Initialize destination
        cursor_d = dest.cursor()
        cursor_d.execute("DROP TABLE IF EXISTS notes")
        cursor_d.execute("""
            CREATE TABLE notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anki_note_id INTEGER,
                deck_name TEXT,
                model_name TEXT,
                fields JSON,
                tags TEXT,
                interval INTEGER,
                reps INTEGER,
                lapses INTEGER,
                status TEXT,
                characters TEXT
            )
        """)
        dest.commit()

        cursor_s = source.cursor()

        # Get field mappings
        cursor_s.execute("SELECT ntid, ord, name FROM fields ORDER BY ntid, ord")
        field_mappings = {}
        for ntid, ord, name in cursor_s.fetchall():
            if ntid not in field_mappings:
                field_mappings[ntid] = []
            while len(field_mappings[ntid]) <= ord:
                field_mappings[ntid].append(None)
            field_mappings[ntid][ord] = name

        # Get model names
        cursor_s.execute("SELECT id, name FROM notetypes")
        model_names = dict(cursor_s.fetchall())

        # Find target decks
        cursor_s.execute("""
            SELECT id, name FROM decks
            WHERE name LIKE '%japanese%'
            OR name LIKE '%Japanese%'
            OR name LIKE '%Wanikani%'
            OR name LIKE '%WaniKani%'
        """)
        target_decks = {row[0]: row[1] for row in cursor_s.fetchall()}

        if not target_decks:
            logger.warning("No Japanese/WaniKani decks found in Anki")
            source.close()
            dest.close()
            return None

        deck_ids = list(target_decks.keys())
        placeholders = ','.join('?' for _ in deck_ids)

        logger.info(f"Exporting from {len(deck_ids)} decks...")

        query = f"""
            SELECT DISTINCT n.id, c.did, n.mid, n.flds, n.tags, c.type, c.queue, c.ivl, c.reps, c.lapses
            FROM cards c
            JOIN notes n ON c.nid = n.id
            WHERE c.did IN ({placeholders})
        """

        cursor_s.execute(query, deck_ids)
        rows = cursor_s.fetchall()

        logger.info(f"Found {len(rows)} cards/notes to export")

        batch = []
        for row in rows:
            nid, did, mid, flds_str, tags, c_type, c_queue, c_ivl, c_reps, c_lapses = row
            deck_name = target_decks.get(did, "Unknown")
            model_name = model_names.get(mid, "Unknown")

            # Determine status
            if c_queue < 0:
                status = "Suspended"
            elif c_type == 0 or c_queue == 0:
                status = "New"
            elif c_type == 1 or c_type == 3:
                status = "Learning"
            elif c_type == 2:
                status = "Mature" if c_ivl >= 21 else "Young"
            else:
                status = "Unknown"

            field_names = field_mappings.get(mid, [])
            field_values = flds_str.split('\x1f')

            data = {}
            for i, val in enumerate(field_values):
                if i < len(field_names) and field_names[i]:
                    data[field_names[i]] = val
                else:
                    data[f"field_{i+1}"] = val

            # Determine characters
            characters = ""
            for p in ['Characters', 'vocab', 'katakana', 'Word', 'Front']:
                if p in data:
                    characters = data[p]
                    break
            if not characters and field_names:
                characters = data.get(field_names[0], "")

            batch.append((nid, deck_name, model_name, json.dumps(data), tags, c_ivl, c_reps, c_lapses, status, characters))

        cursor_d.executemany("""
            INSERT INTO notes (anki_note_id, deck_name, model_name, fields, tags, interval, reps, lapses, status, characters)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch)

        dest.commit()
        source.close()
        dest.close()

        logger.info(f"Anki export completed: {len(batch)} notes")
        return dest_db

    except Exception as e:
        logger.error(f"Failed to export Anki collection: {e}")
        return None
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
