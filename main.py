import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database.database import init_db
from bot.handlers.start import router as start_router
from bot.handlers.game import router as game_router


async def main():
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(game_router)

    print("Бот запущен!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())