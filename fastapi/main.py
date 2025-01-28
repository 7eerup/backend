import os
from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRouter
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

if not HUGGINGFACE_API_KEY:
    raise ValueError("Hugging Face API Key is missing. Please set it in the .env file.")

app = FastAPI()

# Hugging Face Inference URL
HUGGINGFACE_URL = "https://api-inference.huggingface.co/models"

# HTTP headers for Hugging Face API
HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

# Models for different tasks
SUPPORTED_MODELS = {
    "text_generation": "gpt2",  # Text generation model
    "sentiment_analysis": "distilbert-base-uncased-finetuned-sst-2-english",  # Sentiment analysis model
    "translation": "Helsinki-NLP/opus-mt-en-fr",  # English-to-French translation model
}

# Pydantic model for request body
class TextRequest(BaseModel):
    text: str

class TranslationRequest(BaseModel):
    text: str
    target_language: str  # For future support of multiple translations

# Helper function to call Hugging Face API
def query_huggingface_api(model_name: str, payload: dict):
    url = f"{HUGGINGFACE_URL}/{model_name}"
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))


# Routers for different tasks
router = APIRouter()

@router.post("/generate-text")
async def generate_text(request: TextRequest):
    """
    Generate text using the GPT-2 model.
    """
    model_name = SUPPORTED_MODELS["text_generation"]
    payload = {"inputs": request.text}
    result = query_huggingface_api(model_name, payload)

    if isinstance(result, list) and "generated_text" in result[0]:
        return {"generated_text": result[0]["generated_text"]}
    else:
        raise HTTPException(status_code=500, detail="Unexpected response from Hugging Face API.")

@router.post("/analyze-sentiment")
async def analyze_sentiment(request: TextRequest):
    """
    Perform sentiment analysis on the input text.
    """
    model_name = SUPPORTED_MODELS["sentiment_analysis"]
    payload = {"inputs": request.text}
    result = query_huggingface_api(model_name, payload)

    if isinstance(result, list):
        return {"sentiment": result[0].get("label"), "score": result[0].get("score")}
    else:
        raise HTTPException(status_code=500, detail="Unexpected response from Hugging Face API.")

@router.post("/translate")
async def translate_text(request: TranslationRequest):
    """
    Translate text to a target language (e.g., English to French).
    """
    model_name = SUPPORTED_MODELS["translation"]
    payload = {"inputs": request.text}
    result = query_huggingface_api(model_name, payload)

    if isinstance(result, list):
        return {"translated_text": result[0].get("translation_text")}
    else:
        raise HTTPException(status_code=500, detail="Unexpected response from Hugging Face API.")


@app.get("/")
async def root():
    return {
        "message": "Hello FastAPI Hugging Face",
        # "endpoints": [
        #     "/generate-text",
        #     "/analyze-sentiment",
        #     "/translate",
        # ],
    }


@app.post("/generate")
async def generate_text(request: TextRequest):
    """
    Generates text using a Hugging Face model.
    """
    url = "https://api-inference.huggingface.co/models/gpt2"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": request.text}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

    result = response.json()

    # Extract generated text or handle errors
    if isinstance(result, list) and "generated_text" in result[0]:
        return {"generated_text": result[0]["generated_text"]}
    else:
        raise HTTPException(status_code=500, detail="Unexpected response from Hugging Face API.")



app.include_router(router)