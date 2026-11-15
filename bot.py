import os
from pathlib import Path
import requests
from google import genai

HISTORY_FILE = Path("history.txt")


def load_recent_topics(limit: int = 30) -> list[str]:
    if not HISTORY_FILE.exists():
        return []
    lines = [line.strip() for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    return lines[-limit:]


def save_topic(topic: str) -> None:
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(topic.strip() + "\n")


def generate_construction_post(recent_topics: list[str]) -> tuple[str, str]:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    avoid_block = ""
    if recent_topics:
        avoid_list = "\n".join(f"- {t}" for t in recent_topics)
        avoid_block = f"\nQuyidagi oldin yozilgan mavzularni TAKRORLAMA:\n{avoid_list}\n"

    prompt = f"""Sen O'zbekistondagi qurilish va ta'mirlash (remont) bo'yicha Telegram kanalining tajribali muallifisan.
Bugun kanal uchun o'zbek tilida (lotin yozuvida) 1 ta foydali, amaliy va qiziqarli post yoz.

Talablar:
1. Birinchi qatorga faqat post sarlavhasini yoz (qisqa va aniq, masalan: "Beton quyishda eng ko'p uchraydigan 3 ta xato").
2. Ikkinchi qatordan boshlab asosiy matnni yoz (120–180 so'z atrofida, o'qishga qulay qisqa abzatslar va 2–3 ta emoji bilan).
3. Oxirida 2–3 ta mos heshteg qo'sh (masalan: #qurilish #remont #maslahat).
4. Hech qanday Markdown belgilari (** yoki ##) ishlatma, faqat toza matn yoz.
{avoid_block}"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
    )

    text = (response.text or "").strip()
    if not text:
        raise ValueError("Gemini bo'sh javob qaytardi.")

    first_line = text.splitlines()[0].strip()
    return first_line, text


def send_to_telegram(message: str) -> None:
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    channel_id = os.environ["TELEGRAM_CHANNEL_ID"]

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": message,
        "disable_web_page_preview": True,
    }

    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()


def main() -> None:
    recent_topics = load_recent_topics()
    topic_title, post_text = generate_construction_post(recent_topics)
    send_to_telegram(post_text)
    save_topic(topic_title)
    print(f"Post muvaffaqiyatli yuborildi: {topic_title}")


if __name__ == "__main__":
    main()
