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
    assert codes == ["ja", "es", "fr", "ko", "zh"]


def test_only_japanese_supports_server_tts():
    assert get_language_profile("ja").supports_server_tts
    for code in ("es", "fr", "ko", "zh"):
        assert not get_language_profile(code).supports_server_tts


def test_generic_profiles_parameterize_prompts():
    es = get_language_profile("es")

    assert "You are a Spanish language tutor." in es.tutor_prompt_template
    assert "existing CEFR point" in es.listener_prompt_template
    assert "Japanese" not in es.tutor_prompt_template

    # Runtime placeholders must survive the language parameterization.
    es.tutor_prompt_template.format(
        today="2026-07-06",
        student_facts_formatted="f",
        session_summary="s",
        vocab_list_formatted="v",
        grammar_list_formatted="g",
    )
    es.memory_compaction_prompt_template.format(current_summary="c", messages_chunk="m")
    es.grammar_assessment_prompt_template.format(grammar_points="g", excerpts="e")
    es.session_title_prompt_template.format(message_preview="m")


def test_spanish_profile_stores_word_in_reading_slot():
    es = get_language_profile("es")

    normalized = es.normalize_vocab_fields("hola", "", "hello")

    assert normalized["term"] is None
    assert normalized["reading"] == "hola"
    assert es.format_vocab_item(normalized) == "- hola"
    assert not es.has_secondary_script


def test_korean_profile_detects_hangul():
    ko = get_language_profile("ko")

    assert ko.has_reading_script("안녕하세요")
    assert not ko.has_reading_script("hello")
    assert ko.normalize_vocab_fields("안녕", "", "hi")["reading"] == "안녕"


def test_mandarin_profile_keeps_hanzi_and_pinyin():
    zh = get_language_profile("zh")

    normalized = zh.normalize_vocab_fields("你好", "ni hao", "hello")

    assert normalized["term"] == "你好"
    assert normalized["reading"] == "ni hao"
    assert zh.grammar_level_scheme.levels[0] == "HSK1"
    assert zh.has_secondary_script


def test_spanish_mapping_suggestion_uses_field_names():
    es = get_language_profile("es")

    suggestion = es.suggest_anki_mapping(
        ["Word", "Meaning"],
        {"Word": ["hola", "adiós"], "Meaning": ["hello", "goodbye"]},
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
