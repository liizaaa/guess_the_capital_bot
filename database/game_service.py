
from sqlalchemy import select

from database.database import async_session
from database.models import User, Game
from database.achievement_service import check_achievements


async def save_game_result(
    telegram_id: int,
    country: str,
    correct_capital: str,
    user_answer: str | None,
    is_correct: bool,
    time_spent: float | None,
    hints_used: int = 0,
) -> User | None:

    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            return None

        # Сохраняем результат вопроса.
        game = Game(
            user_id=user.id,
            country=country,
            correct_capital=correct_capital,
            user_answer=user_answer,
            is_correct=is_correct,
            time_spent=time_spent,
            hints_used=hints_used,
        )

        session.add(game)

        # Обновляем статистику.
        user.games_played += 1

        if is_correct:
            user.correct_answers += 1
            user.streak += 1

            if user.streak > user.best_streak:
                user.best_streak = user.streak

            # Начисляем XP за правильный ответ.
            if hints_used == 0:
                xp = 10
            elif hints_used == 1:
                xp = 7
            else:
                xp = 5

            user.xp += xp

        else:
            user.streak = 0

        # Проверяем достижения.
        new_achievements = await check_achievements(
            session,
            user,
        )

        # Пересчитываем уровень с учётом бонусного XP.
        user.level = user.xp // 100 + 1

        # Сохраняем все изменения.
        await session.commit()
        await session.refresh(user)

        # Передаём новые достижения обработчику игры.
        user.new_achievements = new_achievements

        return user
