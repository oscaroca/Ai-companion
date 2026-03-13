import sys
import os
from pathlib import Path

# Add workspace root to Python path
workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes,MessageHandler, filters

from llmImplementation.conversation_manager import ConversationManager
from llmImplementation.kobold.koboldConversation import KoboldConversation




# ---------- AI Setup ----------
from prompts import prompt_temp

kobold = KoboldConversation(system_prompt=prompt_temp)
manager = ConversationManager(kobold)





# ---------- Telegram Bot Setup ----------
# settings.py
from dotenv import load_dotenv

dotenv_path = workspace_root / '.env'
load_dotenv(str(dotenv_path))


TELEGRAM_KEY = os.environ.get("TELEGRAM_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey! I'm alive 🤖")

async def handle_message(update, context):
    text = update.message.text
    response = manager.send(text)
    await update.message.reply_text(response)


app = ApplicationBuilder().token(TELEGRAM_KEY).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))





print("Starting bot...")
app.run_polling()
print("Bot started...")