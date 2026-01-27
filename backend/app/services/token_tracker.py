from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models import TokenLog
from app.config import Settings


async def log_token_usage(
    session: AsyncSession,
    session_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    image_count: int = 0,
    settings: Optional[Settings] = None
) -> TokenLog:
    """Log token usage for a request."""
    # Calculate cost
    cost_usd = 0.0
    if settings:
        cost_usd = (
            (input_tokens * settings.gemini_input_cost_per_1m / 1_000_000) +
            (output_tokens * settings.gemini_output_cost_per_1m / 1_000_000)
        )

    log = TokenLog(
        session_id=session_id,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        image_count=image_count,
        cost_usd=cost_usd,
    )
    session.add(log)
    await session.commit()
    return log


async def get_usage_summary(
    session: AsyncSession,
    period: str = "week"
) -> Dict[str, Any]:
    """Get usage summary for a time period."""
    now = datetime.utcnow()

    if period == "day":
        start_date = now - timedelta(days=1)
    elif period == "week":
        start_date = now - timedelta(weeks=1)
    else:  # month
        start_date = now - timedelta(days=30)

    stmt = select(TokenLog).where(TokenLog.created_at >= start_date)
    result = await session.execute(stmt)
    logs = result.scalars().all()

    total_input = sum(log.input_tokens for log in logs)
    total_output = sum(log.output_tokens for log in logs)
    total_cost = sum(log.cost_usd for log in logs)
    total_images = sum(log.image_count for log in logs)

    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": now.isoformat(),
        "input_tokens": total_input,
        "output_tokens": total_output,
        "total_tokens": total_input + total_output,
        "cost_usd": round(total_cost, 4),
        "image_count": total_images,
        "request_count": len(logs),
    }


async def get_weekly_spend(session: AsyncSession) -> float:
    """Get total spend for the current week."""
    week_start = datetime.utcnow() - timedelta(days=7)
    stmt = select(func.sum(TokenLog.cost_usd)).where(
        TokenLog.created_at >= week_start
    )
    total = await session.scalar(stmt)
    return total or 0.0


async def check_cost_limit(
    session: AsyncSession,
    settings: Settings
) -> Dict[str, Any]:
    """Check if cost limit has been reached."""
    spent = await get_weekly_spend(session)
    limit = settings.cost_limit_weekly
    remaining = limit - spent

    return {
        "spent": round(spent, 4),
        "limit": limit,
        "remaining": round(remaining, 4),
        "exceeded": remaining <= 0,
        "percentage": round((spent / limit) * 100, 1) if limit > 0 else 0,
    }
