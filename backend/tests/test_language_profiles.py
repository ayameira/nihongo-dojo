from app.core.agents import TUTOR_SYSTEM_PROMPT_TEMPLATE
from app.core.language_profiles import get_language_profile, normalize_language_code


def test_default_profile_is_japanese_and_preserves_prompt():
    profile = get_language_profile()

    assert profile.code == "ja"
    assert profile.display_name == "Japanese"
    assert profile.speech_language == "ja-JP"
    assert "You are a Japanese language tutor." in profile.tutor_prompt_template
    assert TUTOR_SYSTEM_PROMPT_TEMPLATE == profile.tutor_prompt_template


def test_unknown_language_falls_back_to_japanese():
    assert normalize_language_code("es") == "ja"
    assert get_language_profile("es").code == "ja"


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
