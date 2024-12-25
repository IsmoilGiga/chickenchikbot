import random
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import sqlite3

logging.basicConfig(level=logging.INFO)

def init_db():
    conn = sqlite3.connect('chicken_chick_bot.db')
    cursor = conn.cursor()
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            phone TEXT,
            product TEXT,
            weight REAL,
            quantity INTEGER,
            price REAL,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

PHOTO_IDS = {
    "joja": "https://png.pngtree.com/png-vector/20240204/ourmid/pngtree-chick-image-with-transparency-png-image_11540471.png",
    "tovuq": "https://st.depositphotos.com/1784872/1392/i/450/depositphotos_13927400-stock-photo-chicken-isolated-on-white.jpg"
}

API_TOKEN = "7857180220:AAGvYEcpdDwcHqRR0P8sfLpEsVlFxqFt_8U"
ADMIN_CHAT_ID = "1210843660"
bot = Bot(token=API_TOKEN, proxy='http://proxy.server:3128')
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    klaviatura = ReplyKeyboardMarkup(resize_keyboard=True)
    klaviatura.add(KeyboardButton("Tovuq/Jo'ja sotib olish"))
    klaviatura.add(KeyboardButton("Telefon raqam yuborish", request_contact=True))
    await message.answer("Assalomu aleykum! 'Tovuq/Jo'ja sotib olish' tugmasini bosing", reply_markup=klaviatura)

user_data = {}

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def handle_contact(message: types.Message):
    user_data[message.from_user.id] = {
        "phone": message.contact.phone_number
    }
    await message.answer("Telefon raqamingiz saqlandi! Endi buyurtma berishingiz mumkin.")

@dp.message_handler(lambda message: message.text == "Tovuq/Jo'ja sotib olish")
async def buy_chicken(message: types.Message):
    klaviatura = InlineKeyboardMarkup()
    klaviatura.add(InlineKeyboardButton("Jo'ja", callback_data="joja"))
    klaviatura.add(InlineKeyboardButton("Tovuq", callback_data="tovuq"))
    await message.answer("Qaysi mahsulotni sotib olishni xohlaysiz?", reply_markup=klaviatura)

@dp.callback_query_handler(lambda c: c.data in ["joja", "tovuq"])
async def handle_selection(callback_query: types.CallbackQuery):
    mahsulot = "Jo'ja" if callback_query.data == "joja" else "Tovuq"
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Foydalanuvchi"

    photo_url = PHOTO_IDS[callback_query.data]
    await bot.send_photo(user_id, photo=photo_url, caption=f"Siz {mahsulot} tanladingiz. Mahsulotning og'irligi va narxi hisoblanmoqda.")

    if callback_query.data == "joja":
        ogirlik = round(random.uniform(0.7, 1), 2)
        narx_kg = random.randint(8000, 10000)
    else:
        ogirlik = round(random.uniform(1, 5), 2)
        narx_kg = random.randint(17000, 20000)

    jami_narx = ogirlik * narx_kg

    markup = InlineKeyboardMarkup()
    for i in range(1, 6):
        markup.add(InlineKeyboardButton(f"{i} dona", callback_data=f"quantity_{callback_query.data}_{ogirlik}_{narx_kg}_{jami_narx}_{i}"))

    await bot.send_message(
        user_id,
        f"Buyurtmangiz:\n"
        f"Mahsulot: {mahsulot}\n"
        f"Og'irlik: {ogirlik} kg\n"
        f"Kg narxi: {narx_kg} so'm\n"
        f"Jami narx: {jami_narx} so'm.\n"
        f"Iltimos, qancha dona buyurtma berishingizni tanlang.",
        reply_markup=markup
    )

@dp.callback_query_handler(lambda c: c.data.startswith("quantity_"))
async def handle_quantity(callback_query: types.CallbackQuery):
    data = callback_query.data.split("_")
    product, weight, price_per_kg, total_price, quantity = data[1], float(data[2]), float(data[3]), float(data[4]), int(data[5])
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Foydalanuvchi"
    phone = user_data.get(user_id, {}).get("phone", "Noma'lum")

    conn = sqlite3.connect('chicken_chick_bot.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO orders (username, phone, product, weight, quantity, price, status) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   (username, phone, product, weight, quantity, total_price * quantity, "Tasdiqlangan"))
    conn.commit()
    conn.close()

    conn = sqlite3.connect('chicken_chick_bot.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT SUM(weight), SUM(price) FROM orders WHERE product = ?", (product,))
    total_weight, total_income = cursor.fetchone()
    conn.close()

    await bot.send_message(ADMIN_CHAT_ID, f"Buyurtma tasdiqlandi: @{username}\nTelefon: {phone}\nMahsulot: {product}\nOg'irlik: {weight} kg\nDona: {quantity}\nJami narx: {total_price * quantity} so'm.\n\nJami sotilgan {product}: {total_weight} kg\nJami tushum: {total_income} so'm.")
    await bot.send_message(user_id, 
                           f"Buyurtmangiz tasdiqlandi:\n"
                           f"Mahsulot: {product}\n"
                           f"Og'irlik: {weight} kg\n"
                           f"Dona: {quantity}\n"
                           f"Jami narx: {total_price * quantity} so'm.\n\nRahmat! Sizning buyurtmangiz administrator tomonidan tasdiqlandi.")

if __name__ == '__main__':
    init_db()
    executor.start_polling(dp, skip_updates=True)
