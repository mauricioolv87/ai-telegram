# main.py
import os
import asyncio
import logging
import functools
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from src.bot.handlers import audio_handler, start_handler
from src.config.settings import settings

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Variável global para o bot
bot_application: Application = None
polling_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    global bot_application, polling_task
    
    # Startup: Inicializar bot
    logger.info("🚀 Inicializando bot...")
    logger.info(f"📍 Modo: {settings.bot_mode}")
    
    bot_application = Application.builder().token(settings.telegram_bot_token).build()
    
    # Registrar handlers
    bot_application.add_handler(CommandHandler("start", start_handler))
    bot_application.add_handler(
        MessageHandler(filters.AUDIO | filters.VOICE, audio_handler)
    )
    
    # Inicializar bot
    await bot_application.initialize()
    await bot_application.start()
    
    # Escolher modo de operação
    if settings.bot_mode == 'polling':
        logger.info("🔄 Iniciando polling (desenvolvimento local)...")
        # Iniciar polling em background
        polling_task = asyncio.create_task(bot_application.updater.start_polling())
        logger.info("✅ Polling iniciado com sucesso!")
    elif settings.bot_mode == 'webhook':
        logger.info(f"🔗 Webhook habilitado para produção. URL: {settings.webhook_url}")
        logger.info("✅ Bot preparado para receber webhooks!")
    else:
        logger.warning(f"⚠️ Modo desconhecido: {settings.bot_mode}")
    
    logger.info("✅ Bot inicializado com sucesso!")
    
    yield  # Aplicação rodando
    
    # Shutdown: Limpar recursos
    logger.info("🛑 Finalizando bot...")
    
    if settings.bot_mode == 'polling' and polling_task:
        logger.info("🔴 Parando polling...")
        await bot_application.updater.stop()
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
    
    await bot_application.stop()
    await bot_application.shutdown()

# Criar aplicação FastAPI
app = FastAPI(
    title="AI Telegram Bot",
    description="Bot inteligente para registro de gastos no Organizze",
    version="1.0.0",
    lifespan=lifespan
)


def _require_webhook_mode(detail: str = "Este endpoint só está disponível em modo webhook"):
    """Decorator que bloqueia acesso ao endpoint se não estiver em modo webhook"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if settings.bot_mode != 'webhook':
                raise HTTPException(
                    status_code=400,
                    detail=detail
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "status": "running",
        "bot": "AI Telegram Bot",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check para Cloud Run"""
    return {"status": "healthy"}

@app.post("/webhook")
@_require_webhook_mode("Para webhook, acesse /webhook em modo webhook")
async def telegram_webhook(request: Request):
    """
    Endpoint que recebe updates do Telegram
    
    Este endpoint é chamado pelo Telegram sempre que há uma nova mensagem
    """
    try:
        # Obter dados do webhook
        data = await request.json()
        
        # Criar objeto Update do Telegram
        update = Update.de_json(data, bot_application.bot)
        
        # Processar update de forma assíncrona
        await bot_application.process_update(update)
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/set-webhook")
@_require_webhook_mode("Configure webhook apenas em modo webhook")
async def configure_webhook():
    """
    Configura o webhook no Telegram
    
    Deve ser chamado uma vez após o deploy para registrar a URL do webhook
    """
    webhook_url = settings.webhook_url
    
    if not webhook_url:
        raise HTTPException(
            status_code=400,
            detail="WEBHOOK_URL não configurada nas variáveis de ambiente"
        )
    
    try:
        # Usar URL conforme fornecida (sem adicionar /webhook novamente)
        full_webhook_url = webhook_url.rstrip('/')
        
        # Configurar webhook no Telegram
        await bot_application.bot.set_webhook(
            url=full_webhook_url,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True  # Limpar updates pendentes
        )
        
        # Verificar configuração
        webhook_info = await bot_application.bot.get_webhook_info()
        
        logger.info(f"✅ Webhook configurado: {webhook_info.url}")
        
        return {
            "status": "success",
            "webhook_url": webhook_info.url,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date,
            "last_error_message": webhook_info.last_error_message
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao configurar webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/webhook-info")
@_require_webhook_mode("Webhook info só disponível em modo webhook")
async def webhook_info():
    """Retorna informações sobre o webhook atual"""
    try:
        info = await bot_application.bot.get_webhook_info()
        
        return {
            "url": info.url,
            "has_custom_certificate": info.has_custom_certificate,
            "pending_update_count": info.pending_update_count,
            "last_error_date": info.last_error_date,
            "last_error_message": info.last_error_message,
            "max_connections": info.max_connections,
            "allowed_updates": info.allowed_updates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/webhook")
@_require_webhook_mode("Delete webhook só disponível em modo webhook")
async def delete_webhook():
    """Remove o webhook do Telegram"""
    try:
        await bot_application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook removido")
        
        return {"status": "webhook deleted"}
        
    except Exception as e:
        logger.error(f"❌ Erro ao remover webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Ponto de entrada
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8080))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )