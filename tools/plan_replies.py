"""
WAT Tool: Plan reply drafts for Twitter engagement slots.

Stub implementation — replies are optional. Returns empty plans by default.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp"


def plan_daily_replies(reply_slots: list) -> dict:
    """Generate reply drafts for given slots. Returns empty dict (replies optional)."""
    logger.info(f"plan_daily_replies: slots {reply_slots} — skipping (no reply targets configured)")
    return {str(slot): [] for slot in reply_slots}


def merge_replies_into_plan(reply_plans: dict, plan_file: str = None) -> dict:
    """Merge reply plans into the daily plan file. Returns updated plan."""
    if not plan_file:
        return {}

    plan_path = Path(plan_file)
    if not plan_path.exists():
        logger.warning(f"Plan file not found: {plan_path}")
        return {}

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    for slot_str, replies in reply_plans.items():
        if slot_str in plan.get("slots", {}):
            plan["slots"][slot_str]["replies"] = replies

    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    logger.info(f"Merged replies into {plan_path.name}")
    return plan
