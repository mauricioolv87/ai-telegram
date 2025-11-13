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
        state['messages'].append(
            f"✅ Dados extraídos:\n"
            f"💰 R$ {amount:.2f}\n"
            f"📝 {expense.description}\n"
            f"📅 {expense.date}"
        )
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