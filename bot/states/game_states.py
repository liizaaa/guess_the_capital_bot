from aiogram.fsm.state import State, StatesGroup


class GameStates(StatesGroup):
    choosing_game = State()
    question = State()
    waiting_for_answer = State()
    checking_answer = State()
    showing_result = State()