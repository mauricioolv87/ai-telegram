"""Templates de mensagens do bot"""

WELCOME_MESSAGE = """
👋 Olá! Eu sou o bot de gastos do Organizze.

🎤 Envie um áudio descrevendo seu gasto e eu vou:
1. Transcrever o áudio
2. Extrair as informações (valor, descrição, data)
3. Registrar no Organizze

Exemplo: 'Gastei 50 reais no supermercado hoje'
Ou: 'Paguei 120 reais de academia por boleto dia 15'
"""

PROCESSING_MESSAGE = "🎧 Processando seu áudio..."

def format_success(messages: list) -> str:
    return "\n\n".join(messages)

def format_error(error: str) -> str:
    return f"❌ {error}"