import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from web3 import Web3
from web3.middleware import geth_poa_middleware

BOT_TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
INFURA_URL = "https://bsc-dataseed.binance.org/"
CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181"
CHANNEL_USERNAME = "@benjaminfranklintoken"
SIGNUP_BONUS = 500
REFERRAL_BONUS = 100

w3 = Web3(Web3.HTTPProvider(INFURA_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

with open("abi.json", "r") as abi_file:
    abi = json.load(abi_file)

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)

users = {}
if os.path.exists("users.json"):
    with open("users.json", "r") as f:
        users = json.load(f)

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in users:
        await update.message.reply_text("You already received your bonus.")
        return

    joined = False
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id)
        joined = member.status in ['member', 'administrator', 'creator']
    except:
        pass

    if not joined:
        await update.message.reply_text(f"Please join our channel {CHANNEL_USERNAME} to receive your airdrop.")
        return

    ref = context.args[0] if context.args else None
    users[user_id] = {
        "wallet": None,
        "referred_by": ref if ref in users else None,
        "bonus": SIGNUP_BONUS
    }

    if ref and ref in users:
        users[ref]["bonus"] += REFERRAL_BONUS

    save_users()
    await update.message.reply_text(
        f"Welcome! You received {SIGNUP_BONUS} tokens as a signup bonus.\n"
        f"{'Your referrer received a bonus too!' if ref else ''}\n\n"
        f"Your referral link:\nhttps://t.me/Bjfairdrop_bot?start={user_id}"
    )

async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        await update.message.reply_text("Please start the bot with /start first.")
        return

    wallet = update.message.text.strip()
    if not Web3.is_address(wallet):
        await update.message.reply_text("Invalid wallet address.")
        return

    users[user_id]["wallet"] = wallet
    save_users()
    await update.message.reply_text("Wallet address saved.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet))
    app.run_polling()

if __name__ == "__main__":
    main()
