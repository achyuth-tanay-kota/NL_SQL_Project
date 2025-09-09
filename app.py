import uvicorn
from fastapi import FastAPI
from langchain_core.messages import HumanMessage

import pydantic_models
from sql_agent import data_analyst_agent
import config

app = FastAPI()



@app.post('/invoke')
def invoke_agent(payload: pydantic_models.ApiPayload):
    agent = data_analyst_agent()
    initial_state = {'user_question':payload.user_input, 'messages':[HumanMessage(payload.user_input, name='user')]}
    final_state = agent.invoke(initial_state, config={'configurable':{'thread_id':payload.thread_id}, 'recursion_limit': 100})
    return final_state["messages"], final_state["final_answer"]


if __name__ == '__main__':
    uvicorn.run('app:app', host=config.API_HOST, port=config.API_PORT, reload=True)
