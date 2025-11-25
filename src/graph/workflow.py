"""Definição do workflow LangGraph"""
from langgraph.graph import StateGraph, END
from .state import ExpenseState
from .nodes import transcribe_node, extract_node, send_node, check_error, finalize_messages_node

def create_expense_workflow():
    """Cria o workflow de processamento de despesas"""
    workflow = StateGraph(ExpenseState)
    
    # Adiciona nós
    workflow.add_node("transcribe", transcribe_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("send", send_node)
    workflow.add_node("finalize", finalize_messages_node)
    
    # Define fluxo
    workflow.set_entry_point("transcribe")
    
    workflow.add_conditional_edges(
        "transcribe",
        check_error,
        {"continue": "extract", "error": END}
    )
    
    workflow.add_conditional_edges(
        "extract",
        check_error,
        {"continue": "send", "error": END}
    )
    
    workflow.add_conditional_edges(
        "send",
        check_error,
        {"continue": "finalize", "error": END}
    )

    workflow.add_edge("finalize", END)
    
    return workflow.compile()