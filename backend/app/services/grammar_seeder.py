"""Grammar seeder service - parses JLPT grammar list and seeds the database."""

import re
import logging
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import GrammarEntry
from app.core.language_profiles import get_language_profile, normalize_language_code

logger = logging.getLogger(__name__)

# Path to grammar list file (relative to backend/ directory)
GRAMMAR_FILE = get_language_profile("ja").grammar_seed_file


async def seed_grammar_from_file(
    session: AsyncSession,
    file_path: Path = None,
    language_code: str | None = None,
) -> dict:
    """Parse the active profile's grammar seed file and seed grammar entries.

    Args:
        session: Database session
        file_path: Optional path override (defaults to GRAMMAR_FILE)

    Returns:
        Dict with count of entries inserted
    """
    language_code = normalize_language_code(language_code)
    profile = get_language_profile(language_code)
    path = file_path or profile.grammar_seed_file
    if path is None:
        return {"count": 0, "error": "no_seed_file"}

    if not path.exists():
        logger.warning(f"Grammar file not found: {path}")
        return {"count": 0, "error": "file_not_found"}

    text = path.read_text(encoding="utf-8")

    current_level = None
    count = 0

    level_pattern = "|".join(re.escape(level) for level in profile.grammar_level_scheme.levels)

    for line in text.splitlines():
        # Detect level headers (e.g., "N5 LEVEL")
        if "LEVEL" in line:
            level_match = re.search(rf"({level_pattern})", line)
            if level_match:
                current_level = level_match.group(1)
                logger.debug(f"Parsing grammar for {current_level}")
            continue

        # Skip separator lines, empty lines, comments, headers
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("=") or stripped.startswith("#"):
            continue
        if "STATISTICS" in stripped:
            # Stop at statistics section
            break
        if "grammar points" in stripped.lower():
            continue

        if current_level is None:
            continue

        # Parse: pattern (multiple spaces) meaning
        # The format uses lots of spaces/tabs between pattern and meaning
        match = re.match(r'^(.+?)\s{2,}(.+)$', line)
        if match:
            pattern = match.group(1).strip()
            meaning = match.group(2).strip()

            # Skip empty patterns
            if not pattern or not meaning:
                continue

            entry = GrammarEntry(
                language_code=language_code,
                pattern=pattern,
                meaning=meaning,
                jlpt_level=current_level,
                source=profile.grammar_level_scheme.source_name,
                status="New",
            )
            session.add(entry)
            count += 1

    await session.commit()
    logger.info(f"Seeded {count} grammar entries from {path.name}")
    return {"count": count}


async def check_and_seed_grammar(session: AsyncSession, language_code: str | None = None) -> dict:
    """Check if grammar table is empty and seed if needed.

    Args:
        session: Database session

    Returns:
        Dict with seeding result
    """
    from sqlalchemy import func

    language_code = normalize_language_code(language_code)

    # Check if table is empty
    stmt = select(func.count()).select_from(GrammarEntry).where(GrammarEntry.language_code == language_code)
    result = await session.execute(stmt)
    count = result.scalar()

    if count == 0:
        logger.info(f"Grammar table is empty for {language_code}, seeding from profile list...")
        return await seed_grammar_from_file(session, language_code=language_code)
    else:
        logger.info(f"Grammar table already has {count} entries, skipping seed")
        return {"count": 0, "skipped": True, "existing": count}
