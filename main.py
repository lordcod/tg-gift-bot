import asyncio
from pyrogram import Client
from os import getenv
from dotenv import load_dotenv
import logging
import configparser

load_dotenv()

config = configparser.ConfigParser()
config.read("config.ini")

MIN_PRICE = int(config["gifts"]["min_price"])
MAX_PRICE = int(config["gifts"]["max_price"])
ONLY_LIMITED = config.getboolean("gifts", "only_limited")
RECIPIENT = config["gifts"]["recipient"]

app = Client(
    getenv("SHORT_NAME"),
    api_id=getenv("api_id"),
    api_hash=getenv("api_hash"),
    device_model="Samsung Galaxy A55",
    app_version="Android 1.1.1"
)

seen_gift_ids = set()


async def notify_about_gifts():
    global seen_gift_ids

    async with app:
        while True:
            balance = await app.get_stars_balance()
            gifts = await app.get_available_gifts()

            for gift in gifts:
                gift_id = gift.id
                price = gift.price
                is_limited = gift.is_limited
                is_sold_out = gift.is_sold_out

                if gift_id in seen_gift_ids:
                    continue

                if is_sold_out:
                    continue

                if ONLY_LIMITED and not is_limited:
                    continue

                if not (MIN_PRICE <= price <= MAX_PRICE):
                    continue

                seen_gift_ids.add(gift_id)

                emoji = getattr(gift.sticker, "emoji", "🎁")

                if balance < price:
                    await app.send_message(RECIPIENT,
                                           f"🚫 Платеж заблокирован: Не хватает ваших средств - {balance} на подарок {emoji} {price}⭐ (ID: {gift_id})")
                    continue

                try:
                    await app.send_gift(chat_id=RECIPIENT, gift_id=gift_id, hide_my_name=True)
                    await app.send_message(RECIPIENT,
                                           f"🔔 Новый подарок: {emoji} за {price}⭐ (ID: {gift_id})")
                except Exception as err:
                    await app.send_message(RECIPIENT,
                                           f"🚫 Ошибка при отправке подарка: {err}")

            await asyncio.sleep(10)  # Проверка каждые 10 секунд


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(notify_about_gifts())
