# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import evaluation
import os

# Import config to verify API key is set
from app.config import OPENROUTER_API_KEY

app = FastAPI(title="AI Evaluation Service", version="1.0.0")

# CORS for Node.js backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evaluation.router)

@app.get("/")
async def root():
    return {"message": "AI Evaluation Service Running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))