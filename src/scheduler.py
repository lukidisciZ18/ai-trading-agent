"""Async scheduler setup using APScheduler for periodic tasks.
Provides market‑day guard and job listing endpoint helper.
"""
from __future__ import annotations
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import zoneinfo
import pandas_market_calendars as mcal
from typing import Callable, Any

VIENNA = zoneinfo.ZoneInfo("Europe/Vienna")
XNYS = mcal.get_calendar("XNYS")


def is_trading_day(dt: datetime) -> bool:
    try:
        schedule = XNYS.schedule(start_date=dt.date(), end_date=dt.date())
        return not schedule.empty
    except Exception:
        return True  # fail open


def guarded(fn: Callable, *args, **kwargs):
    dt = datetime.now(VIENNA)
    if not is_trading_day(dt):
        return
    try:
        fn(*args, **kwargs)
    except Exception:
        pass  # TODO: add logging


def build_scheduler(scan_func: Callable[[str], None], sentiment_func: Callable[[], None]) -> AsyncIOScheduler:
    sch = AsyncIOScheduler(timezone=VIENNA)
    # sentiment every 30 minutes during day (simple cron example)
    sch.add_job(lambda: guarded(sentiment_func), CronTrigger(minute="*/30", hour="15-22", day_of_week="1-5", timezone=VIENNA), id="sentiment_ingest")
    # open / mid / close scans
    sch.add_job(lambda: guarded(scan_func, "focus"), CronTrigger(hour=15, minute=35, day_of_week="1-5", timezone=VIENNA), id="open_scan")
    sch.add_job(lambda: guarded(scan_func, "full"), CronTrigger(hour=19, minute=0, day_of_week="1-5", timezone=VIENNA), id="mid_scan")
    sch.add_job(lambda: guarded(scan_func, "full"), CronTrigger(hour=22, minute=0, day_of_week="1-5", timezone=VIENNA), id="close_scan")
    return sch


def list_jobs(scheduler: AsyncIOScheduler):
    return [
        {
            "id": j.id,
            "name": j.name,
            "next_run_time": j.next_run_time.isoformat() if j.next_run_time else None,
        }
        for j in scheduler.get_jobs()
    ]
