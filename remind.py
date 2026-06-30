"""
Moodle課題リマインダー → Discord通知スクリプト

毎日定期実行することを想定。
- MoodleのiCalカレンダーエクスポートURLから課題一覧を取得
- 締切が近い課題、まだ通知していない課題を検出
- Discord Webhookに通知を送信
- 通知済みのIDをファイルに記録し、重複通知を防ぐ
"""

import os
import json
from datetime import datetime, timedelta, timezone

import requests
from icalendar import Calendar

# ===== 設定(環境変数から読み込み) =====
ICAL_URL = os.environ.get("ICAL_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# 締切何日前から通知し始めるか(この日数以内になったら通知対象)
REMIND_DAYS_BEFORE = int(os.environ.get("REMIND_DAYS_BEFORE", "3"))

# 通知済みIDを記録するファイル(GitHub Actions上で永続化する)
STATE_FILE = "notified.json"

JST = timezone(timedelta(hours=9))


def fetch_events():
    """MoodleのiCal URLから課題イベント一覧を取得する"""
    if not ICAL_URL:
        raise RuntimeError("環境変数 ICAL_URL が設定されていません")

    resp = requests.get(ICAL_URL, timeout=30)
    resp.raise_for_status()

    cal = Calendar.from_ical(resp.text)

    events = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        uid = str(component.get("UID"))
        title = str(component.get("SUMMARY"))
        course = str(component.get("CATEGORIES")) if component.get("CATEGORIES") else ""

        dtstart = component.get("DTSTART").dt
        # datetime型に統一(全日イベントなどでdate型の場合に備える)
        if not isinstance(dtstart, datetime):
            dtstart = datetime(dtstart.year, dtstart.month, dtstart.day, tzinfo=timezone.utc)
        if dtstart.tzinfo is None:
            dtstart = dtstart.replace(tzinfo=timezone.utc)

        events.append({
            "uid": uid,
            "title": title,
            "course": course,
            "due": dtstart,
        })

    return events


def load_notified():
    """通知済みUIDのセットをファイルから読み込む"""
    if not os.path.exists(STATE_FILE):
        return set()
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        try:
            return set(json.load(f))
        except json.JSONDecodeError:
            return set()


def save_notified(notified_set):
    """通知済みUIDのセットをファイルに保存する"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(notified_set), f, ensure_ascii=False, indent=2)


def send_discord_message(content):
    """Discord Webhookにメッセージを送信する"""
    if not DISCORD_WEBHOOK_URL:
        raise RuntimeError("環境変数 DISCORD_WEBHOOK_URL が設定されていません")

    resp = requests.post(DISCORD_WEBHOOK_URL, json={"content": content}, timeout=30)
    resp.raise_for_status()


def format_message(event):
    due_jst = event["due"].astimezone(JST)
    due_str = due_jst.strftime("%Y/%m/%d (%a) %H:%M")
    course = event["course"] or "(科目不明)"
    return (
        f"📌 **{event['title']}**\n"
        f"科目: {course}\n"
        f"締切: {due_str}"
    )


def main():
    now = datetime.now(timezone.utc)
    deadline_threshold = now + timedelta(days=REMIND_DAYS_BEFORE)

    events = fetch_events()
    notified = load_notified()

    # 締切が「今〜REMIND_DAYS_BEFORE日後」の範囲にある課題を対象にする
    # (過去の締切や、まだ遠い先の締切は対象外)
    targets = [
        e for e in events
        if now <= e["due"] <= deadline_threshold and e["uid"] not in notified
    ]

    # 締切が近い順に並べる
    targets.sort(key=lambda e: e["due"])

    if not targets:
        print("通知対象の課題はありません")
        return

    for event in targets:
        message = format_message(event)
        send_discord_message(message)
        notified.add(event["uid"])
        print(f"通知送信: {event['title']}")

    save_notified(notified)


if __name__ == "__main__":
    main()
