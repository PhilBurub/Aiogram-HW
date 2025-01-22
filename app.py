import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command, CommandObject
from datetime import date
from get_info import get_water, get_calories, get_workout_calories
from states import UserInfo, Food

from conf import bot_token

bot = Bot(token=bot_token)
dp = Dispatcher()
users = {}


async def check_date(data):
    if data.get('logging', {}).get('today') != date.today():
        data['logging'] = {
            'today': date.today(),
            'water': 0,
            'water_spent': 0,
            'calories': 0,
            'calories_burnt': 0
        }
    return data


@dp.message(Command("set_profile"))
async def set_profile(message: Message, state: FSMContext):
    await state.set_state(UserInfo.weight)
    await message.answer("Введите ваш вес (в кг):")

@dp.message(UserInfo.weight)
async def set_weight(message: Message, state: FSMContext):
    await state.update_data(weight=float(message.text))
    await state.set_state(UserInfo.height)
    await message.answer("Введите ваш рост (в см):")

@dp.message(UserInfo.height)
async def set_height(message: Message, state: FSMContext):
    await state.update_data(height=float(message.text))
    await state.set_state(UserInfo.age)
    await message.answer("Введите ваш возраст:")

@dp.message(UserInfo.age)
async def set_age(message: Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await state.set_state(UserInfo.activity)
    await message.answer("Сколько минут активности у вас в день?")

@dp.message(UserInfo.activity)
async def set_city(message: Message, state: FSMContext):
    await state.update_data(activity=int(message.text))
    await state.set_state(UserInfo.city)
    await message.answer("В каком городе вы находитесь?")

@dp.message(UserInfo.city)
async def is_calories_auto(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(UserInfo.calories_auto)
    await message.answer(
        "Вы хотите рассчитать норму калорий автоматически?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Да"), KeyboardButton(text="Нет")]],
            resize_keyboard=True,
        )
    )

@dp.message(UserInfo.calories_auto, F.text.casefold() == "да")
async def set_calories_auto(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    data['calories'] = 10*data.get('weight') + 6.25*data.get('height') - 5*data.get('age')
    data['water'] = await get_water(data)
    await message.answer(
        f"По вашим параметрам было рассчитано {round(data['calories'])} калорий. Настройка профиля завершена",
        reply_markup=ReplyKeyboardRemove()
    )
    users[message.from_user.id] = data

@dp.message(UserInfo.calories_auto, F.text.casefold() == "нет")
async def set_calories(message: Message, state: FSMContext):
    await state.set_state(UserInfo.calories)
    await message.answer(
        "Введите свою норму калорий:",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(UserInfo.calories)
async def finish_setting_profile(message: Message, state: FSMContext):
    data = await state.update_data(calories=float(message.text))
    data['water'] = await get_water(data)
    await state.clear()
    await message.answer("Настройка профиля завершена")
    users[message.from_user.id] = data

@dp.message(Command('log_water'))
async def log_water(message: Message, command: CommandObject):
    if command.args is None:
        await message.reply("Ошибка: не переданы аргументы")
        return

    users[message.from_user.id] = await check_date(users[message.from_user.id])
    users[message.from_user.id]['logging']['water'] += float(command.args)
    await message.reply("Записано")

@dp.message(Command('log_food'))
async def log_food(message: Message, command: CommandObject, state: FSMContext):
    if command.args is None:
        await message.reply("Ошибка: не переданы аргументы")
        return
    await state.set_state(Food.food)

    calories = await get_calories(command.args)
    await state.update_data(food=calories)

    await message.reply(f"{command.args.capitalize()} — {round(calories)} ккал на 100 г. Сколько граммов вы съели?")
    users[message.from_user.id] = await check_date(users[message.from_user.id])

@dp.message(Food.food)
async def log_gramms(message: Message, state: FSMContext):
    calories = await state.get_value('food')
    calories *= float(message.text) / 100
    users[message.from_user.id]['logging']['calories'] += calories
    await state.clear()
    await message.reply(f"Записано: {round(calories)} ккал.")

@dp.message(Command('log_workout'))
async def log_workout(message: Message, command: CommandObject):
    if command.args is None:
        await message.reply("Ошибка: не переданы аргументы")
        return
    workout, duration = command.args.split()
    users[message.from_user.id] = await check_date(users[message.from_user.id])
    burnt_calories = (await get_workout_calories(workout)) * float(duration) / 60
    users[message.from_user.id]['logging']['calories_burnt'] += burnt_calories
    users[message.from_user.id]['logging']['water_spent'] += 200 * (float(duration) // 30)
    await message.reply(command.args.capitalize() + f' — {round(burnt_calories)} ккал.')
    if float(duration) >= 30:
        await message.reply(f'Дополнительно: выпейте {round(200 * (float(duration) // 30))} мл воды.')

@dp.message(Command('check_progress'))
async def check_progress(message: Message):
    users[message.from_user.id] = await check_date(users[message.from_user.id])
    data = users[message.from_user.id]
    await message.reply(f'''Вода:
    - Выпито: {round(data['logging']['water'])} мл из {round(data['water'] + data['logging']['water_spent'])} мл.
    - Осталось: {round(max(0, data['water'] + data['logging']['water_spent'] - data['logging']['water']))} мл.

Калории:
    - Потреблено: {round(data['logging']['calories'])} ккал из {round(data['calories'])} ккал.
    - Сожжено: {round(data['logging']['calories_burnt'])} ккал.
    - Баланс: {round(data['calories'] + data['logging']['calories_burnt'] - data['logging']['calories'])} ккал.''')


async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
