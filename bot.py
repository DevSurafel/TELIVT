import os
import logging
import random
from typing import Dict
import asyncio
from flask import Flask
from telegram import Update, ChatMemberUpdated
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ChatMemberHandler, ContextTypes
)
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Initialize Flask app
app = Flask(__name__)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

class InviteTrackerBot:
    def __init__(self, token: str, supergroup_id: int):
        self.token = token
        self.supergroup_id = supergroup_id
        self.invite_counts: Dict[int, Dict[str, int]] = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.message.from_user
        if user.id not in self.invite_counts:
            self.invite_counts[user.id] = {
                'invite_count': 0,
                'first_name': user.first_name,
                'withdrawal_key': None
            }
        invite_count = self.invite_counts[user.id]['invite_count']

        buttons = [
            [InlineKeyboardButton("Check", callback_data=f"check_{user.id}"),
             InlineKeyboardButton("Key🔑", callback_data=f"key_{user.id}")]
        ]

        first_name = self.invite_counts[user.id]['first_name']
        balance = invite_count * 50
        remaining = max(200 - invite_count, 0)

        if invite_count >= 200:
            message = (
                f"Congratulations 👏👏🎉\n\n"
                f"📊 Milestone Achieved: @DIGITAL_BIRRI\n"
                f"-----------------------\n"
                f"👤 User: {first_name}\n"
                f"👥 Invites: Nama {invite_count} afeertaniittu! \n"
                f"💰 Balance: {balance} ETB\n"
                f"🚀 Baafachuuf: Baafachuu ni dandeessu! \n"
                f"-----------------------\n\n"
                f"Baafachuuf kan jedhu tuquun baafadhaa 👇"
            )
            buttons.append([InlineKeyboardButton("Withdrawal Request", url="https://t.me/Digital_Birr_Bot?start=ar6222905852")])
        else:
            message = (
                f"📊 Invite Progress: @DIGITAL_BIRRI\n"
                f"-----------------------\n"
                f"👤 User: {first_name}\n"
                f"👥 Invites: Nama {invite_count} afeertaniittu \n"
                f"💰 Balance: {balance} ETB\n"
                f"🚀 Baafachuuf: Dabalataan nama {remaining} afeeraa\n"
                f"-----------------------\n\n"
                f"Add gochuun carraa badhaasaa keessan dabalaa!"
            )

        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(buttons))

    async def track_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info(f"Chat member updated in chat {update.effective_chat.id}")
        logger.info(f"Update: {update}")

        # Check if the update is for the specified supergroup
        if update.effective_chat.id != self.supergroup_id:
            logger.info(f"Ignoring update from chat {update.effective_chat.id}")
            return

        if update.my_chat_member:
            chat_member_update = update.my_chat_member
        elif update.chat_member:
            chat_member_update = update.chat_member
        else:
            logger.error("Update does not contain member status change.")
            return

        new_member = chat_member_update.new_chat_member.user
        old_member = chat_member_update.old_chat_member.user
        inviter = chat_member_update.from_user
        chat_id = chat_member_update.chat.id

        logger.debug(f"Chat ID: {chat_id}, Inviter: {inviter.id}, New Member: {new_member.id}")

        # Check if the user has joined the chat
        if chat_member_update.new_chat_member.status == "member" and chat_member_update.old_chat_member.status != "member":
            if inviter.id == new_member.id:
                logger.debug("Inviter is the new member, skipping...")
                return
            if inviter.id not in self.invite_counts:
                logger.debug(f"Initializing invite count for user {inviter.id}")
                self.invite_counts[inviter.id] = {
                    'invite_count': 0,
                    'first_name': inviter.first_name,
                    'withdrawal_key': None
                }
            self.invite_counts[inviter.id]['invite_count'] += 1
            invite_count = self.invite_counts[inviter.id]['invite_count']

            logger.info(f"User {inviter.id} invited member {new_member.id}. Total invites: {invite_count}")

            if invite_count % 10 == 0:
                first_name = self.invite_counts[inviter.id]['first_name']
                balance = invite_count * 50
                remaining = max(200 - invite_count, 0)

                if invite_count >= 200:
                    message = (
                        f"Congratulations 👏👏🎉\n\n"
                        f"📊 Milestone Achieved: @DIGITAL_BIRRI\n"
                        f"-----------------------\n"
                        f"👤 User: {first_name}\n"
                        f"👥 Invites: Nama {invite_count} afeertaniittu\n"
                        f"💰 Balance: {balance} ETB\n"
                        f"🚀 Baafachuuf: Baafachuu ni dandeessu! \n"
                        f"-----------------------\n\n"
                        f"Baafachuuf kan jedhu tuquun baafadhaa 👇"
                    )
                    buttons = [
                        [InlineKeyboardButton("Baafachuuf", url="https://t.me/Digital_Birr_Bot?start=ar6222905852")]
                    ]
                else:
                    message = (
                        f"📊 Invite Progress: @DIGITAL_BIRRI\n"
                        f"-----------------------\n"
                        f"👤 User: {first_name}\n"
                        f"👥 Invites: Nama {invite_count} afeertaniittu \n"
                        f"💰 Balance: {balance} ETB\n"
                        f"🚀 Baafachuuf: Dabalataan nama {remaining} afeeraa\n"
                        f"-----------------------\n\n"
                        f"Add gochuun carraa badhaasaa keessan dabalaa!"
                    )
                    buttons = [
                        [InlineKeyboardButton("Check", callback_data=f"check_{inviter.id}")]
                    ]

                await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=InlineKeyboardMarkup(buttons))

    async def handle_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user_id = int(query.data.split('_')[1])

        if user_id not in self.invite_counts:
            await query.answer("No invitation data found.")
            return

        user_data = self.invite_counts[user_id]
        invite_count = user_data['invite_count']
        first_name = user_data['first_name']
        balance = invite_count * 50
        remaining = max(200 - invite_count, 0)

        message = (
            f"📊 Invite Progress: @DIGITAL_BIRRI\n"
            f"-----------------------\n"
            f"👤 User: {first_name}\n"
            f"👥 Invites: Nama {invite_count} afeertaniittu \n"
            f"💰 Balance: {balance} ETB\n"
            f"🚀 Baafachuuf: Dabalataan nama {remaining} afeeraa\n"
            f"-----------------------\n\n"
            f"Add gochuun carraa badhaasaa keessan dabalaa!"
        )

        await query.answer(f"Kabajamoo {first_name}, maallaqa baafachuuf dabalataan nama {remaining} afeeruu qabdu", show_alert=True)

    async def handle_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user_id = int(query.data.split('_')[1])

        if user_id not in self.invite_counts:
            await query.answer("No invitation data found.")
            return

        user_data = self.invite_counts[user_id]
        invite_count = user_data['invite_count']
        first_name = user_data['first_name']

        if invite_count >= 200:
            if not user_data['withdrawal_key']:
                user_data['withdrawal_key'] = random.randint(100000, 999999)
            withdrawal_key = user_data['withdrawal_key']
            await query.answer(f"Kabajamoo {first_name}, Lakkoofsi Key🔑 keessanii: 👉{withdrawal_key}", show_alert=True)
        else:
            await query.answer(f"Kabajamoo {first_name}, lakkoofsa Key argachuuf yoo xiqqaate nama 200 afeeruu qabdu!", show_alert=True)

    def run(self):
        try:
            application = Application.builder().token(self.token).build()

            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(ChatMemberHandler(self.track_new_member, ChatMemberUpdated))
            application.add_handler(CallbackQueryHandler(self.handle_check, pattern=r'^check_\d+$'))
            application.add_handler(CallbackQueryHandler(self.handle_key, pattern=r'^key_\d+$'))

            logger.info("Bot started successfully!")

            # Ensure the bot receives all relevant update types
            allowed_updates = ["message", "edited_channel_post", "callback_query", "chat_member", "my_chat_member"]

            # Run the bot asynchronously
            asyncio.run(application.run_polling(drop_pending_updates=True, allowed_updates=allowed_updates))

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")

# Web server to keep the service running on Render
@app.route('/')
def index():
    return "Bot is running!"

def main():
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    SUPERGROUP_ID = int(os.getenv('SUPERGROUP_ID'))
    if not TOKEN:
        logger.error("No bot token provided. Set TELEGRAM_BOT_TOKEN environment variable.")
        return
    if not SUPERGROUP_ID:
        logger.error("No supergroup ID provided. Set SUPERGROUP_ID environment variable.")
        return

    bot = InviteTrackerBot(TOKEN, SUPERGROUP_ID)

    # Run the bot and the Flask app in the same event loop
    loop = asyncio.get_event_loop()
    loop.create_task(bot.run())  # Start the bot as a background task

    # Start the Flask app (it will run in the main thread)
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))

if __name__ == "__main__":
    main()
