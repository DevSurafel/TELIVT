import os
import logging
import random
from typing import Dict
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='invite_tracker.log'
)
logger = logging.getLogger(__name__)

# Data storage for user progress and withdrawal codes
invite_counts: Dict[int, int] = {}
withdrawal_codes: Dict[int, str] = {}

class InviteTrackerBot:
    def __init__(self, token: str):
        self.token = token
        self.invite_counts = {}
        self.withdrawal_codes = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for the /start command"""
        keyboard = [[InlineKeyboardButton("Check", callback_data=f"check_{update.effective_user.id}")]]
        await update.message.reply_text(
            "Welcome! I'm an invite tracking bot. I'll keep track of how many users each person invites to the group.\n\n"
            "Click 'Check' to view your progress!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def track_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Track new members and their inviters"""
        for new_member in update.message.new_chat_members:
            try:
                inviter = update.message.from_user

                # Ignore bot invites or self-joins
                if inviter.id == new_member.id:
                    continue

                # Update invite count
                if inviter.id not in self.invite_counts:
                    self.invite_counts[inviter.id] = 0
                self.invite_counts[inviter.id] += 1

                invite_count = self.invite_counts[inviter.id]

                # Assign withdrawal code if milestone is achieved
                if invite_count >= 6 and inviter.id not in self.withdrawal_codes:
                    self.withdrawal_codes[inviter.id] = f"{random.randint(100000, 999999)}"

                # Send milestone message
                if invite_count % 4 == 0:
                    keyboard = [[InlineKeyboardButton("Check", callback_data=f"check_{inviter.id}")]]
                    await update.message.reply_text(
                        f"🎉 Milestone Achieved! 🎉👏\n\n"
                        f"📋 Dashboard:\n"
                        f"-----------------------\n"
                        f"👤 Name: {inviter.first_name}\n"
                        f"👥 Invites: {invite_count} people\n"
                        f"💰 Balance: {invite_count * 50} ETB\n"
                        f"🚀 Next Goal: Invite 4 more\n"
                        f"-----------------------\n\n"
                        f"Keep inviting to earn more rewards!",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )

            except Exception as e:
                logger.error(f"Error tracking invite: {e}")

    async def handle_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the 'Check' button callback"""
        query = update.callback_query
        user_id = int(query.data.split('_')[1])
        invite_count = self.invite_counts.get(user_id, 0)
        balance = invite_count * 50
        next_milestone = invite_count + (4 - (invite_count % 4))
        remaining = max(next_milestone - invite_count, 0)

        if invite_count >= 6:  # Milestone achieved
            code = self.withdrawal_codes.get(user_id, "Unavailable")
            message = (
                f"🎉 Milestone Achieved! 🎉👏\n\n"
                f"📋 Dashboard:\n"
                f"-----------------------\n"
                f"👤 Name: {query.from_user.first_name}\n"
                f"👥 Invites: {invite_count} people\n"
                f"💰 Balance: {balance} ETB\n"
                f"🔑 Withdrawal Code: {code}\n"
                f"🚀 Next Goal: Invite {remaining} more\n"
                f"-----------------------\n\n"
                f"Keep inviting to earn more rewards!"
            )
        else:  # Normal progress
            message = (
                f"📊 Your Progress:\n"
                f"-----------------------\n"
                f"👤 Name: {query.from_user.first_name}\n"
                f"👥 Invites: {invite_count} people\n"
                f"💰 Balance: {balance} ETB\n"
                f"🚀 Remaining for withdrawal: {remaining} more people\n"
                f"-----------------------\n\n"
                f"Keep inviting to earn more rewards!"
            )

        keyboard = [[InlineKeyboardButton("Back", callback_data=f"back_{user_id}")]]
        await query.answer()
        await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the 'Back' button callback"""
        query = update.callback_query
        user_id = int(query.data.split('_')[1])

        keyboard = [[InlineKeyboardButton("Check", callback_data=f"check_{user_id}")]]
        await query.answer()
        await query.edit_message_text(
            f"🎉 Milestone Achieved! 🎉👏\n\n"
            f"📋 Dashboard:\n"
            f"-----------------------\n"
            f"👤 Name: {query.from_user.first_name}\n"
            f"👥 Invites: {self.invite_counts.get(user_id, 0)} people\n"
            f"💰 Balance: {self.invite_counts.get(user_id, 0) * 50} ETB\n"
            f"🚀 Next Goal: Invite 4 more\n"
            f"-----------------------\n\n"
            f"Keep inviting to earn more rewards!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    def run(self):
        """Run the bot"""
        try:
            application = Application.builder().token(self.token).build()

            # Register handlers
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(MessageHandler(
                filters.StatusUpdate.NEW_CHAT_MEMBERS,
                self.track_new_member
            ))
            application.add_handler(CallbackQueryHandler(self.handle_check, pattern=r'^check_\d+$'))
            application.add_handler(CallbackQueryHandler(self.handle_back, pattern=r'^back_\d+$'))

            # Start the bot
            logger.info("Bot started successfully!")
            application.run_polling(drop_pending_updates=True)

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")

def main():
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logger.error("No bot token provided. Set TELEGRAM_BOT_TOKEN environment variable.")
        return

    bot = InviteTrackerBot(TOKEN)
    bot.run()

if __name__ == "__main__":
    main()
