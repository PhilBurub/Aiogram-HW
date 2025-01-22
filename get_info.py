import translate
import aiohttp

from conf import food_api_token, temp_api_token, workout_api_token

translator = translate.Translator(to_lang='en', from_lang='ru')
food_api_url = 'https://api.calorieninjas.com/v1/nutrition?query='
temp_api_url = 'http://api.openweathermap.org/'
workout_api_url = "https://calories-burned-by-api-ninjas.p.rapidapi.com/v1/caloriesburned"


async def get_temp(city):
    city_query = translator.translate(city)

    async with aiohttp.ClientSession() as session:
        async with session.get(temp_api_url + f'geo/1.0/direct?q={city_query}&limit=1&appid={temp_api_token}') as resp:
            coords = (await resp.json())[0]

        async with session.get(
                temp_api_url + f'data/2.5/weather?lat={coords["lat"]}&lon={coords["lon"]}&appid={temp_api_token}',
                params={'units': 'metric'}
        ) as resp:
            return (await resp.json())['main']['temp']


async def get_water(data):
    temp = await get_temp(data['city'])
    water = 30 * data['weight']
    water += (data['activity'] // 30) * 500
    if temp > 25:
        temp_coef = (temp - 25) // 5
        water += (500 + 100 * temp_coef)
    return water


async def get_calories(food):
    food_query = translator.translate(food) + ' 100g'
    async with aiohttp.ClientSession() as session:
        async with session.get(
                food_api_url + food_query,
                headers={'X-Api-Key': food_api_token}
        ) as response:
            return (await response.json())['items'][0]['calories']


async def get_workout_calories(workout):
    activity_query = {"activity": translator.translate(workout)}
    async with aiohttp.ClientSession() as session:
        async with session.get(
                workout_api_url,
                headers={
                    "x-rapidapi-key": workout_api_token,
                    "x-rapidapi-host": "calories-burned-by-api-ninjas.p.rapidapi.com"
                },
                params=activity_query
        ) as response:
            return (await response.json())[0]['calories_per_hour']
