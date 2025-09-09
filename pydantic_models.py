from pydantic import BaseModel, Field
from typing import Annotated, List, Literal
from langchain_core.messages import AnyMessage
import operator


class ApiPayload(BaseModel):
    thread_id: str
    user_input: str


class AnalystState(BaseModel):
    messages: Annotated[List[AnyMessage], operator.add] = []
    user_question: str
    query_type: Literal['OTHER', 'COMPANY'] = 'COMPANY'
    plan:str = ''
    scope_ok: bool = False
    sql_query:str = ''
    safety_ok:bool = False
    exec_ok:bool = False
    query_result_columns:list = []
    query_result_rows:list = []
    final_answer:str = ''



#unused
class BotState(BaseModel):
    messages: Annotated[List[AnyMessage], operator.add]
    user_question: str
    advice: str = ''
    final_answer: str = ''


class ReasonerOutput(BaseModel):
    reasoning: Annotated[str, Field(description='your reasoning for giving the output based on the user query')]
    query_type:Annotated[Literal['OTHER', 'COMPANY'], Field(description='user query classification. should be one of ["OTHER", "COMPANY"]')]
    response:Annotated[str, Field(description='answer to the user question')]


class GeneratorOutput(BaseModel):
    sql_query: Annotated[str, Field(description='a single SQL SELECT query required to be executed to get the answer to the user question')]

