"""Read-only introspection of Anki collections.

Used by the Anki setup wizard to discover decks, note types and their fields
without committing anything to the app database. Also provides best-guess field
mappings so the wizard can pre-fill the mapping step.
"""
import os
import re
import shutil
import sqlite3
import tempfile
import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)

# Field-name heuristics, ordered by preference. Re-used to pre-fill the wizard.
KANJI_FIELD_HINTS = ["characters", "vocab", "word", "expression", "kanji", "front", "japanese", "sentence"]
KANA_FIELD_HINTS = ["reading", "reading_whitelist", "kana", "hiragana", "furigana", "pronunciation"]
MEANING_FIELD_HINTS = ["meaning", "meaning_whitelist", "english", "definition", "translation", "back", "gloss"]
POS_FIELD_HINTS = ["pos", "part_of_speech", "speech_type", "word_type", "type"]


def default_collection_path() -> str:
    """Best-guess path to an Anki collection for the current platform."""
    import sys

    home = os.path.expanduser("~")
    if sys.platform == "darwin":
        base = os.path.join(home, "Library", "Application Support", "Anki2")
    elif sys.platform.startswith("win"):
        base = os.path.join(os.environ.get("APPDATA", home), "Anki2")
    else:
        base = os.path.join(home, ".local", "share", "Anki2")

    # Prefer a real profile directory if one exists, else fall back to "User 1".
    if os.path.isdir(base):
        for entry in sorted(os.listdir(base)):
            candidate = os.path.join(base, entry, "collection.anki2")
            if os.path.exists(candidate):
                return candidate
    return os.path.join(base, "User 1", "collection.anki2")


@contextmanager
def open_collection(path: str) -> Iterator[sqlite3.Connection]:
    """Open a copy of an Anki collection so we never lock the user's live file."""
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Anki collection not found: {path}")

    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "collection.anki2")
    try:
        shutil.copy2(path, temp_db)
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        conn.create_collation(
            "unicase", lambda x, y: (x.lower() > y.lower()) - (x.lower() < y.lower())
        )
        try:
            yield conn
        finally:
            conn.close()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _field_mappings(cursor) -> Dict[int, List[Optional[str]]]:
    """Map note-type id -> ordered list of field names."""
    cursor.execute("SELECT ntid, ord, name FROM fields ORDER BY ntid, ord")
    mappings: Dict[int, List[Optional[str]]] = {}
    for ntid, ord_, name in cursor.fetchall():
        slots = mappings.setdefault(ntid, [])
        while len(slots) <= ord_:
            slots.append(None)
        slots[ord_] = name
    return mappings


def _model_names(cursor) -> Dict[int, str]:
    cursor.execute("SELECT id, name FROM notetypes")
    return dict(cursor.fetchall())


def _deck_match(deck_name: str):
    """SQL fragment + params matching a deck and all of its subdecks."""
    return "(d.name = ? OR d.name LIKE ?)", [deck_name, f"{deck_name}::%"]


def list_decks(path: str) -> List[Dict[str, Any]]:
    """List every deck in the collection with a note count (subdecks included)."""
    with open_collection(path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM decks ORDER BY name")
        decks = [(row[0], row[1]) for row in cursor.fetchall()]

        result = []
        for deck_id, name in decks:
            if name == "Default":
                # Skip Anki's empty Default deck unless it actually has cards.
                cursor.execute(
                    "SELECT COUNT(DISTINCT c.nid) FROM cards c WHERE c.did = ?",
                    [deck_id],
                )
                if cursor.fetchone()[0] == 0:
                    continue
            clause, params = _deck_match(name)
            cursor.execute(
                f"""
                SELECT COUNT(DISTINCT c.nid)
                FROM cards c
                JOIN decks d ON c.did = d.id
                WHERE {clause}
                """,
                params,
            )
            note_count = cursor.fetchone()[0]
            if note_count:
                result.append({"deck_name": name, "note_count": note_count})
        return result


def read_deck_notes(path: str, deck_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Read notes for a deck (and its subdecks) as plain dicts.

    Each item: anki_note_id, model_name, field_order, fields, c_type, c_queue, c_ivl.
    """
    with open_collection(path) as conn:
        cursor = conn.cursor()
        field_mappings = _field_mappings(cursor)
        model_names = _model_names(cursor)

        clause, params = _deck_match(deck_name)
        query = f"""
            SELECT DISTINCT n.id, n.mid, n.flds, c.type, c.queue, c.ivl
            FROM cards c
            JOIN notes n ON c.nid = n.id
            JOIN decks d ON c.did = d.id
            WHERE {clause}
        """
        if limit:
            query += f" LIMIT {int(limit)}"
        cursor.execute(query, params)

        notes = []
        for nid, mid, flds_str, c_type, c_queue, c_ivl in cursor.fetchall():
            field_names = field_mappings.get(mid, [])
            field_values = flds_str.split("\x1f")
            order: List[str] = []
            fields: Dict[str, str] = {}
            for i, val in enumerate(field_values):
                name = field_names[i] if i < len(field_names) and field_names[i] else f"Field {i + 1}"
                order.append(name)
                fields[name] = val
            notes.append({
                "anki_note_id": nid,
                "model_name": model_names.get(mid, "Unknown"),
                "field_order": order,
                "fields": fields,
                "c_type": c_type,
                "c_queue": c_queue,
                "c_ivl": c_ivl,
            })
        return notes


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _has_kanji(text: str) -> bool:
    return any("一" <= ch <= "鿿" for ch in text or "")


def _has_kana(text: str) -> bool:
    return any("぀" <= ch <= "ヿ" for ch in text or "")


def _is_mostly_latin(text: str) -> bool:
    letters = [ch for ch in text or "" if ch.isalpha()]
    if not letters:
        return False
    latin = sum(1 for ch in letters if ch.isascii())
    return latin / len(letters) > 0.6


def suggest_mapping(field_names: List[str], samples: Dict[str, List[str]]) -> Dict[str, Optional[str]]:
    """Best-guess field mapping from field names plus a few sample values.

    Names are matched against the hint lists first; if that is inconclusive the
    sample content is sniffed (kanji vs. kana vs. latin text).
    """
    def by_name(hints: List[str]) -> Optional[str]:
        for hint in hints:
            for name in field_names:
                if hint == name.lower().replace(" ", "_"):
                    return name
        for hint in hints:
            for name in field_names:
                if hint in name.lower().replace(" ", "_"):
                    return name
        return None

    suggestion: Dict[str, Optional[str]] = {
        "kanji_field": by_name(KANJI_FIELD_HINTS),
        "kana_field": by_name(KANA_FIELD_HINTS),
        "meaning_field": by_name(MEANING_FIELD_HINTS),
        "pos_field": by_name(POS_FIELD_HINTS),
    }

    # Content sniffing to fill any gaps the name heuristics missed.
    profiles: Dict[str, Dict[str, float]] = {}
    for name in field_names:
        values = [_strip_html(v) for v in samples.get(name, []) if _strip_html(v)]
        if not values:
            profiles[name] = {"kanji": 0, "kana": 0, "latin": 0}
            continue
        profiles[name] = {
            "kanji": sum(_has_kanji(v) for v in values) / len(values),
            "kana": sum(_has_kana(v) for v in values) / len(values),
            "latin": sum(_is_mostly_latin(v) for v in values) / len(values),
        }

    taken = {v for v in suggestion.values() if v}

    if not suggestion["meaning_field"]:
        best = max(
            (n for n in field_names if n not in taken),
            key=lambda n: profiles[n]["latin"],
            default=None,
        )
        if best and profiles[best]["latin"] > 0.5:
            suggestion["meaning_field"] = best
            taken.add(best)

    if not suggestion["kanji_field"]:
        best = max(
            (n for n in field_names if n not in taken),
            key=lambda n: profiles[n]["kanji"],
            default=None,
        )
        if best and profiles[best]["kanji"] > 0.3:
            suggestion["kanji_field"] = best
            taken.add(best)

    if not suggestion["kana_field"]:
        best = max(
            (n for n in field_names if n not in taken),
            key=lambda n: profiles[n]["kana"] - profiles[n]["kanji"],
            default=None,
        )
        if best and profiles[best]["kana"] > 0.3:
            suggestion["kana_field"] = best
            taken.add(best)

    # A deck may be kana-only (no kanji field). In that case the kana field can
    # fall back to whatever holds the Japanese word.
    if not suggestion["kana_field"] and suggestion["kanji_field"]:
        suggestion["kana_field"] = suggestion["kanji_field"]

    return suggestion


def get_deck_fields(path: str, deck_name: str, sample_size: int = 8) -> Dict[str, Any]:
    """Inspect a deck's note types, their fields, sample values and a suggested
    field mapping for the wizard's mapping step."""
    notes = read_deck_notes(path, deck_name)
    if not notes:
        return {"deck_name": deck_name, "note_count": 0, "note_types": [], "suggested": {}}

    # Group notes by note type so a deck with mixed note types is handled cleanly.
    by_model: Dict[str, List[Dict[str, Any]]] = {}
    for note in notes:
        by_model.setdefault(note["model_name"], []).append(note)

    note_types = []
    for model_name, model_notes in by_model.items():
        field_order = model_notes[0]["field_order"]
        samples: Dict[str, List[str]] = {name: [] for name in field_order}
        for note in model_notes[:sample_size]:
            for name in field_order:
                samples[name].append(note["fields"].get(name, ""))
        note_types.append({
            "model_name": model_name,
            "note_count": len(model_notes),
            "fields": field_order,
            "samples": [
                {name: _strip_html(note["fields"].get(name, "")) for name in field_order}
                for note in model_notes[:sample_size]
            ],
        })

    # Suggest a mapping from the dominant (largest) note type.
    dominant = max(note_types, key=lambda nt: nt["note_count"])
    dom_samples: Dict[str, List[str]] = {name: [] for name in dominant["fields"]}
    for row in dominant["samples"]:
        for name, val in row.items():
            dom_samples[name].append(val)
    suggested = suggest_mapping(dominant["fields"], dom_samples)

    return {
        "deck_name": deck_name,
        "note_count": len(notes),
        "note_types": note_types,
        "suggested": suggested,
    }
