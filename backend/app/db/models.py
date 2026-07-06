from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class VocabEntry(Base):
    __tablename__ = "vocab_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    language_code = Column(String(10), default="ja", nullable=False, index=True)
    kanji = Column(String(100), nullable=True)
    kana = Column(String(100), nullable=False)
    meaning = Column(Text, nullable=False)
    pos = Column(String(50), nullable=True)  # Part of speech
    status = Column(String(20), default="New")  # New, Learning, Mature
    source = Column(String(20), default="manual")  # anki, tutor, manual
    anki_note_id = Column(Integer, nullable=True)
    # Which Anki deck source this entry was imported from (null for manual/tutor)
    deck_config_id = Column(Integer, ForeignKey("anki_deck_configs.id"), nullable=True, index=True)
    interval_days = Column(Integer, default=0)
    times_seen = Column(Integer, default=0)
    times_correct = Column(Integer, default=0)
    last_seen_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AnkiDeckConfig(Base):
    """A configured Anki deck source: which collection, which deck, and how its
    note fields map onto Nihongo Dojo's vocabulary fields."""
    __tablename__ = "anki_deck_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    language_code = Column(String(10), default="ja", nullable=False, index=True)
    name = Column(String(255), nullable=False)  # user-facing label
    collection_path = Column(String(500), nullable=False)  # path to a collection.anki2
    deck_name = Column(String(255), nullable=False)  # exact Anki deck name
    enabled = Column(Boolean, default=True)

    # Field mappings (Anki note field name -> Nihongo Dojo field)
    kanji_field = Column(String(255), nullable=True)
    kana_field = Column(String(255), nullable=False)
    meaning_field = Column(String(255), nullable=False)
    pos_field = Column(String(255), nullable=True)

    # Optional note filter: only import notes where filter_field == filter_value
    filter_field = Column(String(255), nullable=True)
    filter_value = Column(String(255), nullable=True)

    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    image_data = Column(Text, nullable=True)  # Base64 encoded
    token_count = Column(Integer, default=0)
    is_archived = Column(Boolean, default=False, index=True)  # For memory compaction
    created_at = Column(DateTime, default=func.now())


class TokenLog(Base):
    __tablename__ = "token_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), nullable=False, index=True)
    model = Column(String(50), nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    image_count = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(50), primary_key=True)
    language_code = Column(String(10), default="ja", nullable=False, index=True)
    name = Column(String(200), nullable=True)
    preview = Column(String(100), nullable=True)
    message_count = Column(Integer, default=0)
    summary = Column(Text, nullable=True)  # Compacted conversation summary
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class StudentFact(Base):
    __tablename__ = "student_facts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Every fact belongs to one language room; legacy NULLs are migrated to "ja".
    language_code = Column(String(10), default="ja", nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String(20), default="tutor")  # "tutor" or "compaction"
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class GrammarEntry(Base):
    __tablename__ = "grammar_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    language_code = Column(String(10), default="ja", nullable=False, index=True)
    pattern = Column(String(200), nullable=False)  # e.g. "ている", "が 1"
    meaning = Column(Text, nullable=False)  # English meaning
    jlpt_level = Column(String(20), nullable=True)  # profile grammar level ("N5", "A1", "TOPIK1", ...), null for custom
    status = Column(String(20), default="New")  # "New" | "Learning" | "Burned"
    source = Column(String(20), default="jlpt")  # "jlpt" | "manual" | "tutor"
    notes = Column(Text, nullable=True)  # Usage notes from user/AI
    times_seen = Column(Integer, default=0)
    times_correct = Column(Integer, default=0)
    last_assessed_at = Column(DateTime, nullable=True)  # Prevents re-assessment within cooldown
    last_seen_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
