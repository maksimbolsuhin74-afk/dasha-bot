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


class MovieQuiz(StatesGroup):
    waiting_for_answer = State()


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🐱 Котик чтобы не грустила")],
        [KeyboardButton(text="🔮 Предсказание на день"), KeyboardButton(text="✨ Что-то интересное")],
        [KeyboardButton(text="🇬🇧 Учить английский"), KeyboardButton(text="🎬 Викторина по фильмам")],
        [KeyboardButton(text="🎮 Мини-игра"), KeyboardButton(text="📊 Мой прогресс")],
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

movie_questions = [
    {
        "question": "В каком фильме главный герой говорит: «Я буду обратно»?",
        "options": ["Терминатор", "Назад в будущее", "Хищник", "Рэмбо"],
        "correct": "Терминатор",
    },
    {
        "question": "Как зовут главного героя фильма «Гарри Поттер»?",
        "options": ["Гарри Поттер", "Рон Уизли", "Драко Малфой", "Невилл Долгопупс"],
        "correct": "Гарри Поттер",
    },
    {
        "question": "Какой мультфильм про игрушки, которые оживают?",
        "options": ["Корпорация монстров", "История игрушек", "Шрек", "Ледниковый период"],
        "correct": "История игрушек",
    },
    {
        "question": "В каком фильме есть персонаж по имени Джокер?",
        "options": ["Мстители", "Тёмный рыцарь", "Человек-паук", "Железный человек"],
        "correct": "Тёмный рыцарь",
    },
    {
        "question": "Кто сыграл Джека в фильме «Титаник»?",
        "options": ["Брэд Питт", "Леонардо ДиКаприо", "Том Круз", "Джонни Депп"],
        "correct": "Леонардо ДиКаприо",
    },
    {
        "question": "В каком мультфильме рыбка ищет своего сына?",
        "options": ["В поисках Немо", "Рыбка Поньо", "Акулы", "Русалочка"],
        "correct": "В поисках Немо",
    },
    {
        "question": "Как зовут главного злодея в «Короле Льве»?",
        "options": ["Муфаса", "Шрам", "Тимон", "Пуба"],
        "correct": "Шрам",
    },
    {
        "question": "В каком фильме есть фраза: «Да пребудет с тобой Сила»?",
        "options": ["Звёздные войны", "Звёздный путь", "Дюна", "Стражи Галактики"],
        "correct": "Звёздные войны",
    },
    {
        "question": "Какой фильм про мальчика, который не хочет взрослеть?",
        "options": ["Чарли и шоколадная фабрика", "Питер Пэн", "Хроники Нарнии", "Золотой компас"],
        "correct": "Питер Пэн",
    },
    {
        "question": "В каком фильме главный герой — зелёный огр?",
        "options": ["Шрек", "Монстры на каникулах", "Корпорация монстров", "Город героев"],
        "correct": "Шрек",
    },
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
compliments = ["Ты сегодня особенно красивая 💕", "Сегодня тебя ждёт что-то приятное ✨", "Ты солнышко ☀️"]
random_replies = ["Я тут 💕", "Слушаю тебя 🌸", "Ты милая 💖", "Я рядом 🧸"]


def load_stats():
    if not os.path.exists(STATS_FILE):
        return {
            "correct": 0,
            "lessons_completed": 0,
            "games_played": 0,
            "games_won": 0,
            "quiz_correct": 0,
            "quiz_played": 0,
        }
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("quiz_correct", 0)
            data.setdefault("quiz_played", 0)
            return data
    except Exception:
        return {
            "correct": 0,
            "lessons_completed": 0,
            "games_played": 0,
            "games_won": 0,
            "quiz_correct": 0,
            "quiz_played": 0,
        }


def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def normalize(text: str) -> str:
    return " ".join(
        text.lower().strip().replace(".", "").replace("!", "").replace("?", "").split()
    )


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


@dp.message(F.text == "🐱 Котик чтобы не грустила")
async def send_cat(message: types.Message, state: FSMContext):
    await state.clear()
    photo = await get_random_cat()
    if photo:
        await message.answer_photo(photo=photo, caption="Держи котика 🥰")
    else:
        await message.answer("Котики спят 😴")


@dp.message(F.text == "🔮 Предсказание на день")
async def prediction(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(random.choice(compliments))


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
        f"🎬 Викторина: {stats['quiz_correct']}\n"
        f"🎮 Игр: {stats['games_played']} (побед: {stats['games_won']})"
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "🎬 Викторина по фильмам")
async def start_movie_quiz(message: types.Message, state: FSMContext):
    await state.clear()
    questions = movie_questions.copy()
    random.shuffle(questions)
    await state.set_state(MovieQuiz.waiting_for_answer)
    await state.update_data(questions=questions, current=0, correct=0)

    q = questions[0]
    options = q["options"].copy()
    random.shuffle(options)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=opt)] for opt in options] + [[KeyboardButton(text="🔙 Выйти")]],
        resize_keyboard=True,
    )

    await message.answer(
        f"🎬 <b>Викторина!</b>\n\nВопрос 1:\n\n{q['question']}",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@dp.message(MovieQuiz.waiting_for_answer)
async def process_movie_answer(message: types.Message, state: FSMContext):
    answer = message.text.strip()
    if answer == "🔙 Выйти":
        data = await state.get_data()
        await state.clear()
        await message.answer(
            f"Викторина окончена! Правильных: {data.get('correct', 0)} 💖",
            reply_markup=main_keyboard,
        )
        return

    data = await state.get_data()
    questions = data["questions"]
    current = data["current"]
    correct = data["correct"]
    q = questions[current]

    stats = load_stats()

    if answer == q["correct"]:
        correct += 1
        stats["quiz_correct"] += 1
        save_stats(stats)
        reply = random.choice(praises)
    else:
        reply = f"Неправильно. Ответ: <b>{q['correct']}</b>"

    if current + 1 < len(questions):
        next_q = questions[current + 1]
        options = next_q["options"].copy()
        random.shuffle(options)
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=opt)] for opt in options] + [[KeyboardButton(text="🔙 Выйти")]],
            resize_keyboard=True,
        )
        await state.update_data(current=current + 1, correct=correct)
        await message.answer(
            f"{reply}\n\nВопрос {current + 2}:\n\n{next_q['question']}",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        stats["quiz_played"] += 1
        save_stats(stats)
        await state.clear()
        await message.answer(
            f"{reply}\n\n🏁 Конец! Правильных: {correct} из {len(questions)} 💖",
            parse_mode="HTML",
            reply_markup=main_keyboard,
        )


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
