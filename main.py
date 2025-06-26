import asyncio
from pyrogram import Client
from os import getenv
from dotenv import load_dotenv
import logging
import logging.config
import configparser

load_dotenv()

config = configparser.ConfigParser()
config.read("config.ini")

MIN_PRICE = int(config["gifts"]["min_price"])
MAX_PRICE = int(config["gifts"]["max_price"])
ONLY_LIMITED = config.getboolean("gifts", "only_limited")
RECIPIENT = config["gifts"]["recipient"]

logger = logging.getLogger(__name__)

# Pyrogram client
app = Client(
    getenv("SHORT_NAME"),
    api_id=getenv("API_ID"),
    api_hash=getenv("API_HASH"),
    device_model="Samsung Galaxy A55",
    app_version="Android 1.1.1"
)

seen_gift_ids = set()


async def notify_about_gifts():
    global seen_gift_ids

    async with app:
        logger.info("Client started. Monitoring gifts...")

        while True:
            try:
                balance = await app.get_stars_balance()
                gifts = await app.get_available_gifts()
                logger.debug(
                    "Current balance: %s. Fetched %s gifts.",
                    balance, len(gifts))

                for gift in gifts:
                    gift_id = gift.id
                    price = gift.price
                    is_limited = gift.is_limited
                    is_sold_out = gift.is_sold_out

                    logger.debug("Checking gift ID %s: price=%s, limited=%s, sold_out=%s",
                                 gift_id, price, is_limited, is_sold_out)

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
                        logger.warning("Insufficient balance for gift ID %s. Needed: %s, Available: %s",
                                       gift_id, price, balance)
                        await app.send_message(
                            RECIPIENT,
                            "🚫 Purchase blocked: Not enough stars – you have %s⭐, but the gift %s costs %s⭐ (ID: %s)" %
                            (balance, emoji, price, gift_id)
                        )
                        continue

                    try:
                        await app.send_gift(chat_id=RECIPIENT, gift_id=gift_id, hide_my_name=True)
                        logger.info("Gift ID %s sent successfully.", gift_id)
                        await app.send_message(
                            RECIPIENT,
                            "🔔 New gift sent: %s for %s⭐ (ID: %s)" % (
                                emoji, price, gift_id)
                        )
                    except Exception as err:
                        logger.error(
                            "Failed to send gift ID %s: %s", gift_id, err)
                        await app.send_message(
                            RECIPIENT,
                            "🚫 Failed to send gift: %s" % err
                        )

                await asyncio.sleep(10)

            except Exception as e:
                logger.exception(
                    "Unexpected error occurred in main loop: %s", e)
                await asyncio.sleep(30)


if __name__ == '__main__':
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default"
            }
        },
        "loggers": {
            "pyrogram": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "__main__": {
                "level": "DEBUG",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }

    logging.config.dictConfig(LOGGING_CONFIG)
    asyncio.run(notify_about_gifts())
