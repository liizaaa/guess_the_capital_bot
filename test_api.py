import asyncio

from bot.services.countries_api import get_quiz_countries


async def main():
    countries = await get_quiz_countries()

    print(f"Получено стран: {len(countries)}")

    for country in countries[:10]:
        print(
            country["flag"],
            country["country"],
            "→",
            country["capital"],
        )


if __name__ == "__main__":
    asyncio.run(main())