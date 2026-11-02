import os

from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")

UNSPLASH_ACCESS_KEY = os.getenv(
    "UNSPLASH_ACCESS_KEY"
)

YANDEX_MAPS_API_KEY = os.getenv("YANDEX_MAPS_API_KEY")

YANDEX_GEOCODER_API_KEY = os.getenv(
    "YANDEX_GEOCODER_API_KEY",
    YANDEX_MAPS_API_KEY,
)

REST_COUNTRIES_API_KEY = os.getenv(
    "REST_COUNTRIES_API_KEY"
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./database.db"
)


if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN не найден в .env"
    )

if not REST_COUNTRIES_API_KEY:
    raise ValueError(
        "REST_COUNTRIES_API_KEY не найден в .env"
    )