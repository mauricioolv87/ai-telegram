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
    """Nó de transcrição: apenas popula `transcription` no estado."""
    try:
        transcription = transcription_service.transcribe(state['audio_path'])
        state['transcription'] = transcription
        return state
    except Exception as e:
        state['error'] = f"Erro na transcrição: {str(e)}"
        return state


def extract_node(state: ExpenseState) -> ExpenseState:
    """Nó de extração: popula `expense_data` e `extracted_message` (não adiciona a `messages`)."""
    try:
        expense = extraction_service.extract(state['transcription'])
        state['expense_data'] = expense

        amount = abs(expense.amount_cents) / 100

        # Monta mensagem com informações (guardada separadamente)
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

        state['extracted_message'] = "\n".join(msg_parts)
        return state
    except Exception as e:
        state['error'] = f"Erro na extração: {str(e)}"
        return state


def send_node(state: ExpenseState) -> ExpenseState:
    """Nó de envio ao Organizze: realiza a chamada e guarda resposta (não adiciona mensagem)."""
    try:
        result = organizze_client.create_transaction(state['expense_data'])
        state['organizze_response'] = result
        state['sent_message'] = "✅ Gasto registrado no Organizze!"
        return state
    except Exception as e:
        state['error'] = f"Erro ao registrar: {str(e)}"
        return state


def finalize_messages_node(state: ExpenseState) -> ExpenseState:
    """Compõe as mensagens finais e sobrescreve `state['messages']` com um único item.

    Formato desejado:

    ✅ Transcrição: ...

    ✅ Dados extraídos:
    💰 R$ 50.00
    📝 descrição
    📅 data
    📂 Categoria: ...
    💳 Cartão: ...

    ✅ Gasto registrado no Organizze!
    """

    sections = []

    # Transcription section
    transcription = state.get('transcription')
    if transcription:
        sections.append(f"✅ Transcrição: {transcription}")

    # Extracted data section (extract_node should prepare 'extracted_message').
    # If missing, try to build from `expense_data` as fallback.
    extracted = state.get('extracted_message')
    if not extracted and state.get('expense_data'):
        exp = state['expense_data']
        try:
            amount = abs(exp.amount_cents) / 100
            parts = [
                "✅ Dados extraídos:",
                f"💰 R$ {amount:.2f}",
                f"📝 {exp.description}",
                f"📅 {exp.date}"
            ]
            if getattr(exp, 'category_id', None):
                # try to resolve category name if available in state (organizze client calls are expensive)
                try:
                    categories = organizze_client.get_categories()
                    category = next((c for c in categories if c.id == exp.category_id), None)
                    if category:
                        parts.append(f"📂 Categoria: {category.name}")
                except Exception:
                    pass

            if getattr(exp, 'credit_card_id', None):
                try:
                    cards = organizze_client.get_credit_cards()
                    card = next((c for c in cards if c.id == exp.credit_card_id), None)
                    if card:
                        parts.append(f"💳 Cartão: {card.name}")
                except Exception:
                    pass
            elif getattr(exp, 'account_id', None):
                try:
                    accounts = organizze_client.get_accounts()
                    account = next((a for a in accounts if a.id == exp.account_id), None)
                    if account:
                        parts.append(f"🏦 Conta: {account.name}")
                except Exception:
                    pass

            extracted = "\n".join(parts)
        except Exception:
            extracted = None

    if extracted:
        sections.append(extracted)

    # Sent/confirmation section (fallback to generic message if organizze_response exists)
    sent = state.get('sent_message')
    if not sent and state.get('organizze_response'):
        sent = "✅ Gasto registrado no Organizze!"

    if sent:
        sections.append(sent)

    # Compose final message with a blank line between sections
    final_text = "\n\n".join(sections) if sections else ""

    state['messages'] = [final_text] if final_text else []
    return state


def check_error(state: ExpenseState) -> str:
    """Verifica se houve erro"""
    return "error" if state.get('error') else "continue"