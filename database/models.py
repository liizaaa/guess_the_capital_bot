
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    first_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    games_played: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    correct_answers: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    best_streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    games: Mapped[list["Game"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    achievements: Mapped[list["UserAchievement"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    country: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    correct_capital: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    user_answer: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    time_spent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    hints_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    played_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="games",
    )


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    xp_reward: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    users: Mapped[list["UserAchievement"]] = relationship(
        back_populates="achievement",
        cascade="all, delete-orphan",
    )


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "achievement_id",
            name="unique_user_achievement",
        ),
        Index(
            "idx_user_achievements_user_id",
            "user_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    achievement_id: Mapped[int] = mapped_column(
        ForeignKey("achievements.id"),
        nullable=False,
    )

    earned_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="achievements",
    )

    achievement: Mapped["Achievement"] = relationship(
        back_populates="users",
    )
