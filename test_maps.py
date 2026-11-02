import asyncio

from bot.services.maps_service import get_capital_map


async def main():
    image = await get_capital_map(
        capital="Paris",
        country="France",
    )

    if image is None:
        print("❌ Не удалось получить карту.")
        print("Проверь API-ключ и доступ к Static API.")
        return

    with open("test_map.png", "wb") as file:
        file.write(image)

    print("✅ Карта получена!")
    print(f"Размер изображения: {len(image)} байт")


if __name__ == "__main__":
    asyncio.run(main())