"""Grammar seeder service - parses JLPT grammar list and seeds the database."""

import re
import logging
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import GrammarEntry

logger = logging.getLogger(__name__)

# Path to grammar list file (relative to backend/ directory)
GRAMMAR_FILE = Path(__file__).parent.parent.parent.parent / "jlpt_grammar_list.txt"


async def seed_grammar_from_file(session: AsyncSession, file_path: Path = None) -> dict:
    """Parse jlpt_grammar_list.txt and seed grammar entries.

    Args:
        session: Database session
        file_path: Optional path override (defaults to GRAMMAR_FILE)

    Returns:
        Dict with count of entries inserted
    """
    path = file_path or GRAMMAR_FILE

    if not path.exists():
        logger.warning(f"Grammar file not found: {path}")
        return {"count": 0, "error": "file_not_found"}

    text = path.read_text(encoding="utf-8")

    current_level = None
    count = 0

    for line in text.splitlines():
        # Detect level headers (e.g., "N5 LEVEL")
        if "LEVEL" in line:
            level_match = re.search(r"(N[1-5])", line)
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
                pattern=pattern,
                meaning=meaning,
                jlpt_level=current_level,
                source="jlpt",
                status="New",
            )
            session.add(entry)
            count += 1

    await session.commit()
    logger.info(f"Seeded {count} grammar entries from {path.name}")
    return {"count": count}


async def check_and_seed_grammar(session: AsyncSession) -> dict:
    """Check if grammar table is empty and seed if needed.

    Args:
        session: Database session

    Returns:
        Dict with seeding result
    """
    from sqlalchemy import func

    # Check if table is empty
    stmt = select(func.count()).select_from(GrammarEntry)
    result = await session.execute(stmt)
    count = result.scalar()

    if count == 0:
        logger.info("Grammar table is empty, seeding from JLPT list...")
        return await seed_grammar_from_file(session)
    else:
        logger.info(f"Grammar table already has {count} entries, skipping seed")
        return {"count": 0, "skipped": True, "existing": count}
