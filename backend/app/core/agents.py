"""Compatibility exports for agent prompt templates.

Target-language-specific prompts now live in language profiles. These names are
kept so older imports and tests continue to refer to the Japanese default.
"""

from app.core.language_profiles import get_language_profile

_JAPANESE_PROFILE = get_language_profile("ja")

TUTOR_SYSTEM_PROMPT_TEMPLATE = _JAPANESE_PROFILE.tutor_prompt_template
LISTENER_SYSTEM_PROMPT_TEMPLATE = _JAPANESE_PROFILE.listener_prompt_template
