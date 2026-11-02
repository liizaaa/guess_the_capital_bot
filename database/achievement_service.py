
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    User,
    Achievement,
    UserAchievement,
)


ACHIEVEMENTS = [
    {
        "name": "🌱 Первый успех",
        "description": "Дать первый правильный ответ",
        "xp_reward": 10,
        "condition": lambda user: user.correct_answers >= 1,
    },
    {
        "name": "🧠 Эрудит",
        "description": "Дать 10 правильных ответов",
        "xp_reward": 25,
        "condition": lambda user: user.correct_answers >= 10,
    },
    {
        "name": "🌍 Географ",
        "description": "Дать 50 правильных ответов",
        "xp_reward": 50,
        "condition": lambda user: user.correct_answers >= 50,
    },
    {
        "name": "🏆 Знаток столиц",
        "description": "Дать 100 правильных ответов",
        "xp_reward": 100,
        "condition": lambda user: user.correct_answers >= 100,
    },
    {
        "name": "🔥 На волне",
        "description": "Ответить правильно 5 раз подряд",
        "xp_reward": 25,
        "condition": lambda user: user.best_streak >= 5,
    },
    {
        "name": "⚡ Без ошибок",
        "description": "Ответить правильно 10 раз подряд",
        "xp_reward": 75,
        "condition": lambda user: user.best_streak >= 10,
    },
]


async def check_achievements(
    session: AsyncSession,
    user: User,
) -> list[dict]:
    """Проверяет условия и выдаёт новые достижения."""

    new_achievements = []

    for item in ACHIEVEMENTS:
        # Проверяем, выполнено ли условие.
        if not item["condition"](user):
            continue

        # Ищем достижение в базе данных.
        result = await session.execute(
            select(Achievement).where(
                Achievement.name == item["name"]
            )
        )

        achievement = result.scalar_one_or_none()

        # Если достижения ещё нет, создаём его.
        if achievement is None:
            achievement = Achievement(
                name=item["name"],
                description=item["description"],
                xp_reward=item["xp_reward"],
            )
            session.add(achievement)
            await session.flush()

        # Проверяем, получал ли пользователь это достижение.
        result = await session.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user.id,
                UserAchievement.achievement_id == achievement.id,
            )
        )

        already_received = result.scalar_one_or_none()

        if already_received:
            continue

        # Сохраняем получение достижения.
        user_achievement = UserAchievement(
            user_id=user.id,
            achievement_id=achievement.id,
        )

        session.add(user_achievement)

        # Начисляем дополнительный XP.
        user.xp += achievement.xp_reward

        new_achievements.append({
            "name": achievement.name,
            "description": achievement.description,
            "xp_reward": achievement.xp_reward,
        })

    return new_achievements
