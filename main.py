import asyncio
import logging
import random
import string
from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton
)

USER_BOT_TOKEN = "9145697620:AAFH7S9qA6THJOCB7XS7e_mSKvpN9oX2YtY"
ADMIN_BOT_TOKEN = "8928751621:AAFYkO8mzPDhOiA2w3HCz247_9b1rvo-b84"
HELP_BOT_TOKEN = "9177728669:AAGyoZovonS9OUO2JX8Hegr8QJiBzmJylZE"
REQUIRED_CHANNEL = "https://t.me/EthioGtask"
ADMIN_SECRET_CODE = "192155"
ADMIN_USER_ID = 7215907955

logging.basicConfig(level=logging.INFO)

users_db = {} 
tasks_db = {} 
withdrawals_db = []
admins_logged_in = set()

class UserStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_help_msg = State()

LANG = {
    "am": {
        "welcome": "👋 ሰላም እንቁጣጣ! እንኳን ወደ **Ethio G Task** በደህና መጡ 🚀\n\nቦቱን ለመጠቀም መጀመሪያ ከታች ያለውን ቻናል Join ማድረግ አለብዎት።",
        "join_btn": "📢 ቻናል Join አድርግ",
        "joined_check": "✅ ቻናል ጆይን አድርግሻለሁ",
        "not_joined": "❌ እባክዎ መጀመሪያ ቻናላችንን Join ያድርጉ!",
        "choose_lang": "🌍 እባክዎ የሚፈልጉትን ቋንቋ ይምረጡ / Please choose your language:",
        "main_menu": "🏠 ዋና ማውጫ (Main Menu)",
        "task_btn": "📋 Task (ስራዎች)",
        "balance_btn": "💰 Balance (ሂሳብ)",
        "invite_btn": "👥 Invite (ጋብዝ)",
        "setting_btn": "⚙️ Setting (ማስተካከያ)",
        "help_btn": "🆘 Help (እርዳታ)",
        "withdraw_btn": "💸 Withdraw (ገንዘብ ማውጣት)",
        "back_btn": "⬅️ ተመለስ",
        "email_gen_title": "📧 የተዘጋጀልዎ የጂሜይል መረጃ (ለመቅዳት ይጫኑ)",
        "verify_btn": "✅ ተፈትሾአል / ቼክ አድርግ",
        "cancel_btn": "❌ Task ተመለሰ",
        "balance_info": "💰 የእርስዎ ሂሳብ: **{balance} ብር**\n👥 የጋበዟቸው ሰዎች: {refs}\n💳 እስካሁን ያወጡት: {withdrawn} ብር",
        "withdraw_prompt": "📲 እባክዎ የቴሌብር (Telebirr) ስልክ ቁጥርዎን ይላኩ (ምሳሌ: 0911223344):",
        "withdraw_success": "✅ የገንዘብ ማውጣት ጥያቄዎ ተቀባይነት አግኝቷል! እባክዎ ይጠብቁ።",
        "min_withdraw": "⚠️ ገንዘብ ለማውጣት ቢያንስ 50 ብር ሊኖርዎት ይገባል!",
        "help_text": "🆘 **Ethio G Task Help Desk**\n\nቦቱ ካልሰራ ወይም ማንኛውም ችግር ካለ ከታች ባለው አገናኝ ያነጋግሩን።",
    },
    "en": {
        "welcome": "👋 Hello! Welcome to **Ethio G Task** 🚀\n\nPlease join our official channel first to continue.",
        "join_btn": "📢 Join Channel",
        "joined_check": "✅ I have joined",
        "not_joined": "❌ Please join the channel first!",
        "choose_lang": "🌍 Please choose your language:",
        "main_menu": "🏠 Main Menu",
        "task_btn": "📋 Tasks",
        "balance_btn": "💰 Balance",
        "invite_btn": "👥 Invite",
        "setting_btn": "⚙️ Settings",
        "help_btn": "🆘 Help",
        "withdraw_btn": "💸 Withdraw",
        "back_btn": "⬅️ Back",
        "email_gen_title": "📧 Your Generated Gmail Details (Click to Copy)",
        "verify_btn": "✅ Verify",
        "cancel_btn": "❌ Cancel Task",
        "balance_info": "💰 Your Balance: **{balance} ETB**\n👥 Invited Users: {refs}\n💳 Total Withdrawn: {withdrawn} ETB",
        "withdraw_prompt": "📲 Please send your Telebirr phone number (e.g., 0911223344):",
        "withdraw_success": "✅ Withdrawal request submitted! Please wait.",
        "min_withdraw": "⚠️ You need at least 50 ETB to withdraw!",
        "help_text": "🆘 **Ethio G Task Help Desk**\n\nIf the bot is not working, contact us below.",
    }
}

def get_user_lang(user_id):
    if user_id in users_db and "lang" in users_db[user_id]:
        return users_db[user_id]["lang"]
    return "am"

user_bot = Bot(token=USER_BOT_TOKEN)
user_dp = Dispatcher(storage=MemoryStorage())

def main_menu_keyboard(lang="am"):
    t = LANG[lang]
    kb = [
        [KeyboardButton(text=t["task_btn"]), KeyboardButton(text=t["balance_btn"])],
        [KeyboardButton(text=t["invite_btn"]), KeyboardButton(text=t["setting_btn"])],
        [KeyboardButton(text=t["help_btn"]), KeyboardButton(text=t["withdraw_btn"])]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@user_dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {"balance": 0.0, "refs": 0, "withdrawn": 0.0, "emails": 0, "lang": "am"}
    
    lang_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇪🇹 አማርኛ", callback_data="lang_am"), InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    await message.answer("✨ **Ethio G Task** ✨\n\n🌍 እባክዎ ቋንቋ ይምረጡ / Choose your language:", reply_markup=lang_kb)

@user_dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = callback.data.split("_")[1]
    if user_id not in users_db:
        users_db[user_id] = {"balance": 0.0, "refs": 0, "withdrawn": 0.0, "emails": 0}
    users_db[user_id]["lang"] = lang
    t = LANG[lang]

    join_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["join_btn"], url=REQUIRED_CHANNEL)],
        [InlineKeyboardButton(text=t["joined_check"], callback_data="check_join")]
    ])
    await callback.message.edit_text(t["welcome"], reply_markup=join_kb)

@user_dp.callback_query(F.data == "check_join")
async def check_channel_join(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    t = LANG[lang]
    await callback.message.delete()
    await callback.message.answer(f"🎉 እንኳን ደህና መጡ!\n\n{t['main_menu']}", reply_markup=main_menu_keyboard(lang))

@user_dp.message(F.text.in_(["📋 Task (ስራዎች)", "📋 Tasks"]))
async def handle_tasks(message: Message):
    user_id = message.from_user.id
    fn, ln = random.choice(["Abebe", "Kebede", "Dawit"]), random.choice(["Alemu", "Tadesse", "Bekele"])
    rand_num = random.randint(100, 999)
    gen_email = f"{fn.lower()}.{ln.lower()}{rand_num}@gmail.com"
    gen_pass = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    rec_email = f"recovery.{rand_num}@gmail.com"

    task_id = f"task_{user_id}_{random.randint(1000,9999)}"
    tasks_db[task_id] = {"user_id": user_id, "email": gen_email, "status": "pending", "name": f"{fn} {ln}"}

    text = (
        f"📧 **የተዘጋጀልዎ የጂሜይል መረጃ**\n\n"
        f"👤 First Name: `{fn}`\n👤 Last Name: `{ln}`\n"
        f"✉️ Email: `{gen_email}`\n🔑 Password: `{gen_pass}`\n🔄 Recovery: `{rec_email}`\n\n"
        f"⚠️ *ጂሜይሉን ከፈቱ በኋላ ከታች ያለውን አረጋግጥ ይጫኑ!*"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ አረጋግጥ (Verify)", callback_data=f"verify_{task_id}"),
         InlineKeyboardButton(text="❌ ተመለስ (Cancel)", callback_data=f"cancel_{task_id}")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@user_dp.callback_query(F.data.startswith("verify_"))
async def verify_email_task(callback: CallbackQuery):
    task_id = callback.data.split("_", 1)[1]
    user_id = callback.from_user.id
    if task_id in tasks_db and tasks_db[task_id]["status"] == "pending":
        tasks_db[task_id]["status"] = "verified"
        users_db[user_id]["balance"] += 10.0
        users_db[user_id]["emails"] += 1
        await callback.message.edit_text("✅ **በስተክክል ተረጋግጧል! 10 ብር ተጨምሯል! 🎉**")
    else:
        await callback.answer("⚠️ ይህ ስራ ቀድሞ ተጠናቋል!", show_alert=True)

@user_dp.callback_query(F.data.startswith("cancel_"))
async def cancel_email_task(callback: CallbackQuery):
    task_id = callback.data.split("_", 1)[1]
    if task_id in tasks_db:
        tasks_db[task_id]["status"] = "cancelled"
    await callback.message.edit_text("❌ **Task ተመልሷል**")

@user_dp.message(F.text.in_(["💰 Balance (ሂሳብ)", "💰 Balance"]))
async def handle_balance(message: Message):
    u = users_db.get(message.from_user.id, {"balance": 0.0, "refs": 0, "withdrawn": 0.0})
    await message.answer(f"💰 **Balance**\n\n💵 ቀሪ ሂሳብ: **{u['balance']} ብር**\n👥 ሪፈራል: **{u['refs']}**\n💳 የወጣ: **{u['withdrawn']} ብር**")

@user_dp.message(F.text.in_(["💸 Withdraw (ገንዘብ ማውጣት)", "💸 Withdraw"]))
async def handle_withdraw_start(message: Message, state: FSMContext):
    u = users_db.get(message.from_user.id, {"balance": 0.0})
    if u["balance"] < 50:
        await message.answer("⚠️ ገንዘብ ለማውጣት ቢያንስ 50 ብር ሊኖርዎት ይገባል!")
        return
    await state.set_state(UserStates.waiting_for_phone)
    await message.answer("📲 የቴሌብር ስልክ ቁጥርዎን ይላኩ (ምሳሌ: 0911223344):")

@user_dp.message(UserStates.waiting_for_phone)
async def process_withdraw_phone(message: Message, state: FSMContext):
    user_id = message.from_user.id
    u = users_db.get(user_id, {"balance": 0.0})
    amount = u["balance"]
    withdrawals_db.append({"user_id": user_id, "name": message.from_user.full_name, "phone": message.text, "amount": amount, "status": "Pending"})
    u["balance"] = 0.0
    u["withdrawn"] += amount
    await state.clear()
    await message.answer("✅ የቴሌብር ቁጥርዎ ተቀብለናል! እባክዎ ይጠብቁ።")

@user_dp.message(F.text.in_(["👥 Invite (ጋብዝ)", "👥 Invite"]))
async def handle_invite(message: Message):
    bot_info = await user_bot.get_me()
    await message.answer(f"👥 **መጋበዣ ሊንክዎ:**\n\nhttps://t.me/{bot_info.username}?start=ref_{message.from_user.id}\n\n1 ሰው ሲጋብዙ 5 ብር ያገኛሉ!")

@user_dp.message(F.text.in_(["⚙️ Setting (ማስተካከያ)", "⚙️ Settings"]))
async def handle_settings(message: Message):
    lang_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇪🇹 አማርኛ", callback_data="lang_am"), InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    await message.answer("⚙️ ቋንቋ መቀየር ከፈለጉ ይምረጡ:", reply_markup=lang_kb)

@user_dp.message(F.text.in_(["🆘 Help (እርዳታ)", "🆘 Help"]))
async def handle_help(message: Message):
    await message.answer(f"🆘 **Help Desk**\n\nእርዳታ ለማግኘት ቦታችንን ያነጋግሩ: t.me/{(await Bot(token=HELP_BOT_TOKEN).get_me()).username}")

admin_bot = Bot(token=ADMIN_BOT_TOKEN)
admin_dp = Dispatcher(storage=MemoryStorage())

@admin_dp.message(CommandStart())
async def admin_start(message: Message):
    await message.answer("🔐 እባክዎ የአስተዳዳሪ ኮድ (Password) ያስገቡ:")

@admin_dp.message()
async def admin_messages(message: Message):
    user_id = message.from_user.id
    text = message.text
    if user_id not in admins_logged_in:
        if text == ADMIN_SECRET_CODE:
            admins_logged_in.add(user_id)
            await message.answer("✅ ወደ አስተዳዳሪ ፓነል ገብተዋል ✅", reply_markup=ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text="📋 Task (የተሰሩ ስራዎች)"), KeyboardButton(text="💸 ለማውጣት ያሉ")],
                [KeyboardButton(text="ℹ️ መረጃ (Info)"), KeyboardButton(text="👥 ብዙ የሰራ ሰው")]
            ], resize_keyboard=True))
        else:
            await message.answer("❌ የተሳሳተ ኮድ!")
        return

    if text == "📋 Task (የተሰሩ ስራዎች)":
        res = "\n".join([f"👤 {d['name']} | ✉️ `{d['email']}` | Status: {d['status']}" for d in tasks_db.values()]) or "📭 የለም"
        await message.answer(f"📋 **Task List:**\n\n{res}", parse_mode="Markdown")
    elif text == "💸 ለማውጣት ያሉ":
        res = "\n".join([f"👤 {w['name']} | 📱 `{w['phone']}` | 💵 {w['amount']} ብር" for w in withdrawals_db]) or "📭 የለም"
        await message.answer(f"💸 **Withdrawals:**\n\n{res}", parse_model="Markdown")
    elif text == "ℹ️ መረጃ (Info)":
        await message.answer(f"📊 ተጠቃሚዎች: {len(users_db)} | ስራዎች: {len(tasks_db)}")
    elif text == "👥 ብዙ የሰራ ሰው":
        sorted_u = sorted(users_db.items(), key=lambda x: x[1].get("emails", 0), reverse=True)
        res = "\n".join([f"ID: `{uid}` - {u['emails']} emails" for uid, u in sorted_u[:5]]) or "📭 የለም"
        await message.answer(f"🏆 **Top Workers:**\n\n{res}", parse_model="Markdown")

help_bot = Bot(token=HELP_BOT_TOKEN)
help_dp = Dispatcher(storage=MemoryStorage())

@help_dp.message(CommandStart())
async def help_start(message: Message):
    await message.answer("🆘 **Help Bot**\n\nጥያቄዎትን እዚህ ይጻፉ:")

@help_dp.message()
async def help_forward(message: Message):
    await help_bot.send_message(ADMIN_USER_ID, f"📩 ከ ተጠቃሚ (`{message.from_user.id}`):\n\n{message.text}")
    await message.answer("✅ መልክቶን ተቀብለናል!")

async def main():
    print("🚀 All Telegram Bots are starting up...")
    await user_bot.delete_webhook(drop_pending_updates=True)
    await admin_bot.delete_webhook(drop_pending_updates=True)
    await help_bot.delete_webhook(drop_pending_updates=True)
    
    await asyncio.gather(
        user_dp.start_polling(user_bot),
        admin_dp.start_polling(admin_bot),
        help_dp.start_polling(help_bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
