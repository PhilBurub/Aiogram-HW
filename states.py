from aiogram.fsm.state import State, StatesGroup


class UserInfo(StatesGroup):
    weight = State('weight', 'set_profile')
    height = State('height', 'set_profile')
    age = State('age', 'set_profile')
    activity = State('activity', 'set_profile')
    city = State('city', 'set_profile')
    calories_auto = State('calories_auto', 'set_profile')
    calories = State('calories', 'set_profile')


class Food(StatesGroup):
    food = State('food', 'log_food')