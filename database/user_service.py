from sqlalchemy import select

from database.database import async_session
from database.models import User


async def get_or_create_user(
    telegram_id: int,
    username: str | None,
    first_name: str | None,
) -> User:
    async with async_session() as session:

        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )

        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
            )

            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user