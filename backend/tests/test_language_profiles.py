from app.core.agents import TUTOR_SYSTEM_PROMPT_TEMPLATE
from app.core.language_profiles import (
    get_language_profile,
    list_language_profiles,
    normalize_language_code,
)


def test_default_profile_is_japanese_and_preserves_prompt():
    profile = get_language_profile()

    assert profile.code == "ja"
    assert profile.display_name == "Japanese"
    assert profile.speech_language == "ja-JP"
    assert "You are a Japanese language tutor." in profile.tutor_prompt_template
    assert TUTOR_SYSTEM_PROMPT_TEMPLATE == profile.tutor_prompt_template


def test_unknown_language_falls_back_to_japanese():
    assert normalize_language_code("xx") == "ja"
    assert get_language_profile("xx").code == "ja"


def test_registry_includes_generic_profiles():
    codes = [profile.code for profile in list_language_profiles()]
    assert codes == ["ja", "en", "fr"]


def test_tts_engine_assignments():
    assert get_language_profile("ja").tts_engine == "voicevox"
    assert get_language_profile("en").tts_engine == "kokoro"
    assert get_language_profile("fr").tts_engine == "kokoro"
    assert get_language_profile("ja").supports_server_tts


def test_generic_profiles_parameterize_prompts():
    fr = get_language_profile("fr")

    assert "You are a French language tutor." in fr.tutor_prompt_template
    assert "existing CEFR point" in fr.listener_prompt_template
    assert "Japanese" not in fr.tutor_prompt_template

    # Runtime placeholders must survive the language parameterization.
    fr.tutor_prompt_template.format(
        today="2026-07-06",
        student_facts_formatted="f",
        session_summary="s",
        vocab_list_formatted="v",
        grammar_list_formatted="g",
    )
    fr.memory_compaction_prompt_template.format(current_summary="c", messages_chunk="m")
    fr.grammar_assessment_prompt_template.format(grammar_points="g", excerpts="e")
    fr.session_title_prompt_template.format(message_preview="m")


def test_french_profile_stores_word_in_reading_slot():
    fr = get_language_profile("fr")

    normalized = fr.normalize_vocab_fields("bonjour", "", "hello")

    assert normalized["term"] is None
    assert normalized["reading"] == "bonjour"
    assert fr.format_vocab_item(normalized) == "- bonjour"
    assert not fr.has_secondary_script


def test_english_profile_stores_word_in_reading_slot():
    en = get_language_profile("en")

    normalized = en.normalize_vocab_fields("serendipity", "", "a fortunate accident")

    assert normalized["term"] is None
    assert normalized["reading"] == "serendipity"
    assert en.format_vocab_item(normalized) == "- serendipity"
    assert not en.has_secondary_script


def test_english_mapping_treats_english_field_as_word_not_meaning():
    en = get_language_profile("en")

    suggestion = en.suggest_anki_mapping(
        ["English", "Definition"],
        {"English": ["run", "beautiful"], "Definition": ["to move fast", "pleasing to look at"]},
    )

    assert suggestion["kana_field"] == "English"
    assert suggestion["meaning_field"] == "Definition"
    assert suggestion["kanji_field"] is None


def test_french_mapping_suggestion_uses_field_names():
    fr = get_language_profile("fr")

    suggestion = fr.suggest_anki_mapping(
        ["Word", "Meaning"],
        {"Word": ["bonjour", "au revoir"], "Meaning": ["hello", "goodbye"]},
    )

    assert suggestion["kana_field"] == "Word"
    assert suggestion["meaning_field"] == "Meaning"
    assert suggestion["kanji_field"] is None


def test_japanese_profile_exposes_jlpt_levels_and_seed_file():
    profile = get_language_profile("ja")

    assert profile.grammar_level_scheme.name == "JLPT"
    assert profile.grammar_level_scheme.levels == ["N5", "N4", "N3", "N2", "N1"]
    assert profile.grammar_seed_file.name == "jlpt_grammar_list.txt"


def test_profile_formats_japanese_vocab_as_term_and_reading():
    profile = get_language_profile("ja")

    assert profile.format_vocab_item({"term": "食べる", "reading": "たべる"}) == "- 食べる (たべる)"
    assert profile.format_vocab_item({"term": None, "reading": "これ"}) == "- これ"


def test_japanese_profile_suggests_anki_mapping_from_hints_and_content():
    profile = get_language_profile("ja")
    fields = ["Characters", "Reading", "Meaning"]
    samples = {
        "Characters": ["食べる", "飲む"],
        "Reading": ["たべる", "のむ"],
        "Meaning": ["to eat", "to drink"],
    }

    suggestion = profile.suggest_anki_mapping(fields, samples)

    assert suggestion["kanji_field"] == "Characters"
    assert suggestion["kana_field"] == "Reading"
    assert suggestion["meaning_field"] == "Meaning"
