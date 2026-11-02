import random

from bot.services.countries_api import get_quiz_countries


def get_capital_name(capital) -> str | None:
    """
    Преобразует данные о столице REST Countries
    в обычную строку.
    """

    if isinstance(capital, str):
        return capital

    if isinstance(capital, dict):
        return capital.get("name")

    return None


def get_initial(capital: str) -> str:
    """
    Возвращает первую букву названия столицы.
    """

    return capital.strip()[0].casefold()


async def generate_question() -> dict | None:
    countries = await get_quiz_countries()

    if len(countries) < 4:
        return None

    # Выбираем страну для вопроса
    question_country = random.choice(countries)

    correct_capital = get_capital_name(
        question_country["capital"]
    )

    if not correct_capital:
        return None

    correct_initial = get_initial(correct_capital)

    # Все остальные страны с нормальными столицами
    available_countries = []

    for country in countries:
        capital = get_capital_name(
            country["capital"]
        )

        if not capital:
            continue

        if capital == correct_capital:
            continue

        available_countries.append(
            {
                "capital": capital
            }
        )

    if len(available_countries) < 3:
        return None

    # Ищем неправильный вариант,
    # который начинается с той же буквы
    same_initial = []

    for country in available_countries:
        capital = country["capital"]

        if get_initial(capital) == correct_initial:
            same_initial.append(country)

    selected_wrong_answers = []

    # Если нашли хотя бы одну столицу
    # с такой же первой буквой —
    # обязательно добавляем её
    if same_initial:
        same_initial_answer = random.choice(
            same_initial
        )

        selected_wrong_answers.append(
            same_initial_answer
        )

    # Добавляем остальные неправильные ответы
    remaining_answers = [
        country
        for country in available_countries
        if country not in selected_wrong_answers
    ]

    needed = 3 - len(selected_wrong_answers)

    if len(remaining_answers) < needed:
        return None

    selected_wrong_answers.extend(
        random.sample(
            remaining_answers,
            needed,
        )
    )

    # Формируем варианты ответа
    options = [
        correct_capital,
        *[
            country["capital"]
            for country in selected_wrong_answers
        ],
    ]

    random.shuffle(options)

    return {
        "country": question_country["country"],
        "capital": correct_capital,
        "flag": question_country["flag"],
        "options": options,
    }