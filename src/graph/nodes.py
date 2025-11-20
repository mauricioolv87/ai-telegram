"""Nós do grafo LangGraph"""
import logging
from .state import ExpenseState
from ..services.transcription import TranscriptionService
from ..services.extraction import ExtractionService
from ..services.organizze import OrganizzeClient

logger = logging.getLogger(__name__)

transcription_service = TranscriptionService()
extraction_service = ExtractionService()
organizze_client = OrganizzeClient()

def transcribe_node(state: ExpenseState) -> ExpenseState:
    """Nó de transcrição"""
    try:
        transcription = transcription_service.transcribe(state['audio_path'])
        state['transcription'] = transcription
        state['messages'].append(f"✅ Transcrição: {transcription}")
        return state
    except Exception as e:
        state['error'] = f"Erro na transcrição: {str(e)}"
        return state

def extract_node(state: ExpenseState) -> ExpenseState:
    """Nó de extração"""
    try:
        expense = extraction_service.extract(state['transcription'])
        state['expense_data'] = expense
        
        amount = abs(expense.amount_cents) / 100
        
        # Monta mensagem com informações
        msg_parts = [
            "✅ Dados extraídos:",
            f"💰 R$ {amount:.2f}",
            f"📝 {expense.description}",
            f"📅 {expense.date}"
        ]
        
        # Adiciona categoria se identificada
        if expense.category_id:
            categories = organizze_client.get_categories()
            category = next((c for c in categories if c.id == expense.category_id), None)
            if category:
                msg_parts.append(f"📂 Categoria: {category.name}")
        
        # Adiciona forma de pagamento
        if expense.credit_card_id:
            cards = organizze_client.get_credit_cards()
            card = next((c for c in cards if c.id == expense.credit_card_id), None)
            if card:
                msg_parts.append(f"💳 Cartão: {card.name}")
        elif expense.account_id:
            accounts = organizze_client.get_accounts()
            account = next((a for a in accounts if a.id == expense.account_id), None)
            if account:
                msg_parts.append(f"🏦 Conta: {account.name}")
        
        state['messages'].append("\n".join(msg_parts))
        return state
    except Exception as e:
        state['error'] = f"Erro na extração: {str(e)}"
        return state

def send_node(state: ExpenseState) -> ExpenseState:
    """Nó de envio ao Organizze"""
    try:
        result = organizze_client.create_transaction(state['expense_data'])
        state['organizze_response'] = result
        state['messages'].append("✅ Gasto registrado no Organizze!")
        return state
    except Exception as e:
        state['error'] = f"Erro ao registrar: {str(e)}"
        return state

def check_error(state: ExpenseState) -> str:
    """Verifica se houve erro"""
    return "error" if state.get('error') else "continue"