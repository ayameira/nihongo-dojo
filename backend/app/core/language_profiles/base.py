from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class GrammarLevelScheme:
    name: str
    levels: List[str]
    source_name: str
    custom_label: str = "Custom"


@dataclass(frozen=True)
class VocabularyDisplaySemantics:
    term_label: str
    reading_label: str
    meaning_label: str
    part_of_speech_label: str


@dataclass(frozen=True)
class AnkiFieldHints:
    term: List[str]
    reading: List[str]
    meaning: List[str]
    part_of_speech: List[str]


@dataclass(frozen=True)
class LanguageProfile:
    code: str
    display_name: str
    native_name: str
    speech_language: str
    tutor_prompt_template: str
    listener_prompt_template: str
    memory_compaction_prompt_template: str
    grammar_assessment_prompt_template: str
    session_title_prompt_template: str
    grammar_level_scheme: GrammarLevelScheme
    grammar_seed_file: Optional[Path]
    vocabulary_semantics: VocabularyDisplaySemantics
    anki_field_hints: AnkiFieldHints
    has_term_script: Callable[[str], bool]
    has_reading_script: Callable[[str], bool]
    is_translation_text: Callable[[str], bool]
    # Server-side TTS engine for this language: "voicevox" (Japanese) or
    # "kokoro" (Kokoro-FastAPI). None means only the browser's Web Speech
    # API is available.
    tts_engine: Optional[str] = None
    # Whether the language keeps a secondary written form next to the primary
    # one (kanji next to kana, hanzi next to pinyin). Languages without one
    # store the word in the reading slot and hide the term field in the UI.
    has_secondary_script: bool = True

    @property
    def supports_server_tts(self) -> bool:
        return self.tts_engine is not None

    def format_vocab_item(self, item: Dict[str, Optional[str]]) -> str:
        term = item.get("term") or item.get("kanji") or ""
        reading = item.get("reading") or item.get("kana") or ""
        if term and reading and term != reading:
            return f"- {term} ({reading})"
        return f"- {reading or term}"

    def normalize_vocab_fields(
        self,
        term: str,
        reading: str,
        meaning: str,
        part_of_speech: Optional[str] = None,
    ) -> Dict[str, Optional[str]]:
        normalized_term = term.strip()
        normalized_reading = reading.strip()

        if normalized_term and not self.has_term_script(normalized_term):
            if not normalized_reading:
                normalized_reading = normalized_term
            normalized_term = ""

        if not normalized_reading and normalized_term:
            normalized_reading = normalized_term

        return {
            "term": normalized_term or None,
            "reading": normalized_reading or None,
            "meaning": meaning.strip(),
            "part_of_speech": (part_of_speech or "").strip() or None,
        }

    def suggest_anki_mapping(
        self,
        field_names: List[str],
        samples: Dict[str, List[str]],
    ) -> Dict[str, Optional[str]]:
        def normalized_name(name: str) -> str:
            return name.lower().replace(" ", "_")

        def by_name(hints: Iterable[str]) -> Optional[str]:
            for hint in hints:
                for name in field_names:
                    if hint == normalized_name(name):
                        return name
            for hint in hints:
                for name in field_names:
                    if hint in normalized_name(name):
                        return name
            return None

        suggestion: Dict[str, Optional[str]] = {
            "kanji_field": by_name(self.anki_field_hints.term),
            "kana_field": by_name(self.anki_field_hints.reading),
            "meaning_field": by_name(self.anki_field_hints.meaning),
            "pos_field": by_name(self.anki_field_hints.part_of_speech),
        }

        profiles: Dict[str, Dict[str, float]] = {}
        for name in field_names:
            values = [_strip_html(v) for v in samples.get(name, []) if _strip_html(v)]
            if not values:
                profiles[name] = {"term": 0, "reading": 0, "translation": 0}
                continue
            profiles[name] = {
                "term": sum(self.has_term_script(v) for v in values) / len(values),
                "reading": sum(self.has_reading_script(v) for v in values) / len(values),
                "translation": sum(self.is_translation_text(v) for v in values) / len(values),
            }

        taken = {value for value in suggestion.values() if value}

        if not suggestion["meaning_field"]:
            best = max(
                (name for name in field_names if name not in taken),
                key=lambda name: profiles[name]["translation"],
                default=None,
            )
            if best and profiles[best]["translation"] > 0.5:
                suggestion["meaning_field"] = best
                taken.add(best)

        if not suggestion["kanji_field"]:
            best = max(
                (name for name in field_names if name not in taken),
                key=lambda name: profiles[name]["term"],
                default=None,
            )
            if best and profiles[best]["term"] > 0.3:
                suggestion["kanji_field"] = best
                taken.add(best)

        if not suggestion["kana_field"]:
            best = max(
                (name for name in field_names if name not in taken),
                key=lambda name: profiles[name]["reading"] - profiles[name]["term"],
                default=None,
            )
            if best and profiles[best]["reading"] > 0.3:
                suggestion["kana_field"] = best
                taken.add(best)

        if not suggestion["kana_field"] and suggestion["kanji_field"]:
            suggestion["kana_field"] = suggestion["kanji_field"]

        return suggestion


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _has_kanji(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text or "")


def _has_kana(text: str) -> bool:
    return any("\u3040" <= ch <= "\u30ff" for ch in text or "")


def _never(text: str) -> bool:
    """For languages whose word and translation share a script, content
    sniffing cannot tell them apart; mapping relies on field-name hints."""
    return False


def _is_mostly_latin(text: str) -> bool:
    letters = [ch for ch in text or "" if ch.isalpha()]
    if not letters:
        return False
    latin = sum(1 for ch in letters if ch.isascii())
    return latin / len(letters) > 0.6


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


JAPANESE_TUTOR_SYSTEM_PROMPT_TEMPLATE = """Current Date: {today}

You are a Japanese language tutor.

## Core Principles
- Push the student to the edge of their ability (i+1 hypothesis). Finding out exactly where their level is and acting accordingly is your most crucial task.
- Use vocabulary the student is currently learning when possible
- Incorporate grammar patterns the student is currently learning into your examples and practice sentences
- Repetition is key for learning: use the same vocabulary and grammatical constructions that the user is currently learning or has been struggling with. However, always use it in new phrases and contexts. Repetition can also be boring.

## About This Student
{student_facts_formatted}

## Conversation Summary (This Session)
{session_summary}

## Vocabulary Currently Being Learned
{vocab_list_formatted}

## Grammar Points Currently Being Learned
{grammar_list_formatted}

## Instructions for Difficulty
- If user says something is "too hard", simplify slightly but don't overcompensate
- If user says something is "too easy", increase complexity gradually
"""


JAPANESE_LISTENER_SYSTEM_PROMPT_TEMPLATE = """You are a silent observer for a Japanese tutoring application.
Your job is to:
1. Extract and manage facts about the student based on their conversation
2. Manage grammar points when the student explicitly requests changes, or when the exchange clearly shows the tutor introduced a concrete grammar point the student should keep practicing

## Current Student Facts (with IDs for reference)
{student_facts_formatted}

## Current Learning Grammar (with IDs for reference)
{learning_grammar_formatted}

## Conversation Exchange
Tutor: {tutor_message}
Student: {user_message}

## Task
Analyze the student's message in context of the tutor's question.

### Fact Management (manage_student_facts tool)
If needed:
- add: New permanent info about the student (goals, interests, background, preferences, learning style)
- edit: Update an existing fact if new information contradicts or refines it (provide fact_id)
- delete: Remove a fact that is no longer accurate (provide fact_id)

### Grammar Management (manage_grammar tool)
If the student explicitly asks to add a grammar point to their study list, or asks to mark one as learned/burned:
- Use manage_grammar with action "add" to create a new grammar point
- Use manage_grammar with action "update_status" to change status (New/Learning/Burned)

If the tutor introduces or corrects a specific grammar pattern and the student appears to be learning it now:
- Use manage_grammar with action "start_learning"
- Include the exact Japanese pattern and a concise English meaning
- Include brief notes when the conversation contained a useful correction or example
- This will mark an existing JLPT point as Learning if it already exists, or create a custom Learning point when it is absent

If NO changes are needed, do not call any tools.

## Important Rules
- Extract PERMANENT facts about the student as a person
- Record the grammar points the student is currently learning
- Record the issues the student is struggling with
- Only add inferred grammar when there is a concrete grammar pattern, not for broad topics or incidental phrases
- Do not add duplicate grammar points already listed as Learning unless you are adding genuinely useful notes
- Keep facts non-redundant to spare context window
"""


JAPANESE_COMPACTION_PROMPT_TEMPLATE = """You are the Memory Manager for Nihongo Dojo, a Japanese language tutoring application.

I will provide you with:
1. A 'Current Conversation Summary' (may be empty if this is the first compaction)
2. A 'Recent Chunk' of 10 messages from the conversation

## Task 1: Recursive Summarization
Update the 'Current Conversation Summary' to include the key events and topics from the 'Recent Chunk'.
- Keep it concise but specific
- Include details like grammar points practiced, vocabulary themes, corrections made
- Example: "User practiced Te-form verbs (tabete, nonde). Discussed travel plans to Tokyo. Corrected wa vs ga usage."

## Task 2: Fact Extraction
Did the user reveal any NEW permanent information about themselves in this chunk?
This includes:
- Biography (job, location, family)
- Language learning goals
- Interests and hobbies
- Dislikes or preferences
- Background context

If yes, extract it clearly. If no new facts, return null.

## Current Conversation Summary
{current_summary}

## Recent Chunk (10 messages)
{messages_chunk}

## Output Format
Return ONLY valid JSON:
{{"new_summary": "Updated comprehensive summary...", "new_student_facts": "New facts about the student..." or null}}"""


JAPANESE_ASSESSMENT_PROMPT_TEMPLATE = """You are evaluating a Japanese language student's proficiency with specific grammar points.

For each grammar point below, I will show you relevant excerpts from the student's conversations where they used (or attempted to use) the grammar.

Evaluate each grammar point and return a JSON response with your assessments.

## Grammar Points to Assess
{grammar_points}

## Relevant Conversation Excerpts
{excerpts}

## Output Format
Return ONLY valid JSON:
{{
  "assessments": [
    {{
      "grammar_id": <id>,
      "pattern": "<pattern>",
      "proficiency": "beginner" | "developing" | "proficient" | "mastered",
      "times_used_correctly": <count>,
      "times_used_incorrectly": <count>,
      "recommendation": "keep_learning" | "promote_to_burned" | "demote_to_new",
      "reasoning": "<brief explanation>"
    }}
  ]
}}

Proficiency levels:
- beginner: Student has barely used it or uses it incorrectly most of the time
- developing: Student uses it sometimes correctly but still makes mistakes
- proficient: Student uses it correctly most of the time with minor errors
- mastered: Student uses it consistently and naturally in varied contexts

Recommendations:
- keep_learning: Student is making progress but needs more practice
- promote_to_burned: Student has mastered this grammar point
- demote_to_new: Student is struggling and may need to re-learn basics
"""


JAPANESE_TITLE_PROMPT_TEMPLATE = """Generate a very short title (3-6 words) for a Japanese learning chat session that starts with this message:

"{message_preview}"

The title should:
- Be in English
- Capture the main topic or question
- Be concise and descriptive
- Not include quotes or punctuation at the end

Return JSON: {{"title": "your title here"}}"""


JAPANESE_PROFILE = LanguageProfile(
    code="ja",
    display_name="Japanese",
    native_name="日本語",
    speech_language="ja-JP",
    tts_engine="voicevox",
    tutor_prompt_template=JAPANESE_TUTOR_SYSTEM_PROMPT_TEMPLATE,
    listener_prompt_template=JAPANESE_LISTENER_SYSTEM_PROMPT_TEMPLATE,
    memory_compaction_prompt_template=JAPANESE_COMPACTION_PROMPT_TEMPLATE,
    grammar_assessment_prompt_template=JAPANESE_ASSESSMENT_PROMPT_TEMPLATE,
    session_title_prompt_template=JAPANESE_TITLE_PROMPT_TEMPLATE,
    grammar_level_scheme=GrammarLevelScheme(
        name="JLPT",
        levels=["N5", "N4", "N3", "N2", "N1"],
        source_name="jlpt",
    ),
    grammar_seed_file=_repo_root() / "jlpt_grammar_list.txt",
    vocabulary_semantics=VocabularyDisplaySemantics(
        term_label="term",
        reading_label="reading",
        meaning_label="meaning",
        part_of_speech_label="part of speech",
    ),
    anki_field_hints=AnkiFieldHints(
        term=["characters", "vocab", "word", "expression", "kanji", "front", "japanese", "sentence"],
        reading=["reading", "reading_whitelist", "kana", "hiragana", "furigana", "pronunciation"],
        meaning=["meaning", "meaning_whitelist", "english", "definition", "translation", "back", "gloss"],
        part_of_speech=["pos", "part_of_speech", "speech_type", "word_type", "type"],
    ),
    has_term_script=_has_kanji,
    has_reading_script=_has_kana,
    is_translation_text=_is_mostly_latin,
)


# ---------------------------------------------------------------------------
# Generic profiles
#
# Japanese keeps its bespoke prompt wording above; every other language gets
# the same prompts parameterized by language and grammar-scheme name.
# ---------------------------------------------------------------------------


def _generic_tutor_prompt(language: str) -> str:
    return f"""Current Date: {{today}}

You are a {language} language tutor.

## Core Principles
- Conduct the practice in {language}. Use English for explanations and translations when the student needs help, but never switch the practice itself to another language, even if the student's profile mentions studying other languages.
- Push the student to the edge of their ability (i+1 hypothesis). Finding out exactly where their level is and acting accordingly is your most crucial task.
- Use vocabulary the student is currently learning when possible
- Incorporate grammar patterns the student is currently learning into your examples and practice sentences
- Repetition is key for learning: use the same vocabulary and grammatical constructions that the user is currently learning or has been struggling with. However, always use it in new phrases and contexts. Repetition can also be boring.

## About This Student
{{student_facts_formatted}}

## Conversation Summary (This Session)
{{session_summary}}

## Vocabulary Currently Being Learned
{{vocab_list_formatted}}

## Grammar Points Currently Being Learned
{{grammar_list_formatted}}

## Instructions for Difficulty
- If user says something is "too hard", simplify slightly but don't overcompensate
- If user says something is "too easy", increase complexity gradually
"""


def _generic_listener_prompt(language: str, scheme_name: str) -> str:
    return f"""You are a silent observer for a {language} tutoring application.
Your job is to:
1. Extract and manage facts about the student based on their conversation
2. Manage grammar points when the student explicitly requests changes, or when the exchange clearly shows the tutor introduced a concrete grammar point the student should keep practicing

## Current Student Facts (with IDs for reference)
{{student_facts_formatted}}

## Current Learning Grammar (with IDs for reference)
{{learning_grammar_formatted}}

## Conversation Exchange
Tutor: {{tutor_message}}
Student: {{user_message}}

## Task
Analyze the student's message in context of the tutor's question.

### Fact Management (manage_student_facts tool)
If needed:
- add: New permanent info about the student (goals, interests, background, preferences, learning style)
- edit: Update an existing fact if new information contradicts or refines it (provide fact_id)
- delete: Remove a fact that is no longer accurate (provide fact_id)

### Grammar Management (manage_grammar tool)
If the student explicitly asks to add a grammar point to their study list, or asks to mark one as learned/burned:
- Use manage_grammar with action "add" to create a new grammar point
- Use manage_grammar with action "update_status" to change status (New/Learning/Burned)

If the tutor introduces or corrects a specific grammar pattern and the student appears to be learning it now:
- Use manage_grammar with action "start_learning"
- Include the exact {language} pattern and a concise English meaning
- Include brief notes when the conversation contained a useful correction or example
- This will mark an existing {scheme_name} point as Learning if it already exists, or create a custom Learning point when it is absent

If NO changes are needed, do not call any tools.

## Important Rules
- Extract PERMANENT facts about the student as a person
- Record the grammar points the student is currently learning
- Record the issues the student is struggling with
- Only add inferred grammar when there is a concrete grammar pattern, not for broad topics or incidental phrases
- Do not add duplicate grammar points already listed as Learning unless you are adding genuinely useful notes
- Keep facts non-redundant to spare context window
"""


def _generic_compaction_prompt(language: str) -> str:
    return f"""You are the Memory Manager for a {language} language tutoring application.

I will provide you with:
1. A 'Current Conversation Summary' (may be empty if this is the first compaction)
2. A 'Recent Chunk' of 10 messages from the conversation

## Task 1: Recursive Summarization
Update the 'Current Conversation Summary' to include the key events and topics from the 'Recent Chunk'.
- Keep it concise but specific
- Include details like grammar points practiced, vocabulary themes, corrections made
- Example: "User practiced past-tense verbs. Discussed weekend travel plans. Corrected recurring word-order mistakes."

## Task 2: Fact Extraction
Did the user reveal any NEW permanent information about themselves in this chunk?
This includes:
- Biography (job, location, family)
- Language learning goals
- Interests and hobbies
- Dislikes or preferences
- Background context

If yes, extract it clearly. If no new facts, return null.

## Current Conversation Summary
{{current_summary}}

## Recent Chunk (10 messages)
{{messages_chunk}}

## Output Format
Return ONLY valid JSON:
{{{{"new_summary": "Updated comprehensive summary...", "new_student_facts": "New facts about the student..." or null}}}}"""


def _generic_assessment_prompt(language: str) -> str:
    return f"""You are evaluating a {language} language student's proficiency with specific grammar points.

For each grammar point below, I will show you relevant excerpts from the student's conversations where they used (or attempted to use) the grammar.

Evaluate each grammar point and return a JSON response with your assessments.

## Grammar Points to Assess
{{grammar_points}}

## Relevant Conversation Excerpts
{{excerpts}}

## Output Format
Return ONLY valid JSON:
{{{{
  "assessments": [
    {{{{
      "grammar_id": <id>,
      "pattern": "<pattern>",
      "proficiency": "beginner" | "developing" | "proficient" | "mastered",
      "times_used_correctly": <count>,
      "times_used_incorrectly": <count>,
      "recommendation": "keep_learning" | "promote_to_burned" | "demote_to_new",
      "reasoning": "<brief explanation>"
    }}}}
  ]
}}}}

Proficiency levels:
- beginner: Student has barely used it or uses it incorrectly most of the time
- developing: Student uses it sometimes correctly but still makes mistakes
- proficient: Student uses it correctly most of the time with minor errors
- mastered: Student uses it consistently and naturally in varied contexts

Recommendations:
- keep_learning: Student is making progress but needs more practice
- promote_to_burned: Student has mastered this grammar point
- demote_to_new: Student is struggling and may need to re-learn basics
"""


def _generic_title_prompt(language: str) -> str:
    return f"""Generate a very short title (3-6 words) for a {language} learning chat session that starts with this message:

"{{message_preview}}"

The title should:
- Be in English
- Capture the main topic or question
- Be concise and descriptive
- Not include quotes or punctuation at the end

Return JSON: {{{{"title": "your title here"}}}}"""


_MEANING_FIELD_HINTS = ["meaning", "meaning_whitelist", "english", "definition", "translation", "back", "gloss"]
_POS_FIELD_HINTS = ["pos", "part_of_speech", "speech_type", "word_type", "type"]

CEFR_SCHEME = GrammarLevelScheme(
    name="CEFR",
    levels=["A1", "A2", "B1", "B2", "C1", "C2"],
    source_name="cefr",
)


def _make_profile(
    *,
    code: str,
    display_name: str,
    native_name: str,
    speech_language: str,
    grammar_level_scheme: GrammarLevelScheme,
    vocabulary_semantics: VocabularyDisplaySemantics,
    anki_field_hints: AnkiFieldHints,
    has_term_script: Callable[[str], bool] = _never,
    has_reading_script: Callable[[str], bool] = _is_mostly_latin,
    is_translation_text: Callable[[str], bool] = _is_mostly_latin,
    grammar_seed_file: Optional[Path] = None,
    tts_engine: Optional[str] = None,
    has_secondary_script: bool = True,
) -> LanguageProfile:
    """Build a profile that uses the generic prompt templates."""
    return LanguageProfile(
        code=code,
        display_name=display_name,
        native_name=native_name,
        speech_language=speech_language,
        tutor_prompt_template=_generic_tutor_prompt(display_name),
        listener_prompt_template=_generic_listener_prompt(display_name, grammar_level_scheme.name),
        memory_compaction_prompt_template=_generic_compaction_prompt(display_name),
        grammar_assessment_prompt_template=_generic_assessment_prompt(display_name),
        session_title_prompt_template=_generic_title_prompt(display_name),
        grammar_level_scheme=grammar_level_scheme,
        grammar_seed_file=grammar_seed_file,
        vocabulary_semantics=vocabulary_semantics,
        anki_field_hints=anki_field_hints,
        has_term_script=has_term_script,
        has_reading_script=has_reading_script,
        is_translation_text=is_translation_text,
        tts_engine=tts_engine,
        has_secondary_script=has_secondary_script,
    )


ENGLISH_PROFILE = _make_profile(
    code="en",
    display_name="English",
    native_name="English",
    speech_language="en-US",
    tts_engine="kokoro",
    grammar_level_scheme=CEFR_SCHEME,
    vocabulary_semantics=VocabularyDisplaySemantics(
        term_label="word",
        reading_label="word",
        meaning_label="meaning",
        part_of_speech_label="part of speech",
    ),
    anki_field_hints=AnkiFieldHints(
        term=[],
        reading=["word", "english", "expression", "vocab", "front", "term"],
        # No "english" here: in an English deck that field holds the word
        # being learned, not its meaning.
        meaning=["meaning", "meaning_whitelist", "definition", "translation", "back", "gloss"],
        part_of_speech=_POS_FIELD_HINTS,
    ),
    has_secondary_script=False,
)


FRENCH_PROFILE = _make_profile(
    code="fr",
    display_name="French",
    native_name="Français",
    speech_language="fr-FR",
    tts_engine="kokoro",
    grammar_level_scheme=CEFR_SCHEME,
    vocabulary_semantics=VocabularyDisplaySemantics(
        term_label="word",
        reading_label="word",
        meaning_label="meaning",
        part_of_speech_label="part of speech",
    ),
    anki_field_hints=AnkiFieldHints(
        term=[],
        reading=["word", "french", "expression", "vocab", "front", "term"],
        meaning=_MEANING_FIELD_HINTS,
        part_of_speech=_POS_FIELD_HINTS,
    ),
    has_secondary_script=False,
)


_PROFILES: Dict[str, LanguageProfile] = {
    profile.code: profile
    for profile in (
        JAPANESE_PROFILE,
        ENGLISH_PROFILE,
        FRENCH_PROFILE,
    )
}


def normalize_language_code(language_code: Optional[str]) -> str:
    code = (language_code or "ja").strip().lower()
    return code if code in _PROFILES else "ja"


def get_language_profile(language_code: Optional[str] = None) -> LanguageProfile:
    return _PROFILES[normalize_language_code(language_code)]


def get_active_language_profile() -> LanguageProfile:
    from app.config import get_settings

    return get_language_profile(get_settings().target_language_code)


def list_language_profiles() -> List[LanguageProfile]:
    return list(_PROFILES.values())
