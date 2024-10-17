from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from ai_assistent import ai_assistant, start_button, ai_assistant_respond, clear_history, contact_handler, \
    contact_handler
from bmi_calculator import ask_weight, handle_bmi_input
from gfr_calculator import ask_gfr, handle_gfr_input
from instructions import instructions
from ml import ecg, mri, xray
from open_api import request_image, handle_image_description
from utils import init_pool

TELEGRAM_BOT_TOKEN = "7878572582:AAGAfT5xKcGlT_7k22c_UM7z_yiVfTTLynA"
WAITING_FOR_IMAGE = range(1)

def main():
    init_pool()
    print(f"{datetime.now()} - Started")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_button))
    application.add_handler(CommandHandler("clear", clear_history))
    application.add_handler(
        MessageHandler(filters.TEXT & filters.Regex("^(Виртуальный ассистент 🤖)$"), ai_assistant_respond))
    application.add_handler(
        MessageHandler(filters.TEXT & filters.Regex("^(Как пользоваться ботом 📖)$"), instructions))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(Калькулятор ИМТ 🏋️)$"), ask_weight))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(Калькулятор СКФ 🦠)$"), ask_gfr))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(Анализ ЭКГ)$"), ecg))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(Анализ МРТ)$"), mri))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(Анализ рентгена легких)$"), xray))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(Анализ фото)$"), request_image))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image_description))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gfr_input))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bmi_input))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_assistant))
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
