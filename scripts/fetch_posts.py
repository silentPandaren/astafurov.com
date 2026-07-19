"""Fetch latest posts from t.me/s/mindventure and write posts.json for the site feed."""
import json
import re
import html
import urllib.request
from pathlib import Path

CHANNEL = "mindventure"
MAX_POSTS = 5
OUT = Path(__file__).resolve().parent.parent / "posts.json"

req = urllib.request.Request(
    f"https://t.me/s/{CHANNEL}",
    headers={"User-Agent": "Mozilla/5.0 (site feed; astafurov.com)"},
)
page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")

# Each message sits in its own wrapper div; split page into per-message chunks.
chunks = page.split('class="tgme_widget_message_wrap')[1:]

posts = []
for chunk in chunks:
    m_id = re.search(rf'data-post="{CHANNEL}/(\d+)"', chunk)
    m_date = re.search(r'<time datetime="([^"]+)"', chunk)
    m_text = re.search(
        r'tgme_widget_message_text js-message_text" dir="auto">(.*?)</div>',
        chunk,
        re.DOTALL,
    )
    if not (m_id and m_date and m_text):
        continue  # photo-only posts or service messages have no text block

    raw = m_text.group(1)
    raw = re.sub(r"<br\s*/?>", "\n", raw)
    text = html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()
    if not text:
        continue

    first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    title = first_line if len(first_line) <= 110 else first_line[:107].rstrip() + "…"

    posts.append(
        {
            "id": int(m_id.group(1)),
            "url": f"https://t.me/{CHANNEL}/{m_id.group(1)}",
            "date": m_date.group(1)[:10],
            "title": title,
        }
    )

posts.sort(key=lambda p: p["id"], reverse=True)
posts = posts[:MAX_POSTS]

if not posts:
    raise SystemExit("No posts parsed — page layout may have changed, keeping old posts.json")

OUT.write_text(json.dumps(posts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {len(posts)} posts to {OUT}")
