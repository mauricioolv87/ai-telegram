"""Handlers do Telegram"""
import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from ..graph.workflow import create_expense_workflow
from ..graph.state import ExpenseState
from .messages import WELCOME_MESSAGE, PROCESSING_MESSAGE, format_success, format_error

logger = logging.getLogger(__name__)
expense_workflow = create_expense_workflow()

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /start"""
    await update.message.reply_text(WELCOME_MESSAGE)

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de mensagens de voz"""
    await _process_audio(update, update.message.voice, "voice")

async def audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler de arquivos de áudio"""
    await _process_audio(update, update.message.audio, "audio")

async def _process_audio(update: Update, audio_file, file_type: str):
    """Processa áudio e envia para o workflow"""
    try:
        # responder processamento
        if update.message:
            await update.message.reply_text(PROCESSING_MESSAGE)

        # Se audio_file vier None, tentar encontrar em outros campos
        message = update.message
        if audio_file is None and message is not None:
            # prioridade: voice, audio, document (se for audio)
            if getattr(message, 'voice', None):
                audio_file = message.voice
                file_type = 'voice'
            elif getattr(message, 'audio', None):
                audio_file = message.audio
                file_type = 'audio'
            elif getattr(message, 'document', None):
                doc = message.document
                mime = getattr(doc, 'mime_type', '') or ''
                if mime.startswith('audio'):
                    audio_file = doc
                    file_type = 'audio'

        if audio_file is None:
            # não há áudio no update
            msg = 'Nenhum arquivo de áudio encontrado na mensagem.'
            logger.error(msg)
            if update.message:
                await update.message.reply_text(format_error(msg))
            return

        # Download do arquivo
        file = await audio_file.get_file()
        ext = "ogg" if file_type == "voice" else "mp3"
        audio_path = f"data/audios/{file_type}_{update.message.message_id}.{ext}"

        os.makedirs("data/audios", exist_ok=True)
        await file.download_to_drive(audio_path)
        
        # Processa
        initial_state = ExpenseState(
            audio_path=audio_path,
            transcription="",
            expense_data=None,
            organizze_response=None,
            error=None,
            messages=[]
        )
        
        result = expense_workflow.invoke(initial_state)
        
        # Cleanup
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        # Responde
        if result.get('error'):
            await update.message.reply_text(format_error(result['error']))
        else:
            await update.message.reply_text(format_success(result['messages']))
    
    except Exception as e:
        logger.error(f"Erro ao processar áudio: {e}")
        if update.message:
            await update.message.reply_text(format_error(f"Erro: {str(e)}"))