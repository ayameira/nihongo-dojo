import sqlite3
import shutil
import os
import json
import tempfile
import re
from datetime import datetime
from typing import Dict, Any, List
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import VocabEntry, AnkiDeckConfig
from app.services.anki_introspect import read_deck_notes
from app.core.language_profiles import get_language_profile

logger = logging.getLogger(__name__)


async def import_deck_config(config: AnkiDeckConfig, session: AsyncSession) -> Dict[str, Any]:
    """Import a single configured Anki deck source using its field mapping.

    Vocab is deduplicated per deck source via (deck_config_id, anki_note_id), so
    re-syncing updates existing rows instead of creating duplicates.
    """
    notes = read_deck_notes(config.collection_path, config.deck_name)
    profile = get_language_profile(config.language_code)

    imported = 0
    updated = 0
    skipped = 0

    for note in notes:
        fields = note["fields"]

        # Optional per-deck note filter (e.g. Object_Type == "Vocabulary").
        if config.filter_field:
            actual = strip_html(fields.get(config.filter_field, ""))
            if actual != (config.filter_value or ""):
                skipped += 1
                continue

        kanji = strip_html(fields.get(config.kanji_field, "")) if config.kanji_field else ""
        kana = strip_html(fields.get(config.kana_field, "")) if config.kana_field else ""
        meaning = strip_html(fields.get(config.meaning_field, "")) if config.meaning_field else ""
        pos = strip_html(fields.get(config.pos_field, "")) if config.pos_field else None

        normalized = profile.normalize_vocab_fields(kanji, kana, meaning, pos)
        kanji = normalized["term"] or ""
        kana = normalized["reading"] or ""
        meaning = normalized["meaning"] or ""
        pos = normalized["part_of_speech"]

        if not kana or "<" in kana or len(kana) > 50:
            skipped += 1
            continue

        status = determine_status(note["c_type"], note["c_queue"], note["c_ivl"])
        note_id = note["anki_note_id"]

        stmt = select(VocabEntry).where(
            VocabEntry.deck_config_id == config.id,
            VocabEntry.anki_note_id == note_id,
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing:
            existing.kanji = kanji or None
            existing.kana = kana
            existing.meaning = meaning
            existing.pos = pos or None
            existing.status = status
            existing.interval_days = note["c_ivl"]
            updated += 1
        else:
            session.add(VocabEntry(
                kanji=kanji or None,
                kana=kana,
                meaning=meaning,
                pos=pos or None,
                status=status,
                source="anki",
                anki_note_id=note_id,
                deck_config_id=config.id,
                language_code=config.language_code,
                interval_days=note["c_ivl"],
            ))
            imported += 1

    config.last_synced_at = datetime.utcnow()
    await session.commit()

    return {
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "total_processed": len(notes),
    }


async def sync_all_decks(
    session: AsyncSession,
    language_code: str | None = None,
) -> List[Dict[str, Any]]:
    """Sync every enabled Anki deck source. Failures are reported per deck and
    never abort the remaining decks."""
    stmt = select(AnkiDeckConfig).where(AnkiDeckConfig.enabled.is_(True))
    if language_code:
        stmt = stmt.where(AnkiDeckConfig.language_code == language_code)
    configs = (await session.execute(stmt)).scalars().all()

    results: List[Dict[str, Any]] = []
    for config in configs:
        try:
            result = await import_deck_config(config, session)
            results.append({"deck_config_id": config.id, "name": config.name, **result})
            logger.info(
                f"Anki sync '{config.name}': {result['imported']} imported, "
                f"{result['updated']} updated, {result['skipped']} skipped"
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Anki sync failed for '{config.name}': {e}")
            results.append({"deck_config_id": config.id, "name": config.name, "error": str(e)})
    return results


async def import_from_export_db(
    export_db_path: str,
    session: AsyncSession
) -> Dict[str, Any]:
    """Import vocabulary from an existing anki_export.db file."""

    export_db_path = os.path.expanduser(export_db_path)

    if not os.path.exists(export_db_path):
        raise FileNotFoundError(f"Export database not found: {export_db_path}")

    conn = sqlite3.connect(export_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query the existing export data - only Vocabulary and Kanji entries
    cursor.execute("""
        SELECT anki_note_id, characters, fields, status, interval
        FROM notes
        WHERE characters IS NOT NULL AND characters != ''
        AND (
            json_extract(fields, '$.Object_Type') = 'Vocabulary'
            OR json_extract(fields, '$.Object_Type') = 'Kanji'
        )
    """)
    rows = cursor.fetchall()
    conn.close()

    imported = 0
    updated = 0
    skipped = 0

    for row in rows:
        note_id = row['anki_note_id']
        characters = row['characters']
        fields_json = row['fields']
        status = row['status']
        interval = row['interval'] or 0

        # Skip HTML/radical entries
        if '<' in characters or len(characters) > 20:
            skipped += 1
            continue

        try:
            fields = json.loads(fields_json) if fields_json else {}
        except:
            fields = {}

        # Extract meaning from fields
        meaning = fields.get('Meaning', '') or fields.get('meaning', '') or ''

        # Strip HTML from meaning
        meaning = strip_html(meaning)

        # Get reading
        reading = fields.get('Reading', '') or fields.get('Reading_Whitelist', '') or ''
        reading = strip_html(reading)

        # Determine kanji vs kana
        # If characters contains kanji, it's kanji; reading is kana
        # If characters is all kana, no kanji
        kanji = None
        kana = characters

        if has_kanji(characters):
            kanji = characters
            kana = reading if reading else characters

        if not kana:
            skipped += 1
            continue

        # Map status
        db_status = map_status(status)

        # Check if exists
        stmt = select(VocabEntry).where(
            VocabEntry.language_code == "ja",
            VocabEntry.anki_note_id == note_id,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.language_code = "ja"
            existing.kanji = kanji
            existing.kana = kana
            existing.meaning = meaning
            existing.status = db_status
            existing.interval_days = interval
            updated += 1
        else:
            entry = VocabEntry(
                language_code="ja",
                kanji=kanji,
                kana=kana,
                meaning=meaning,
                status=db_status,
                source="anki",
                anki_note_id=note_id,
                interval_days=interval,
            )
            session.add(entry)
            imported += 1

    await session.commit()

    return {
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "total_processed": len(rows),
    }


async def import_anki_collection(
    anki_path: str,
    session: AsyncSession
) -> Dict[str, Any]:
    """Import vocabulary from an Anki collection into the database.

    Legacy compatibility path: this predates the deck-config wizard and keeps
    the old Japanese/WaniKani heuristics intentionally. New language profiles
    should use AnkiDeckConfig + import_deck_config instead.
    """

    # Check if this is pointing to anki_export.db (pre-parsed)
    anki_path = os.path.expanduser(anki_path)

    if anki_path.endswith('anki_export.db'):
        return await import_from_export_db(anki_path, session)

    if not os.path.exists(anki_path):
        raise FileNotFoundError(f"Anki collection not found: {anki_path}")

    # Create temp copy to avoid locking issues
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "temp_collection.anki2")

    try:
        shutil.copy2(anki_path, temp_db)

        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        conn.create_collation("unicase", lambda x, y: (x.lower() > y.lower()) - (x.lower() < y.lower()))

        cursor = conn.cursor()

        field_mappings = get_field_mappings(cursor)
        model_names = get_model_names(cursor)

        # Find Japanese-related decks
        cursor.execute("""
            SELECT id, name FROM decks
            WHERE name LIKE '%japanese%'
            OR name LIKE '%Japanese%'
            OR name LIKE '%Wanikani%'
            OR name LIKE '%vocab%'
            OR name LIKE '%kanji%'
        """)
        target_decks = {row[0]: row[1] for row in cursor.fetchall()}

        if not target_decks:
            cursor.execute("SELECT id, name FROM decks")
            target_decks = {row[0]: row[1] for row in cursor.fetchall()}

        deck_ids = list(target_decks.keys())
        placeholders = ','.join('?' for _ in deck_ids)

        query = f"""
            SELECT DISTINCT n.id, c.did, n.mid, n.flds, n.tags,
                   c.type, c.queue, c.ivl, c.reps, c.lapses
            FROM cards c
            JOIN notes n ON c.nid = n.id
            WHERE c.did IN ({placeholders})
        """

        cursor.execute(query, deck_ids)
        rows = cursor.fetchall()
        conn.close()

        imported = 0
        updated = 0
        skipped = 0

        for row in rows:
            nid, did, mid, flds_str, tags, c_type, c_queue, c_ivl, c_reps, c_lapses = row

            status = determine_status(c_type, c_queue, c_ivl)
            field_names = field_mappings.get(mid, [])
            field_values = flds_str.split('\x1f')

            data = {}
            for i, val in enumerate(field_values):
                if i < len(field_names) and field_names[i]:
                    data[field_names[i]] = val
                else:
                    data[f"field_{i+1}"] = val

            vocab_info = extract_vocab_info(data, field_names)

            if not vocab_info.get("kana"):
                skipped += 1
                continue

            if not vocab_info.get("meaning"):
                vocab_info["meaning"] = ""

            # Skip if kana is just HTML or invalid
            if '<' in vocab_info["kana"] or len(vocab_info["kana"]) > 50:
                skipped += 1
                continue

            stmt = select(VocabEntry).where(
                VocabEntry.language_code == "ja",
                VocabEntry.anki_note_id == nid,
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.language_code = "ja"
                existing.kanji = vocab_info.get("kanji")
                existing.kana = vocab_info["kana"]
                existing.meaning = vocab_info["meaning"]
                existing.status = status
                existing.interval_days = c_ivl
                updated += 1
            else:
                entry = VocabEntry(
                    language_code="ja",
                    kanji=vocab_info.get("kanji"),
                    kana=vocab_info["kana"],
                    meaning=vocab_info["meaning"],
                    pos=vocab_info.get("pos"),
                    status=status,
                    source="anki",
                    anki_note_id=nid,
                    interval_days=c_ivl,
                )
                session.add(entry)
                imported += 1

        await session.commit()

        return {
            "imported": imported,
            "updated": updated,
            "skipped": skipped,
            "total_processed": len(rows),
            "decks_found": len(target_decks),
        }

    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


def get_field_mappings(cursor) -> Dict[int, list]:
    cursor.execute("SELECT ntid, ord, name FROM fields ORDER BY ntid, ord")
    mappings = {}
    for ntid, ord, name in cursor.fetchall():
        if ntid not in mappings:
            mappings[ntid] = []
        while len(mappings[ntid]) <= ord:
            mappings[ntid].append(None)
        mappings[ntid][ord] = name
    return mappings


def get_model_names(cursor) -> Dict[int, str]:
    cursor.execute("SELECT id, name FROM notetypes")
    return dict(cursor.fetchall())


def determine_status(c_type: int, c_queue: int, c_ivl: int) -> str:
    if c_queue < 0:
        return "Suspended"
    elif c_type == 0 or c_queue == 0:
        return "New"
    elif c_type == 1 or c_type == 3:
        return "Learning"
    elif c_type == 2:
        if c_ivl >= 21:
            return "Mature"
        else:
            return "Learning"
    return "New"


def map_status(status: str) -> str:
    """Map Anki status to our status."""
    status = status.lower() if status else "new"
    if status in ["mature", "young"]:
        return "Mature" if status == "mature" else "Learning"
    elif status == "learning":
        return "Learning"
    elif status == "new":
        return "New"
    elif status == "suspended":
        return "Suspended"
    return "New"


def has_kanji(text: str) -> bool:
    """Japanese compatibility wrapper for profile script detection."""
    return get_language_profile("ja").has_term_script(text)


def extract_vocab_info(data: Dict[str, str], field_names: list) -> Dict[str, Any]:
    kanji_fields = ['Characters', 'vocab', 'Word', 'Expression', 'Front', 'Kanji']
    kana_fields = ['Reading', 'Reading_Whitelist', 'kana', 'hiragana', 'Furigana']
    meaning_fields = ['Meaning', 'Meaning_Whitelist', 'meaning', 'English', 'Definition', 'Back']

    result = {"kanji": None, "kana": None, "meaning": None, "pos": None}

    # Find kanji/word
    for field in kanji_fields:
        if field in data and data[field].strip():
            result["kanji"] = strip_html(data[field])
            break

    # Find kana reading
    for field in kana_fields:
        if field in data and data[field].strip():
            result["kana"] = strip_html(data[field])
            break

    # If no kana found, use kanji as kana (for kana-only words)
    if not result["kana"] and result["kanji"]:
        if not has_kanji(result["kanji"]):
            result["kana"] = result["kanji"]
            result["kanji"] = None
        else:
            result["kana"] = result["kanji"]

    # Find meaning
    for field in meaning_fields:
        if field in data and data[field].strip():
            result["meaning"] = strip_html(data[field])
            break

    # Fallback
    if not result["kana"] and field_names:
        first_field = field_names[0]
        if first_field and first_field in data:
            result["kana"] = strip_html(data[first_field])

    return result


def strip_html(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()
