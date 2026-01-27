from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional

from app.db.database import get_session
from app.db.models import TokenLog
from app.config import get_settings

router = APIRouter()


class LimitUpdate(BaseModel):
    limit: float


@router.get("/usage")
async def get_usage(
    period: str = Query("week", pattern="^(day|week|month)$"),
    session=Depends(get_session)
):
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

    # Group by day
    daily_breakdown = {}
    for log in logs:
        day_key = log.created_at.strftime("%Y-%m-%d")
        if day_key not in daily_breakdown:
            daily_breakdown[day_key] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0,
                "requests": 0,
            }
        daily_breakdown[day_key]["input_tokens"] += log.input_tokens
        daily_breakdown[day_key]["output_tokens"] += log.output_tokens
        daily_breakdown[day_key]["cost_usd"] += log.cost_usd
        daily_breakdown[day_key]["requests"] += 1

    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": now.isoformat(),
        "totals": {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "cost_usd": round(total_cost, 4),
            "image_count": total_images,
            "request_count": len(logs),
        },
        "daily_breakdown": daily_breakdown,
    }


@router.get("/limit")
async def get_limit(session=Depends(get_session)):
    settings = get_settings()
    now = datetime.utcnow()
    week_start = now - timedelta(days=7)

    stmt = select(func.sum(TokenLog.cost_usd)).where(TokenLog.created_at >= week_start)
    spent = await session.scalar(stmt) or 0.0

    return {
        "spent": round(spent, 4),
        "limit": settings.cost_limit_weekly,
        "remaining": round(settings.cost_limit_weekly - spent, 4),
        "period": "weekly",
        "period_start": week_start.isoformat(),
    }


@router.put("/limit")
async def update_limit(data: LimitUpdate):
    # Note: This would typically update a database setting or config file
    # For now, we just return success since the limit is from env
    return {
        "message": "Limit setting requires updating environment variable COST_LIMIT_WEEKLY",
        "requested_limit": data.limit,
    }
