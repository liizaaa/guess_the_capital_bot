import asyncio
import logging
import ssl
import time

import aiohttp
import certifi

from config import (
    YANDEX_MAPS_API_KEY,
    YANDEX_GEOCODER_API_KEY,
)

logger = logging.getLogger(__name__)

STATIC_MAPS_URL = "https://static-maps.yandex.ru/v1"
GEOCODER_URL = "https://geocode-maps.yandex.ru/v1"

CACHE_TTL = 60 * 60

# Кеш координат столиц
_coordinates_cache = {}


async def get_capital_coordinates(
    capital: str,
    country: str,
) -> tuple[float, float] | None:
    """
    Находит координаты столицы через Яндекс Геокодер.

    Возвращает (долгота, широта).
    """

    if not YANDEX_GEOCODER_API_KEY:
        logger.error("Не настроен ключ Яндекс Геокодера")
        return None

    query = f"{capital}, {country}"
    cache_key = query.casefold()
    now = time.monotonic()

    cached = _coordinates_cache.get(cache_key)

    if cached and now - cached["time"] < CACHE_TTL:
        return cached["coordinates"]

    params = {
        "apikey": YANDEX_GEOCODER_API_KEY,
        "geocode": query,
        "format": "json",
        "lang": "en_US",
        "results": 1,
    }

    ssl_context = ssl.create_default_context(
        cafile=certifi.where()
    )

    connector = aiohttp.TCPConnector(
        ssl=ssl_context
    )

    timeout = aiohttp.ClientTimeout(total=15)

    try:
        async with aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
        ) as session:
            async with session.get(
                GEOCODER_URL,
                params=params,
            ) as response:

                if response.status != 200:
                    logger.warning(
                        "Геокодер HTTP %s: %s",
                        response.status,
                        (await response.text())[:300],
                    )
                    return None

                data = await response.json()

        members = (
            data.get("response", {})
            .get("GeoObjectCollection", {})
            .get("featureMember", [])
        )

        if not members:
            logger.warning(
                "Координаты не найдены для %s",
                query,
            )
            return None

        position = (
            members[0]
            .get("GeoObject", {})
            .get("Point", {})
            .get("pos")
        )

        if not position:
            return None

        # Яндекс возвращает: "долгота широта"
        longitude, latitude = map(
            float,
            position.split(),
        )

        coordinates = (longitude, latitude)

        _coordinates_cache[cache_key] = {
            "coordinates": coordinates,
            "time": time.monotonic(),
        }

        return coordinates

    except (
        aiohttp.ClientError,
        asyncio.TimeoutError,
        ValueError,
        TypeError,
    ) as error:
        logger.warning(
            "Ошибка геокодирования %s: %s",
            query,
            type(error).__name__,
        )
        return None


async def get_capital_map(
    capital: str,
    country: str,
) -> bytes | None:
    """
    Создаёт изображение карты с отметкой столицы.
    """

    if not YANDEX_MAPS_API_KEY:
        logger.error("Не настроен ключ Яндекс Static API")
        return None

    coordinates = await get_capital_coordinates(
        capital,
        country,
    )

    if coordinates is None:
        return None

    longitude, latitude = coordinates

    params = {
        "apikey": YANDEX_MAPS_API_KEY,
        "ll": f"{longitude},{latitude}",
        "z": 12,
        "size": "600,400",
        "lang": "ru_RU",
        "pt": f"{longitude},{latitude},pm2rdm",
    }

    ssl_context = ssl.create_default_context(
        cafile=certifi.where()
    )

    connector = aiohttp.TCPConnector(
        ssl=ssl_context
    )

    timeout = aiohttp.ClientTimeout(total=15)

    try:
        async with aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
        ) as session:
            async with session.get(
                STATIC_MAPS_URL,
                params=params,
            ) as response:

                if response.status != 200:
                    logger.warning(
                        "Static API HTTP %s: %s",
                        response.status,
                        (await response.text())[:300],
                    )
                    return None

                content_type = response.headers.get(
                    "Content-Type", ""
                )

                if not content_type.startswith("image/"):
                    logger.warning(
                        "Static API вернул не изображение"
                    )
                    return None

                return await response.read()

    except (
        aiohttp.ClientError,
        asyncio.TimeoutError,
    ) as error:
        logger.warning(
            "Ошибка загрузки карты: %s",
            type(error).__name__,
        )
        return None