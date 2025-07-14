from fastapi import FastAPI
from module.response.main_response import run_response_pipeline

app = FastAPI()

@app.post("/chat")
def chat_endpoint(user_input: str):
    response, emotion_data = run_response_pipeline(user_input)
    return {"response": response, "emotion_data": emotion_data}
