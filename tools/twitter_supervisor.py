"""
監督: 毎朝09:00 JSTに今日のツイート予定をTeamsに通知する。

- 今日のプランをSharePoint/ローカルから読み込む
- 10:00・19:00の予定ツイートをTeamsに送信
- 承認待ちの場合は「承認してください」と促す
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

PROJECT_ROOT = Path(__file__).parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp"

JST = timezone(timedelta(hours=9))
SLOT_INFO = {
    10: "朝の投稿",
    19: "夜の投稿",
}


def get_today_plan() -> dict:
    """今日のプランをローカルまたはSharePointから取得する。"""
    date_str = datetime.now(JST).strftime("%Y-%m-%d")
    local_path = TMP_DIR / f"daily_tweet_plan_{date_str}.json"

    if not local_path.exists():
        try:
            from teams_upload import download_plan_json
            download_plan_json(date_str, str(local_path))
        except Exception as e:
            logger.warning(f"SharePoint download failed: {e}")

    if local_path.exists():
        with open(local_path, encoding="utf-8") as f:
            return json.load(f), date_str

    return {}, date_str


def get_approval_status(date_str: str) -> dict:
    """ExcelからConfirmed/Declined状態を取得する。"""
    status = {}
    try:
        from excel_feedback import download_plan_excel, read_feedback
        excel_path = download_plan_excel()
        if excel_path:
            for slot in [10, 19]:
                result = read_feedback(excel_path, slot, date_str)
                status[slot] = result.get("action", "pending")
    except Exception as e:
        logger.warning(f"Excel check failed: {e}")
        for slot in [10, 19]:
            status[slot] = "pending"
    return status


def send_daily_briefing(plan: dict, date_str: dict, approval: dict):
    """今日のツイート予定をTeamsに通知する。"""
    import requests

    webhook_url = os.getenv("TEAMS_WEBHOOK_URL") or os.getenv("TEAMS_MASTER_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("No Teams webhook URL configured")
        return

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    day_names = ["月", "火", "水", "木", "金", "土", "日"]
    day_jp = day_names[dt.weekday()]

    slots = plan.get("slots", {})

    lines = [f"📋 **{date_str}（{day_jp}）のツイート予定**\n"]

    for slot in [10, 19]:
        slot_data = slots.get(str(slot), {})
        tweet = slot_data.get("tweet_jp", "")
        category = slot_data.get("category", "")
        approval_status = approval.get(slot, "pending")

        if approval_status == "approve":
            status_icon = "✅ 承認済み"
        elif approval_status == "cancel":
            status_icon = "❌ Declined"
        else:
            status_icon = "⏳ 承認待ち"

        label = SLOT_INFO.get(slot, f"{slot}:00")
        lines.append(f"**{slot}:00 {label}** [{category}] {status_icon}")
        if tweet:
            lines.append(f"> {tweet[:100]}{'...' if len(tweet) > 100 else ''}")
        else:
            lines.append("> （プランなし）")
        lines.append("")

    pending = [s for s in [10, 19] if approval.get(s, "pending") == "pending" and slots.get(str(s))]
    if pending:
        slots_str = "・".join([f"{s}:00" for s in pending])
        lines.append(f"⚠️ **{slots_str} の承認をお願いします。**")
        lines.append("Excelで「Confirmed」を入力して保存してください。")

    message = "\n".join(lines)

    payload = {"text": message}
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("Daily briefing sent to Teams")
    except Exception as e:
        logger.error(f"Teams notification failed: {e}")


def main():
    plan, date_str = get_today_plan()

    if not plan or not plan.get("slots"):
        logger.warning(f"No plan found for {date_str}")
        # プランがない場合もその旨をTeamsに通知
        import requests
        webhook_url = os.getenv("TEAMS_WEBHOOK_URL") or os.getenv("TEAMS_MASTER_WEBHOOK_URL")
        if webhook_url:
            requests.post(webhook_url, json={
                "text": f"⚠️ **監督**: {date_str} のツイートプランが見つかりません。企画マンを手動実行してください。"
            }, timeout=10)
        return

    approval = get_approval_status(date_str)
    send_daily_briefing(plan, date_str, approval)


if __name__ == "__main__":
    main()
