import asyncio
import random
import json
import os
import aiohttp
from urllib.parse import quote
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

STATS_FILE = "dasha_stats.json"


class EnglishLesson(StatesGroup):
    waiting_for_answer = State()


class MiniGame(StatesGroup):
    waiting_for_choice = State()


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🐱 Котята"), KeyboardButton(text="🎬 Фильм на вечер")],
        [KeyboardButton(text="🎵 Музыка"), KeyboardButton(text="✨ Что-то интересное")],
        [KeyboardButton(text="🇬🇧 Учить английский"), KeyboardButton(text="🎮 Мини-игра")],
        [KeyboardButton(text="📊 Мой прогресс")],
    ],
    resize_keyboard=True
)

game_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🪨 Камень"), KeyboardButton(text="✂️ Ножницы"), KeyboardButton(text="📄 Бумага")],
        [KeyboardButton(text="🔙 Выйти из игры")],
    ],
    resize_keyboard=True
)

movies = [
    {"title": "Сумерки", "why": "Романтика + вампиры. Классика, если любишь такой вайб."},
    {"title": "Интервью с вампиром", "why": "Кинопоиск 7.9. Красивая и мрачная история."},
    {"title": "Дракула Брэма Стокера", "why": "Кинопоиск 7.8. Готическая любовь."},
    {"title": "Другой мир", "why": "Кинопоиск 7.6. Вампиры и оборотни, очень стильно."},
    {"title": "Век Адалин", "why": "IMDb 7.2. Девушка не стареет и ищет любовь."},
    {"title": "Тепло наших тел", "why": "IMDb 6.8. Милая романтика с необычным героем."},
    {"title": "Полночное солнце", "why": "Кинопоиск 7.0. Любовь, которая почти невозможна."},
    {"title": "Прекрасные создания", "why": "Как «Сумерки», только про ведьм."},
    {"title": "Виноваты звёзды", "why": "IMDb 7.7. Очень сильная и красивая история любви."},
    {"title": "Три метра над уровнем неба", "why": "IMDb 7.1. Страстная запретная любовь."},
    {"title": "Дневник памяти", "why": "IMDb 7.8. Трогательная романтика на весь вечер."},
    {"title": "Гордость и предубеждение (2005)", "why": "Красивая классика про любовь."},
    {"title": "Ла-Ла Ленд", "why": "IMDb 8.0. Музыка, город и большая любовь."},
    {"title": "Эдвард Руки-ножницы", "why": "IMDb 7.9. Готическая сказка про «другого»."},
    {"title": "Красавица и чудовище (2017)", "why": "Сказка: обычная девушка и загадочный герой."},
    {"title": "Амели", "why": "Добрый и необычный фильм про любовь."},
    {"title": "Титаник", "why": "IMDb 7.9. Большая история любви."},
    {"title": "Гарри Поттер и философский камень", "why": "Волшебство и уют."},
    {"title": "Гарри Поттер и узник Азкабана", "why": "Один из самых атмосферных фильмов серии."},
    {"title": "Хроники Нарнии: Лев, колдунья и волшебный шкаф", "why": "Доброе фэнтези про другой мир."},
    {"title": "Как приручить дракона", "why": "Драконы, дружба и приключения."},
    {"title": "Голодные игры", "why": "Кинопоиск 7.3. Сильная героиня и напряжённый мир."},
    {"title": "Душа", "why": "Красивый мультфильм про жизнь и мечты."},
    {"title": "Головоломка", "why": "Про эмоции, тёплый и умный мультфильм."},
    {"title": "Рататуй", "why": "Уютный фильм про мечту."},
    {"title": "Шрек", "why": "Если хочется посмеяться."},
    {"title": "Аватар", "why": "IMDb 7.9. Другой мир, природа и любовь."},
    {"title": "Начало", "why": "IMDb 8.8. Умное и красивое кино."},
    {"title": "Интерстеллар", "why": "IMDb 8.7. Космос, семья и сильные чувства."},
    {"title": "Один дома", "why": "Простой и смешной фильм."},
    {"title": "Паддингтон 2", "why": "Очень милый и добрый фильм."},
    {"title": "Практическая магия", "why": "Ведьмы, сёстры и романтика."},
    {"title": "Зачарованная", "why": "Сказка, которая попадает в реальный мир."},
    {"title": "Ходячий замок", "why": "Красивое аниме-фэнтези про ведьму и мага."},
    {"title": "Унесённые призраками", "why": "Волшебный другой мир."},
    {"title": "Дневники вампира", "why": "Кинопоиск 8.0. Сериал: школа, вампиры, треугольник."},
]

songs = [
    {"title": "Cardigan", "artist": "Taylor Swift"},
    {"title": "Lover", "artist": "Taylor Swift"},
    {"title": "August", "artist": "Taylor Swift"},
    {"title": "Cruel Summer", "artist": "Taylor Swift"},
    {"title": "Style", "artist": "Taylor Swift"},
    {"title": "Vampire", "artist": "Olivia Rodrigo"},
    {"title": "Drivers License", "artist": "Olivia Rodrigo"},
    {"title": "Good Luck, Babe!", "artist": "Chappell Roan"},
    {"title": "Espresso", "artist": "Sabrina Carpenter"},
    {"title": "Nonsense", "artist": "Sabrina Carpenter"},
    {"title": "Birds of a Feather", "artist": "Billie Eilish"},
    {"title": "What Was I Made For?", "artist": "Billie Eilish"},
    {"title": "Happier Than Ever", "artist": "Billie Eilish"},
    {"title": "Summertime Sadness", "artist": "Lana Del Rey"},
    {"title": "Video Games", "artist": "Lana Del Rey"},
    {"title": "Young and Beautiful", "artist": "Lana Del Rey"},
    {"title": "That's So True", "artist": "Gracie Abrams"},
    {"title": "I Love You, I'm Sorry", "artist": "Gracie Abrams"},
    {"title": "As It Was", "artist": "Harry Styles"},
    {"title": "Sign of the Times", "artist": "Harry Styles"},
    {"title": "Watermelon Sugar", "artist": "Harry Styles"},
    {"title": "Easy On Me", "artist": "Adele"},
    {"title": "Someone Like You", "artist": "Adele"},
    {"title": "Set Fire to the Rain", "artist": "Adele"},
    {"title": "Shallow", "artist": "Lady Gaga & Bradley Cooper"},
    {"title": "Die With A Smile", "artist": "Lady Gaga & Bruno Mars"},
    {"title": "Just the Way You Are", "artist": "Bruno Mars"},
    {"title": "Levitating", "artist": "Dua Lipa"},
    {"title": "Don't Start Now", "artist": "Dua Lipa"},
    {"title": "Flowers", "artist": "Miley Cyrus"},
    {"title": "Perfect", "artist": "Ed Sheeran"},
    {"title": "Photograph", "artist": "Ed Sheeran"},
    {"title": "Yellow", "artist": "Coldplay"},
    {"title": "The Scientist", "artist": "Coldplay"},
    {"title": "Fix You", "artist": "Coldplay"},
    {"title": "Do I Wanna Know?", "artist": "Arctic Monkeys"},
    {"title": "I Wanna Be Yours", "artist": "Arctic Monkeys"},
    {"title": "Sweater Weather", "artist": "The Neighbourhood"},
    {"title": "Apocalypse", "artist": "Cigarettes After Sex"},
    {"title": "Heavenly", "artist": "Cigarettes After Sex"},
    {"title": "Night Changes", "artist": "One Direction"},
    {"title": "What Makes You Beautiful", "artist": "One Direction"},
    {"title": "Stay With Me", "artist": "Sam Smith"},
    {"title": "I'm Not The Only One", "artist": "Sam Smith"},
    {"title": "Stitches", "artist": "Shawn Mendes"},
    {"title": "Treat You Better", "artist": "Shawn Mendes"},
    {"title": "Skinny Love", "artist": "Birdy"},
    {"title": "Another Love", "artist": "Tom Odell"},
    {"title": "Let Her Go", "artist": "Passenger"},
    {"title": "Somewhere Only We Know", "artist": "Keane"},
    {"title": "Chasing Cars", "artist": "Snow Patrol"},
    {"title": "All of Me", "artist": "John Legend"},
    {"title": "A Thousand Years", "artist": "Christina Perri"},
    {"title": "Unstoppable", "artist": "Sia"},
    {"title": "Chandelier", "artist": "Sia"},
    {"title": "Radioactive", "artist": "Imagine Dragons"},
    {"title": "Demons", "artist": "Imagine Dragons"},
]

lessons = [
    {"wrong": "She go to school every day.", "correct": "She goes to school every day.", "explanation": "После he/she/it глагол получает -s."},
    {"wrong": "I have 20 years.", "correct": "I am 20 years old.", "explanation": "Говорим 'I am ... years old'."},
    {"wrong": "He don't like coffee.", "correct": "He doesn't like coffee.", "explanation": "С he/she/it — doesn't."},
    {"wrong": "There is many people.", "correct": "There are many people.", "explanation": "People — множественное число."},
    {"wrong": "I am agree with you.", "correct": "I agree with you.", "explanation": "'am' не нужен."},
    {"wrong": "She can to swim.", "correct": "She can swim.", "explanation": "После can не ставим to."},
    {"wrong": "He is doctor.", "correct": "He is a doctor.", "explanation": "Нужен артикль a."},
    {"wrong": "We was happy.", "correct": "We were happy.", "explanation": "С we используем were."},
    {"wrong": "She didn't went.", "correct": "She didn't go.", "explanation": "После didn't — первая форма глагола."},
    {"wrong": "The news are good.", "correct": "The news is good.", "explanation": "News — неисчисляемое."},
]

praises = ["Молодец, Даша! 💖", "Отлично! 🌸", "Супер! ✨", "Правильно! 💕", "Умница! 🌟"]
greetings = ["Привет, Даша! 💖", "Привееет, Даша! 🌸", "Даша, привет! ✨", "Хей, Даша! 😊"]
random_replies = ["Я тут 💕", "Слушаю тебя 🌸", "Ты милая 💖", "Я рядом 🧸"]


def load_stats():
    default = {"correct": 0, "lessons_completed": 0, "games_played": 0, "games_won": 0}
    if not os.path.exists(STATS_FILE):
        return default
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key, value in default.items():
                data.setdefault(key, value)
            return data
    except Exception:
        return default


def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def normalize(text: str) -> str:
    return " ".join(text.lower().strip().replace(".", "").replace("!", "").replace("?", "").split())


async def get_random_cat():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search", timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data[0]["url"]
    except Exception:
        return None


async def get_random_fact():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://uselessfacts.jsph.pl/api/v2/facts/random", timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("text")
    except Exception:
        return None


async def translate_to_russian(text: str):
    try:
        url = f"https://api.mymemory.translated.net/get?q={quote(text)}&langpair=en|ru"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("responseData", {}).get("translatedText")
    except Exception:
        return None


@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(random.choice(greetings), reply_markup=main_keyboard)


@dp.message(F.text == "🐱 Котята")
async def send_cat(message: types.Message, state: FSMContext):
    await state.clear()
    photo = await get_random_cat()
    if photo:
        await message.answer_photo(photo=photo, caption="Держи котика 🥰")
    else:
        await message.answer("Котики спят 😴")


@dp.message(F.text == "🎬 Фильм на вечер")
async def random_movie(message: types.Message, state: FSMContext):
    await state.clear()
    movie = random.choice(movies)
    await message.answer(
        f"🎬 Сегодня можно посмотреть:\n\n"
        f"<b>{movie['title']}</b>\n"
        f"{movie['why']}\n\n"
        f"Если не зайдёт — нажми кнопку ещё раз 💫",
        parse_mode="HTML",
    )


@dp.message(F.text == "🎵 Музыка")
async def random_song(message: types.Message, state: FSMContext):
    await state.clear()
    song = random.choice(songs)
    query = f"{song['artist']} {song['title']}"
    link = "https://www.youtube.com/results?search_query=" + quote(query)
    await message.answer(
        f"🎵 Сегодня можно послушать:\n\n"
        f"<b>{song['artist']} — {song['title']}</b>\n\n"
        f"<a href=\"{link}\">Открыть на YouTube</a>\n\n"
        f"Если не зайдёт — нажми кнопку ещё раз 💫",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@dp.message(F.text == "✨ Что-то интересное")
async def interesting_fact(message: types.Message, state: FSMContext):
    await state.clear()
    fact = await get_random_fact()
    if fact:
        translated = await translate_to_russian(fact)
        await message.answer(f"✨ {translated or fact}")
    else:
        await message.answer("Факты отдыхают 😴")


@dp.message(F.text == "📊 Мой прогресс")
async def show_progress(message: types.Message, state: FSMContext):
    await state.clear()
    stats = load_stats()
    text = (
        f"📊 <b>Твой прогресс:</b>\n\n"
        f"✅ Английский: {stats['correct']}\n"
        f"📚 Уроков: {stats['lessons_completed']}\n"
        f"🎮 Игр: {stats['games_played']} (побед: {stats['games_won']})"
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "🇬🇧 Учить английский")
async def start_english(message: types.Message, state: FSMContext):
    await state.clear()
    shuffled = lessons.copy()
    random.shuffle(shuffled)
    await state.set_state(EnglishLesson.waiting_for_answer)
    await state.update_data(lessons=shuffled, current=0, correct_in_session=0)
    current = shuffled[0]
    await message.answer(
        f"🇬🇧 Исправь ошибку:\n\n<code>{current['wrong']}</code>\n\nНапиши стоп чтобы выйти",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )


@dp.message(EnglishLesson.waiting_for_answer)
async def check_english(message: types.Message, state: FSMContext):
    user_answer = message.text.strip()
    if user_answer.lower() in ["стоп", "меню", "выйти", "stop"]:
        data = await state.get_data()
        await state.clear()
        await message.answer(
            f"Урок закончен! Правильных: {data.get('correct_in_session', 0)}",
            reply_markup=main_keyboard,
        )
        return

    data = await state.get_data()
    lessons_list = data["lessons"]
    current_index = data["current"]
    correct_in_session = data.get("correct_in_session", 0)
    current_lesson = lessons_list[current_index]
    stats = load_stats()

    if normalize(user_answer) == normalize(current_lesson["correct"]):
        correct_in_session += 1
        stats["correct"] += 1
        save_stats(stats)
        if current_index + 1 < len(lessons_list):
            next_lesson = lessons_list[current_index + 1]
            await state.update_data(current=current_index + 1, correct_in_session=correct_in_session)
            await message.answer(
                f"{random.choice(praises)}\n\n{current_lesson['explanation']}\n\nСледующее:\n<code>{next_lesson['wrong']}</code>",
                parse_mode="HTML",
            )
        else:
            stats["lessons_completed"] += 1
            save_stats(stats)
            await state.clear()
            await message.answer(
                f"🎉 Урок пройден! Правильных: {correct_in_session} 💖",
                reply_markup=main_keyboard,
            )
    else:
        await message.answer(
            f"Пока нет 😊\n{current_lesson['explanation']}\n\nПопробуй:\n<code>{current_lesson['wrong']}</code>",
            parse_mode="HTML",
        )


@dp.message(F.text == "🎮 Мини-игра")
async def start_game(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(MiniGame.waiting_for_choice)
    await message.answer("🎮 Камень-ножницы-бумага!", reply_markup=game_keyboard)


@dp.message(MiniGame.waiting_for_choice)
async def play_game(message: types.Message, state: FSMContext):
    user_choice = message.text.strip()
    if user_choice == "🔙 Выйти из игры":
        await state.clear()
        await message.answer("Вышли 🌸", reply_markup=main_keyboard)
        return

    options = {"🪨 Камень": "камень", "✂️ Ножницы": "ножницы", "📄 Бумага": "бумага"}
    if user_choice not in options:
        return

    user = options[user_choice]
    bot_choice = random.choice(["камень", "ножницы", "бумага"])
    stats = load_stats()
    stats["games_played"] += 1

    if user == bot_choice:
        result = "Ничья!"
    elif (
        (user == "камень" and bot_choice == "ножницы")
        or (user == "ножницы" and bot_choice == "бумага")
        or (user == "бумага" and bot_choice == "камень")
    ):
        result = "Ты победила! 🎉"
        stats["games_won"] += 1
    else:
        result = "Я победила!"

    save_stats(stats)
    await message.answer(f"Ты: {user}\nЯ: {bot_choice}\n\n{result}")


@dp.message()
async def any_message(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(random.choice(random_replies), reply_markup=main_keyboard)


async def main():
    if not TOKEN:
        print("Ошибка: не найден TOKEN")
        return
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
