"""
# Data analyst agent(lookup SQL tables and return the results as required for the given input from the supervisor)
# Contains the query-planner(schema checker + scope checker + terminology retriever tool), query generator, query safety checker, execute query, repeat if error, SQL-NL formatter
"""

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from typing import Literal
import re
import sqlite3
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver

import config
import utilities
import prompts
from agent_tools import get_canonical_line_items
import pydantic_models

load_dotenv()

sql_llm = ChatOpenAI(model=config.CHAT_OPENAI_MODEL_NAME)
tools = [get_canonical_line_items]
sql_llm_with_tools = sql_llm.bind_tools(tools)
checkpoint_conn = sqlite3.connect(config.checkpoint_db_path, check_same_thread=False)
checkpointer = SqliteSaver(checkpoint_conn)
AnalystState = pydantic_models.AnalystState

#Nodes definitions
def initial_reasoner(state:AnalystState):
    db_schema = open(config.DB_SCHEMA_PATH, 'r').read()
    initial_reasoner_prompt = SystemMessage(prompts.initial_reasoner_prompt.format_map({'user_input':state.user_question, 'schema':db_schema}))
    structured_llm = sql_llm.with_structured_output(pydantic_models.ReasonerOutput)
    response = structured_llm.invoke([initial_reasoner_prompt]+state.messages)
    # print('initial_reasoner type:',response.query_type, '\ninitial_reasoner response:',response.response, '\nmessages:',state.messages)
    if response.query_type.lower() == 'other':
        return {'messages':[AIMessage(response.response)], 'final_answer':response.response, 'query_type':response.query_type}
    else:
        return {'messages':[AIMessage(response.response)],'query_type':response.query_type}


def planner(state:AnalystState):
    db_schema = open(config.DB_SCHEMA_PATH, 'r').read()
    if state.user_question:
        format_map = {'user_question': state.user_question, 'db_schema': db_schema}
        planner_system_prompt = SystemMessage(prompts.sql_planner_system_prompt.format_map(format_map))
        response = sql_llm_with_tools.invoke([planner_system_prompt]+state.messages)
        # print('planner:', response.pretty_print())
        return {'messages': [response], 'plan': response.content}

    return {}

tool_node = ToolNode(tools)

def scope_checker(state:AnalystState):
    if re.search(r'\bOUT_OF_SCOPE\b', state.plan):
        return {'messages': [HumanMessage('OUT_OF_SCOPE', name='scope_checker')], 'final_answer': state.plan, 'scope_ok': False}
    elif re.search(r'\bINSUFFICIENT_DATA\b', state.plan):
        return {'messages': [HumanMessage('INSUFFICIENT_DATA',name='scope_checker')], 'final_answer': state.plan, 'scope_ok': False}
    else:
        return {'scope_ok':True}


def query_generator(state:AnalystState):
    db_schema = open(config.DB_SCHEMA_PATH, 'r').read()
    if state.plan:
        format_map = {'user_question': state.user_question, 'db_schema': db_schema, 'query_plan': state.plan}
        query_generator_prompt = SystemMessage(prompts.sql_generator_system_prompt.format_map(format_map))
        structured_sql_llm = sql_llm.with_structured_output(pydantic_models.GeneratorOutput)
        response = structured_sql_llm.invoke([query_generator_prompt])
        # print('query_generator:', response.sql_query)
        return {'messages': [HumanMessage(f'Here is the generated SQL query: {response.sql_query}', name='sql_query_generator')], 'sql_query': response.sql_query}

    return {}

def safety_checker(state:AnalystState):
    if state.sql_query:
        safety_flag = utilities.is_safe_sql(state.sql_query)
        if not safety_flag:
            return {'safety_ok': safety_flag, 'messages':[HumanMessage(f'the generated query contains one of the forbidden sql keywords {config.forbidden_sql_keywords}', name= 'SQL_query_safety_validator')]}
        else:
            return {'safety_ok':safety_flag}
    return {'messages':[HumanMessage('query not generated using the plan', name = 'SQL_query_safety_validator')]}


def query_executor(state:AnalystState):
    if state.safety_ok and state.sql_query:
        if not re.search(r"\bLIMIT\b", state.sql_query, re.IGNORECASE):
            # append LIMIT safely
            modified = state.sql_query.strip().strip(';')
            state.sql_query = f"{modified} LIMIT {config.SQL_ROW_LIMIT};"
        columns,rows, exception = utilities.execute_sql(state.sql_query)
        # print('query_executor:', 'Exception:', exception, 'rows:', rows, 'columns:', columns)
        if exception:
            return {'query_result_rows':rows,'query_result_columns':columns, 'exec_ok':False, 'messages':[HumanMessage(f'Generated query resulted in exception:{exception}', name = 'SQL_query_executor')]}
        else:
            return {'query_result_rows': rows, 'query_result_columns': columns, 'exec_ok': True}
    return {'messages':[HumanMessage('Either query is not safe to use or query not generated using the plan', name = 'SQL_query_executor')]}


def sql_to_nl_converter(state:AnalystState):
    format_map = {'question':state.user_question, 'plan': state.plan, 'sql':state.sql_query, 'column_names': state.query_result_columns, 'rows': state.query_result_rows}
    sql_to_nl_prompt = SystemMessage(prompts.sql_to_nl_prompt.format_map(format_map))
    response = sql_llm.invoke([sql_to_nl_prompt])
    return {'messages':[response], 'final_answer':response.content}


#routing nodes
def route_based_on_query_type(state:AnalystState)->Literal['planner', END]:
    if state.query_type.lower() == 'other':
        return END
    else:
        return 'planner'

def route_based_on_scope(state:AnalystState)-> Literal['sql_to_nl_converter','query_generator']:
    if not state.scope_ok:
        return 'sql_to_nl_converter'
    else:
        return 'query_generator'

def route_based_on_tools(state:AnalystState) -> Literal['tool_node', 'scope_checker']:
    if state.messages[-1].tool_calls:
        return 'tool_node'
    else:
        return 'scope_checker'

def route_based_on_safety(state:AnalystState) -> Literal['planner', 'query_executor']:
    if state.safety_ok:
        return 'query_executor'
    else:
        return 'planner'

def route_based_on_execution(state:AnalystState) -> Literal['planner', 'sql_to_nl_converter']:
    if state.exec_ok:
        return 'sql_to_nl_converter'
    else:
        return 'planner'

def data_analyst_agent():
    #Graph buildup

    analyst_workflow = StateGraph(AnalystState)
    #adding nodes
    analyst_workflow.add_node('initial_reasoner', initial_reasoner)
    analyst_workflow.add_node('planner', planner)
    analyst_workflow.add_node('tool_node', tool_node)
    analyst_workflow.add_node('scope_checker', scope_checker)
    analyst_workflow.add_node('query_generator', query_generator)
    analyst_workflow.add_node('safety_checker', safety_checker)
    analyst_workflow.add_node('query_executor', query_executor)
    analyst_workflow.add_node('sql_to_nl_converter', sql_to_nl_converter)


    #adding edges
    analyst_workflow.add_edge(START,'initial_reasoner')
    analyst_workflow.add_conditional_edges('initial_reasoner', route_based_on_query_type)
    analyst_workflow.add_conditional_edges('planner', route_based_on_tools)
    analyst_workflow.add_edge('tool_node', 'planner')
    analyst_workflow.add_conditional_edges('scope_checker', route_based_on_scope)
    analyst_workflow.add_edge('query_generator', 'safety_checker')
    analyst_workflow.add_conditional_edges('safety_checker', route_based_on_safety)
    analyst_workflow.add_conditional_edges('query_executor', route_based_on_execution)
    analyst_workflow.add_edge('sql_to_nl_converter', END)

    data_analyst = analyst_workflow.compile(checkpointer=checkpointer, debug=config.debug_mode)

    return data_analyst

if __name__ == '__main__':
    my_agent = data_analyst_agent()
    img_bytes = my_agent.get_graph().draw_mermaid_png()
    with open('workflow.png', 'wb') as f:
        f.write(img_bytes)

    # image_str = my_agent.get_graph().draw_ascii()
    # with open('workflow_ascii.txt', 'w') as f:
    #     f.write(image_str)