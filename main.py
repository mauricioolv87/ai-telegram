"""Ponto de entrada do bot"""
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from src.config.settings import settings
from src.bot.handlers import start_handler, voice_handler, audio_handler

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Inicia o bot"""
    # Carrega variáveis de ambiente
    load_dotenv()
    
    # Valida configurações
    settings.validate()
    
    # Cria aplicação
    application = Application.builder().token(settings.telegram_bot_token).build()
    
    # Adiciona handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(MessageHandler(filters.VOICE, voice_handler))
    application.add_handler(MessageHandler(filters.AUDIO, audio_handler))
    
    # Inicia
    logger.info("🤖 Bot iniciado!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()