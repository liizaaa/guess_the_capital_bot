
import asyncio
import logging
import ssl
import time

import aiohttp
import certifi

from config import REST_COUNTRIES_API_KEY


logger = logging.getLogger(__name__)

BASE_URL = "https://api.restcountries.com/countries/v5"

CACHE_TTL = 60 * 60
MAX_ATTEMPTS = 3

_cache = None
_cache_time = 0

_quiz_cache = None
_quiz_cache_time = 0


def _is_cache_valid(cache_time: float) -> bool:
    """Проверить, не истёк ли срок действия кэша."""
    return time.monotonic() - cache_time < CACHE_TTL


async def get_countries() -> list[dict]:
    """Получить список стран с использованием кэша."""
    global _cache, _cache_time

    # Возвращаем кэш, если он ещё действителен.
    if _cache is not None and _is_cache_valid(_cache_time):
        logger.info("Используем кеш REST Countries")
        return _cache

    headers = {
        "Authorization": f"Bearer {REST_COUNTRIES_API_KEY}"
    }

    params = {
        "response_fields": "names.common,capitals,flag.emoji",
        "limit": 100,
    }

    ssl_context = ssl.create_default_context(
        cafile=certifi.where()
    )

    timeout = aiohttp.ClientTimeout(total=10)

    # Выполняем до трёх попыток запроса.
    for attempt in range(MAX_ATTEMPTS):
        try:
            connector = aiohttp.TCPConnector(ssl=ssl_context)

            async with aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=connector,
            ) as session:
                async with session.get(
                    BASE_URL,
                    params=params,
                ) as response:

                    if response.status == 200:
                        result = await response.json()

                        data = result.get("data", {})
                        countries = data.get("objects", [])

                        if not isinstance(countries, list):
                            raise ValueError(
                                "API вернул некорректный список стран"
                            )

                        # Не сохраняем пустой результат как успешный ответ.
                        if not countries:
                            raise ValueError(
                                "API вернул пустой список стран"
                            )

                        _cache = countries
                        _cache_time = time.monotonic()

                        # При обновлении исходных данных сбрасываем
                        # подготовленный список для викторины.
                        _clear_quiz_cache()

                        logger.info(
                            "Получено стран из REST Countries: %s",
                            len(countries),
                        )

                        return countries

                    text = await response.text()

                    logger.warning(
                        "REST Countries: HTTP %s: %s",
                        response.status,
                        text[:300],
                    )

                    # Повторять запрос при большинстве ошибок HTTP
                    # бессмысленно, например при 401 или 403.
                    if response.status < 500 and response.status != 429:
                        break

        except (
            aiohttp.ClientError,
            asyncio.TimeoutError,
            ValueError,
        ) as error:
            logger.warning(
                "Ошибка REST Countries, попытка %s/%s: %s",
                attempt + 1,
                MAX_ATTEMPTS,
                error,
            )

        if attempt < MAX_ATTEMPTS - 1:
            await asyncio.sleep(2 ** attempt)

    logger.error("Не удалось загрузить данные REST Countries")

    # Если API недоступен, используем ранее загруженные данные,
    # даже если их срок действия истёк.
    if _cache is not None:
        logger.warning("Используем устаревший кеш стран")
        return _cache

    return []


def _clear_quiz_cache() -> None:
    """Сбросить кэш подготовленных стран."""
    global _quiz_cache, _quiz_cache_time

    _quiz_cache = None
    _quiz_cache_time = 0


async def get_quiz_countries() -> list[dict]:
    """Получить подготовленный список стран для викторины."""
    global _quiz_cache, _quiz_cache_time

    # Проверяем кэш уже подготовленного списка.
    if (
        _quiz_cache is not None
        and _is_cache_valid(_quiz_cache_time)
    ):
        logger.info("Используем кеш стран для викторины")
        return _quiz_cache

    countries = await get_countries()
    result = []

    for country in countries:
        names = country.get("names", {})
        name = names.get("common")

        capitals = country.get("capitals", [])
        flag_data = country.get("flag", {})
        flag = flag_data.get("emoji", "")

        if not name or not capitals:
            continue

        capital = capitals[0]

        # На случай, если API вернул столицу в виде словаря.
        if isinstance(capital, dict):
            capital = capital.get("name")

        if not capital:
            continue

        result.append({
            "country": name,
            "capital": capital,
            "flag": flag,
        })

    _quiz_cache = result
    _quiz_cache_time = time.monotonic()

    logger.info(
        "Подготовлено стран для викторины: %s",
        len(result),
    )

    return result
