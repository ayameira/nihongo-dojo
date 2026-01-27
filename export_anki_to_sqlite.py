import sqlite3
import json

import shutil
import os

# Path to the live Anki collection (Update 'User 1' if you use a different profile)
ANKI_PATH = os.path.expanduser("~/Library/Application Support/Anki2/User 1/collection.anki2")
TEMP_DB = "temp_collection.anki2"
DEST_DB = "anki_export.db"

def connect_source():
    # Work on a temporary copy to avoid locking the live database if Anki is open
    if os.path.exists(TEMP_DB):
        os.remove(TEMP_DB)
    
    try:
        shutil.copy2(ANKI_PATH, TEMP_DB)
        print(f"Copied Anki database from {ANKI_PATH}")
    except FileNotFoundError:
        print(f"Error: Could not find Anki collection at {ANKI_PATH}")
        print("Please check your Anki profile path.")
        exit(1)

    conn = sqlite3.connect(TEMP_DB)
    # Register dummy collation
    conn.create_collation("unicase", lambda x, y: (x.lower() > y.lower()) - (x.lower() < y.lower()))
    return conn

def cleanup_temp():
    if os.path.exists(TEMP_DB):
        os.remove(TEMP_DB)

def connect_dest():
    conn = sqlite3.connect(DEST_DB)
    return conn

def init_dest_db(conn):
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS notes")
    cursor.execute("""
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
    conn.commit()

def determine_characters(data, field_names):
    # Priority list of field names that likely contain the main character/word
    priorities = ['Characters', 'vocab', 'katakana', 'Word', 'Front', 'Frente', 'Texto']
    
    for p in priorities:
        if p in data:
            return data[p]
    
    # Fallback: use the first field if available
    if field_names:
        return data.get(field_names[0], "")
    
    return ""

def get_field_mappings(conn):
    cursor = conn.cursor()
    # Map mid -> [field_names_sorted_by_ord]
    # We use 'fields' table: ntid, ord, name
    cursor.execute("SELECT ntid, ord, name FROM fields ORDER BY ntid, ord")
    mappings = {}
    for ntid, ord, name in cursor.fetchall():
        if ntid not in mappings:
            mappings[ntid] = []
        # Ensure list is big enough (though sort order should handle it)
        while len(mappings[ntid]) <= ord:
            mappings[ntid].append(None)
        mappings[ntid][ord] = name
    return mappings

def get_model_names(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM notetypes")
    return dict(cursor.fetchall())

def export_data():
    source = connect_source()
    dest = connect_dest()
    init_dest_db(dest)

    try:
        cursor_s = source.cursor()
        cursor_d = dest.cursor()

        field_mappings = get_field_mappings(source)
        model_names = get_model_names(source)

        # Identify target decks
        cursor_s.execute("SELECT id, name FROM decks WHERE name LIKE 'japanese%' OR name LIKE '%Wanikani%'")
        target_decks = {row[0]: row[1] for row in cursor_s.fetchall()}
        
        if not target_decks:
            print("No target decks found.")
            return

        deck_ids = list(target_decks.keys())
        placeholders = ','.join('?' for _ in deck_ids)

        print(f"Exporting from {len(deck_ids)} decks...")

        # Query notes from these decks
        # We join with cards to get deck info. 
        # distinct nid, did pair to handle notes in multiple decks (if any)
        # Added card fields: type, queue, ivl, reps, lapses
        query = f"""
            SELECT DISTINCT n.id, c.did, n.mid, n.flds, n.tags, c.type, c.queue, c.ivl, c.reps, c.lapses
            FROM cards c
            JOIN notes n ON c.nid = n.id
            WHERE c.did IN ({placeholders})
        """
        
        cursor_s.execute(query, deck_ids)
        rows = cursor_s.fetchall()
        
        print(f"Found {len(rows)} cards/notes to export.")
        
        batch = []
        BATCH_SIZE = 1000

        for row in rows:
            nid, did, mid, flds_str, tags, c_type, c_queue, c_ivl, c_reps, c_lapses = row
            deck_name = target_decks.get(did, "Unknown")
            model_name = model_names.get(mid, "Unknown")
            
            # Determine status
            status = "Unknown"
            if c_queue < 0:
                status = "Suspended"
            elif c_type == 0 or c_queue == 0:
                status = "New"
            elif c_type == 1 or c_type == 3:
                status = "Learning"
            elif c_type == 2:
                if c_ivl >= 21:
                    status = "Mature"
                else:
                    status = "Young"
            
            field_names = field_mappings.get(mid, [])
            field_values = flds_str.split('\x1f')
            
            # Create a dictionary of fields
            # Handle mismatch in length if any (Anki sometimes allows it?)
            data = {}
            for i, val in enumerate(field_values):
                if i < len(field_names):
                    data[field_names[i]] = val
                else:
                    data[f"field_{i+1}"] = val
            
            characters = determine_characters(data, field_names)

            batch.append((nid, deck_name, model_name, json.dumps(data), tags, c_ivl, c_reps, c_lapses, status, characters))
            
            if len(batch) >= BATCH_SIZE:
                cursor_d.executemany("""
                    INSERT INTO notes (anki_note_id, deck_name, model_name, fields, tags, interval, reps, lapses, status, characters) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                batch = []
        
        if batch:
            cursor_d.executemany("""
                INSERT INTO notes (anki_note_id, deck_name, model_name, fields, tags, interval, reps, lapses, status, characters) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
        
        dest.commit()
        print("Export completed successfully.")

    finally:
        source.close()
        dest.close()
        cleanup_temp()

if __name__ == "__main__":
    export_data()

