import sqlite3
import json

DB_PATH = "collection.anki2"

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    # Register dummy collation to handle Anki's custom 'unicase'
    conn.create_collation("unicase", lambda x, y: (x.lower() > y.lower()) - (x.lower() < y.lower()))
    return conn

def get_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return cursor.fetchall()

def inspect_col_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM col")
    columns = [description[0] for description in cursor.description]
    row = cursor.fetchone()
    if row:
        return dict(zip(columns, row))
    return None

def find_target_decks(conn):
    cursor = conn.cursor()
    # Search for decks starting with 'japanese'
    cursor.execute("SELECT id, name FROM decks WHERE name LIKE 'japanese%' OR name LIKE '%Wanikani%'")
    rows = cursor.fetchall()
    print("\nTarget Decks found:")
    deck_ids = []
    for row in rows:
        print(f"ID: {row[0]}, Name: {row[1]}")
        deck_ids.append(row[0])
    return deck_ids

def inspect_cards_and_notes(conn, deck_ids):
    if not deck_ids:
        print("No decks found to inspect.")
        return

    cursor = conn.cursor()
    # Get a few cards from these decks
    # cards table: id, nid, did, ...
    # notes table: id, flds, ...
    
    placeholders = ','.join('?' for _ in deck_ids)
    query = f"""
        SELECT c.id, c.did, d.name, n.flds
        FROM cards c
        JOIN notes n ON c.nid = n.id
        JOIN decks d ON c.did = d.id
        WHERE c.did IN ({placeholders})
        LIMIT 5
    """
    
    cursor.execute(query, deck_ids)
    rows = cursor.fetchall()
    print(f"\nSample Cards (first 5 from target decks):")
    for row in rows:
        cid, did, dname, flds = row
        # Fields are separated by 0x1f
        fields = flds.split('\x1f')
        print(f"\nCard ID: {cid}")
        print(f"Deck: {dname}")
        print(f"Fields: {fields}")

def inspect_notetypes(conn):
    cursor = conn.cursor()
    # Check if notetypes table exists (newer Anki) or if it's in col.models
    # We saw 'notetypes' in the table list.
    try:
        cursor.execute("SELECT id, name, config FROM notetypes LIMIT 5")
        print("\nNote Types (from table):")
        for row in cursor.fetchall():
            nt_id, name, config_bytes = row
            # Config is often JSON or binary. In newer Anki it might be distinct fields
            # Let's see if we can decode it if it looks like bytes
            print(f"ID: {nt_id}, Name: {name}")
            # print(f"Config: {config_bytes}") # Might be too verbose
            
            # Actually, we need to find where field names are stored.
            # Usually in the 'fields' table or inside the JSON config.
    except sqlite3.OperationalError:
        print("notetypes table read failed.")

    # Also check 'fields' table
    try:
        cursor.execute("SELECT ntid, ord, name FROM fields ORDER BY ntid, ord LIMIT 20")
        print("\nFields (first 20):")
        for row in cursor.fetchall():
            print(f"NoteTypeID: {row[0]}, Order: {row[1]}, Name: {row[2]}")
    except sqlite3.OperationalError:
        print("fields table read failed.")

def analyze_deck_notetypes(conn, deck_ids):
    placeholders = ','.join('?' for _ in deck_ids)
    cursor = conn.cursor()
    
    # Check which note types are used in the target decks
    query = f"""
        SELECT d.name, nt.name, COUNT(*)
        FROM cards c
        JOIN notes n ON c.nid = n.id
        JOIN decks d ON c.did = d.id
        JOIN notetypes nt ON n.mid = nt.id
        WHERE c.did IN ({placeholders})
        GROUP BY d.name, nt.name
    """
    cursor.execute(query, deck_ids)
    print("\nNote usage in target decks:")
    rows = cursor.fetchall()
    for row in rows:
        print(f"Deck: {row[0]}, Note Type: {row[1]}, Count: {row[2]}")
    return rows

def main():
    conn = connect_db()
    try:
        deck_ids = find_target_decks(conn)
        analyze_deck_notetypes(conn, deck_ids)

    finally:
        conn.close()

if __name__ == "__main__":
    main()

