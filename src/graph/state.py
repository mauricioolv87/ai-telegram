"""Estado do grafo LangGraph"""
from typing import TypedDict, Annotated, Optional
import operator
from ..models.expense import ExpenseData

class ExpenseState(TypedDict):
    audio_path: str
    transcription: str
    expense_data: Optional[ExpenseData]
    organizze_response: Optional[dict]
    error: Optional[str]
    messages: Annotated[list, operator.add]