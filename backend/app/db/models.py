from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, func
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class VocabEntry(Base):
    __tablename__ = "vocab_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kanji = Column(String(100), nullable=True)
    kana = Column(String(100), nullable=False)
    meaning = Column(Text, nullable=False)
    pos = Column(String(50), nullable=True)  # Part of speech
    status = Column(String(20), default="New")  # New, Learning, Mature
    source = Column(String(20), default="manual")  # anki, tutor, manual
    anki_note_id = Column(Integer, nullable=True)
    interval_days = Column(Integer, default=0)
    times_seen = Column(Integer, default=0)
    times_correct = Column(Integer, default=0)
    last_seen_at = Column(DateTime, nullable=True)
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
