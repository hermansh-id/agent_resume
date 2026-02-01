from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from langfuse.langchain import CallbackHandler
from langchain_core.messages import ToolMessage
from agent_st.agent import supervisor_agent
import os
import uvicorn

app = FastAPI(title="Agent Resume API", description="API to interact with the Resume Search Agent")

langfuse_handler = CallbackHandler()

class ChatRequest(BaseModel):
    query: str
    history: Optional[str] = ""

class ChatResponse(BaseModel):
    response: str
    input_tokens: int
    output_tokens: int
    tool_messages: list[str]

@app.get("/")
async def root():
    return {"message": "Agent Resume API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        print(f"DEBUG: Processing query: {request.query}")
        print(f"DEBUG: QDRANT_URL: {os.getenv('QDRANT_URL')}")
        print(f"DEBUG: LANGFUSE_BASE_URL: {os.getenv('LANGFUSE_BASE_URL')}")
        
        result = supervisor_agent.invoke({
            "messages": [{"role": "user", "content": request.query + " history chat: " + (request.history or "")}]
        }, config={"callbacks": [langfuse_handler]})
        
        print("DEBUG: Agent invocation successful")
        
        # supervisor_agent return the list of messages, we take the last message content
        response_text = result["messages"][-1].content
        
        # Extract metadata
        total_input_tokens = 0
        total_output_tokens = 0
        tool_messages = []

        for message in result["messages"]:
            # Token usage
            if hasattr(message, "response_metadata") and message.response_metadata:
                if "usage_metadata" in message.response_metadata:
                    total_input_tokens += message.response_metadata["usage_metadata"].get("input_tokens", 0)
                    total_output_tokens += message.response_metadata["usage_metadata"].get("output_tokens", 0)
                elif "token_usage" in message.response_metadata:
                    total_input_tokens += message.response_metadata["token_usage"].get("prompt_tokens", 0)
                    total_output_tokens += message.response_metadata["token_usage"].get("completion_tokens", 0)
            
            # Tool messages
            if isinstance(message, ToolMessage):
                tool_messages.append(message.content)

        return ChatResponse(
            response=response_text,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            tool_messages=tool_messages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))