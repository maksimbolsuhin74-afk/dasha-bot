impimport asyncio
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

TOKEN = "8632894430:AAHTi0S4Wg22As_ox8oE9SuY4X0G6bY4nlk"  # ← Вставь новый токен!

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

STATS_FILE = "dasha_stats.json"

# ========== СОСТОЯНИЯ ==========
class EnglishLesson(StatesGroup):
    waiting_for_answer = State()

class MiniGame(StatesGroup):
    waiting_for_choice = State()

# ========== КЛАВИАТУРЫ ==========
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🐱 Котик чтобы не грустила")],
        [KeyboardButton(text="🔮 Предсказание на день"), KeyboardButton(text="✨ Что-то интересное")],
        [KeyboardButton(text="🇬🇧 Учить английский"), KeyboardButton(text="🎮 Мини-игра")],
        [KeyboardButton(text="📊 Мой прогресс")]
    ],
    resize_keyboard=True
)

game_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🪨 Камень"), KeyboardButton(text="✂️ Ножницы"), KeyboardButton(text="📄 Бумага")],
        [KeyboardButton(text="🔙 Выйти из игры")]
    ],
    resize_keyboard=True
)

# ========== УРОКИ АНГЛИЙСКОГО (25 штук) ==========
lessons = [
    {"wrong": "She go to school every day.", "correct": "She goes to school every day.", "explanation": "После he/she/it в Present Simple глагол получает -s/-es."},
    {"wrong": "I have 20 years.", "correct": "I am 20 years old.", "explanation": "Мы говорим 'I am ... years old', а не 'I have ... years'."},
    {"wrong": "He don't like coffee.", "correct": "He doesn't like coffee.", "explanation": "С he/she/it используем doesn't, а не don't."},
    {"wrong": "There is many people in the room.", "correct": "There are many people in the room.", "explanation": "People — множественное число, поэтому are."},
    {"wrong": "I am agree with you.", "correct": "I agree with you.", "explanation": "Agree — глагол, 'am' не нужен."},
    {"wrong": "She can to swim very well.", "correct": "She can swim very well.", "explanation": "После can/may/must частица to не ставится."},
    {"wrong": "I very like this movie.", "correct": "I like this movie very much.", "explanation": "Правильно: like ... very much / a lot."},
    {"wrong": "He is doctor.", "correct": "He is a doctor.", "explanation": "Перед профессией нужен артикль a/an."},
    {"wrong": "We was happy yesterday.", "correct": "We were happy yesterday.", "explanation": "С we/you/they в прошлом = were."},
    {"wrong": "She didn't went to the party.", "correct": "She didn't go to the party.", "explanation": "После did/didn't глагол в первой форме."},
    {"wrong": "I look forward to meet you.", "correct": "I look forward to meeting you.", "explanation": "После look forward to нужен герундий (-ing)."},
    {"wrong": "This is the most biggest house.", "correct": "This is the biggest house.", "explanation": "Biggest уже превосходная степень."},
    {"wrong": "She is more taller than me.", "correct": "She is taller than me.", "explanation": "Taller уже сравнительная степень, more не нужен."},
    {"wrong": "I didn t saw him yesterday.", "correct": "I didn't see him yesterday.", "explanation": "После didn't глагол в первой форме (see)."},
    {"wrong": "He has went to the shop.", "correct": "He has gone to the shop.", "explanation": "После has/have нужна третья форма глагола (gone)."},
    {"wrong": "My brother work in a bank.", "correct": "My brother works in a bank.", "explanation": "He/she/it + глагол с -s."},
    {"wrong": "I am living here since 2020.", "correct": "I have lived here since 2020.", "explanation": "С since используем Present Perfect."},
    {"wrong": "She told she was busy.", "correct": "She said she was busy.", "explanation": "Told нужно использовать с дополнением (told me)."},
    {"wrong": "I want that you help me.", "correct": "I want you to help me.", "explanation": "Правильная конструкция: want somebody to do something."},
    {"wrong": "He is good in English.", "correct": "He is good at English.", "explanation": "Мы говорим good at, а не good in."},
    {"wrong": "Despite of the rain, we went out.", "correct": "Despite the rain, we went out.", "explanation": "Despite используется без of."},
    {"wrong": "I suggest to go there.", "correct": "I suggest going there.", "explanation": "После suggest обычно герундий (-ing)."},
    {"wrong": "She is married with a doctor.", "correct": "She is married to a doctor.", "explanation": "Married to, а не married with."},
    {"wrong": "I have been knowing her for years.", "correct": "I have known her for years.", "explanation": "Know — глагол состояния, не используется в Continuous."},
    {"wrong": "The news are good.", "correct": "The news is good.", "explanation": "News — неисчисляемое, поэтому is."},
]

praises = [
    "Молодец, Даша! 💖 Правильно!",
    "Отлично! Ты умничка 🌸",
    "Супер! Всё верно ✨",
    "Правильно! Я горжусь тобой 💕",
    "Браво! Ты справляешься замечательно 🐻",
    "Идеально! Так держать 🌟",
    "Даша, ты просто космос! Всё правильно ☀️",
    "Умница! Продолжаем в том же духе 💞"
]

greetings = [
    "Привет, Даша! 💖",
    "Привееет, Даша! 🌸",
    "Даша, привет-привет! ✨",
    "Хей, Даша! Как дела? 😊",
    "Привет, солнышко Даша! ☀️",
    "Дашааа, привет! 💞",
    "Привет, моя хорошая Даша! 🧸",
    "Даша, ты тут? Привет! 🐻"
]

compliments = [
    "Сегодня тебя ждёт что-то очень приятное ✨",
    "Ты сегодня особенно красивая, Даша 💕",
    "Этот день принесёт тебе улыбки и хорошее настроение",
    "Вселенная сегодня на твоей стороне 🌟",
    "Ты заслуживаешь только самого лучшего сегодня",
    "Сегодня у тебя всё получится, даже лучше, чем планировала",
    "Кто-то будет думать о тебе с теплотой весь день 💖",
    "Ты — настоящее солнышко, и сегодня это особенно заметно"
]

random_replies = [
    "Я тут 💕",
    "Слушаю тебя, Даша 🌸",
    "Ты сегодня особенно милая 💖",
    "Просто хотела напомнить, что ты классная 🐻",
    "Я рядом 🧸",
    "Улыбнулась твоим сообщениям 💞",
    "Ты заслуживаешь самых тёплых слов ☀️"
]

# ========== РАБОТА С ПРОГРЕССОМ ==========
def load_stats():
    if not os.path.exists(STATS_FILE):
        return {"correct": 0, "lessons_completed": 0, "games_played": 0, "games_won": 0}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"correct": 0, "lessons_completed": 0, "games_played": 0, "games_won": 0}

def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

# ========== ФУНКЦИИ ==========
async def get_random_cat() -> str | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search", timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data[0]["url"]
    except:
        return None
    return None

async def get_random_fact() -> str | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://uselessfacts.jsph.pl/api/v2/facts/random", timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("text")
    except:
        return None
    return None

async def translate_to_russian(text: str) -> str | None:
    try:
        url = f"https://api.mymemory.translated.net/get?q={quote(text)}&langpair=en|ru"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("responseData", {}).get("translatedText")
    except:
        return None
    return None

def normalize(text: str) -> str:
    return " ".join(text.lower().strip().replace(".", "").replace("!", "").replace("?", "").replace("'", "").split())

# ========== ХЭНДЛЕРЫ ==========
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(random.choice(greetings), reply_markup=main_keyboard)

@dp.message(F.text == "🐱 Котик чтобы не грустила")
async def send_cat(message: types.Message, state: FSMContext):
    await state.clear()
    photo_url = await get_random_cat()
    if photo_url:
        await message.answer_photo(photo=photo_url, caption="Держи котика, чтобы не грустила 🥰")
    else:
        await message.answer("Котики сейчас спят 😴 Попробуй ещё раз")

@dp.message(F.text == "🔮 Предсказание на день")
async def prediction(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(random.choice(compliments))

@dp.message(F.text == "✨ Что-то интересное")
async def interesting_fact(message: types.Message, state: FSMContext):
    await state.clear()
    fact = await get_random_fact()
    if not fact:
        await message.answer("Факты сейчас отдыхают 😴")
        return
    translated = await translate_to_russian(fact)
    await message.answer(f"✨ Интересный факт:\n\n{translated or fact}")

@dp.message(F.text == "📊 Мой прогресс")
async def show_progress(message: types.Message, state: FSMContext):
    await state.clear()
    stats = load_stats()
    text = (
        "📊 <b>Твой прогресс, Даша:</b>\n\n"
        f"✅ Правильных ответов по английскому: <b>{stats['correct']}</b>\n"
        f"📚 Уроков полностью пройдено: <b>{stats['lessons_completed']}</b>\n"
        f"🎮 Сыграно мини-игр: <b>{stats['games_played']}</b>\n"
        f"🏆 Побед в играх: <b>{stats['games_won']}</b>\n\n"
        "Ты молодец! Продолжай в том же духе 💖"
    )
    await message.answer(text, parse_mode="HTML")

# ========== АНГЛИЙСКИЙ ==========
@dp.message(F.text == "🇬🇧 Учить английский")
async def start_english(message: types.Message, state: FSMContext):
    await state.clear()
    shuffled = lessons.copy()
    random.shuffle(shuffled)
    await state.set_state(EnglishLesson.waiting_for_answer)
    await state.update_data(lessons=shuffled, current=0, correct_in_session=0)
    
    current = shuffled[0]
    text = (
        "🇬🇧 <b>Начинаем урок английского!</b>\n\n"
        "Я даю предложения с ошибками — напиши правильный вариант.\n"
        "Чтобы выйти — напиши <b>стоп</b>.\n\n"
        f"✏️ Исправь ошибку:\n\n<code>{current['wrong']}</code>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

@dp.message(EnglishLesson.waiting_for_answer)
async def check_answer(message: types.Message, state: FSMContext):
    user_answer = message.text.strip()
    
    if user_answer.lower() in ["стоп", "меню", "выйти", "хватит", "stop"]:
        data = await state.get_data()
        correct = data.get("correct_in_session", 0)
        await state.clear()
        await message.answer(
            f"Урок закончен! В этот раз ты правильно исправила {correct} предложений 💖",
            reply_markup=main_keyboard
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
        
        praise = random.choice(praises)
        
        if current_index + 1 < len(lessons_list):
            next_lesson = lessons_list[current_index + 1]
            await state.update_data(current=current_index + 1, correct_in_session=correct_in_session)
            text = (
                f"{praise}\n\n"
                f"📝 {current_lesson['explanation']}\n\n"
                f"Следующее:\n<code>{next_lesson['wrong']}</code>"
            )
            await message.answer(text, parse_mode="HTML")
        else:
            stats["lessons_completed"] += 1
            save_stats(stats)
            await state.clear()
            await message.answer(
                f"{praise}\n\n"
                f"🎉 Ты прошла весь урок! Правильных ответов: {correct_in_session} из {len(lessons_list)}\n"
                f"Всего уроков пройдено: {stats['lessons_completed']}\n\n"
                "Ты большая умница, Даша! 💖",
                reply_markup=main_keyboard
            )
    else:
        text = (
            "Пока неправильно 😊\n\n"
            f"💡 Подсказка: {current_lesson['explanation']}\n\n"
            f"Попробуй ещё раз:\n<code>{current_lesson['wrong']}</code>"
        )
        await message.answer(text, parse_mode="HTML")

# ========== МИНИ-ИГРА ==========
@dp.message(F.text == "🎮 Мини-игра")
async def start_game(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(MiniGame.waiting_for_choice)
    await message.answer(
        "🎮 <b>Камень-ножницы-бумага!</b>\n\nВыбери свой вариант:",
        parse_mode="HTML",
        reply_markup=game_keyboard
    )

@dp.message(MiniGame.waiting_for_choice)
async def play_game(message: types.Message, state: FSMContext):
    user_choice = message.text.strip()
    
    if user_choice == "🔙 Выйти из игры":
        await state.clear()
        await message.answer("Вышли из игры 🌸", reply_markup=main_keyboard)
        return
    
    options = {
        "🪨 Камень": "камень",
        "✂️ Ножницы": "ножницы",
        "📄 Бумага": "бумага"
    }
    
    if user_choice not in options:
        await message.answer("Выбери одну из кнопок 😊")
        return
    
    user = options[user_choice]
    bot_choice = random.choice(["камень", "ножницы", "бумага"])
    
    emojis = {"камень": "🪨", "ножницы": "✂️", "бумага": "📄"}
    
    # Определяем победителя
    result = ""
    stats = load_stats()
    stats["games_played"] += 1
    
    if user == bot_choice:
        result = "Ничья! 🤝"
    elif (user == "камень" and bot_choice == "ножницы") or \
         (user == "ножницы" and bot_choice == "бумага") or \
         (user == "бумага" and bot_choice == "камень"):
        result = "Ты победила! 🎉💖"
        stats["games_won"] += 1
    else:
        result = "Я победила! 😏 Но ты всё равно молодец"
    
    save_stats(stats)
    
    text = (
        f"Твой выбор: {emojis[user]} {user}\n"
        f"Мой выбор: {emojis[bot_choice]} {bot_choice}\n\n"
        f"<b>{result}</b>"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message()
async def any_message(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(random.choice(random_replies), reply_markup=main_keyboard)

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())