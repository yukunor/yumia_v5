# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running Commands

### Start the application
```bash
uvicorn main:app --reload
```

### Deploy to Render
```bash
# Build command (as specified in render.yaml)
pip install -r requirements.txt

# Start command for production
uvicorn main:app --host 0.0.0.0 --port 10000
```

### Run tests
```bash
pytest tests/
```

### Environment setup
```bash
pip install -r requirements.txt
```

### Load environment variables
```bash
# Ensure .env file exists with OPENAI_API_KEY
# The system uses python-dotenv to load environment variables
```

## Architecture Overview

This is a FastAPI-based emotional AI response system (Yumia) that analyzes user input for emotional content and generates contextually appropriate responses. The system is primarily written in Japanese and uses OpenAI's GPT-4o model.

### Core Components

**FastAPI Server (`main.py`)**
- Handles `/chat` endpoint for user interactions
- Processes user input through the emotion pipeline
- Serves static HTML frontend at root path
- Manages conversation history via `/history` endpoint

**Emotion Processing Pipeline (`module/response/main_response.py`)**
- Multi-step emotion analysis: estimation → indexing → keyword matching → response generation
- Categorizes emotions into short/intermediate/long term memory
- Uses reference emotion data to improve response quality

**Memory System (`module/memory/`)**
- **main_memory.py**: Central handler for emotion data processing
- **divide_emotion.py**: Categorizes emotions by intensity/duration (short/intermediate/long)
- **index_emotion.py**: Maintains searchable emotion indexes
- **oblivion_emotion.py**: Handles cleanup of old emotion data

**LLM Client (`llm_client.py`)**
- Manages OpenAI API interactions
- Handles emotion normalization and validation
- Processes structured emotion data extraction from responses
- Maintains allowed emotions list and emotion mapping
- **Key functions**: `generate_emotion_from_prompt_simple()` for initial emotion estimation, `generate_emotion_from_prompt_with_context()` for context-aware response generation

**Context Selection (`module/context/context_selector.py`)**
- Selects relevant conversation history for context
- Manages dialogue continuity

### Data Flow

1. User input → FastAPI endpoint (`/chat`)
2. Emotion estimation using GPT-4o (`llm_client.py`)
3. Index search for similar emotions (`response_index.py`)
4. Response generation with emotion context (`main_response.py`)
5. Memory storage and categorization (`memory/` modules)
6. Response sanitization and history logging

### Key Data Structures

- **Emotion Data**: JSON objects with `主感情` (main emotion), `構成比` (composition ratio), keywords, and metadata
- **Memory Categories**: `short/`, `intermediate/`, `long/` directories storing emotion data by duration
- **Index Files**: JSONL format emotion indexes for fast retrieval
- **Conversation History**: JSONL format dialogue records

### Configuration Files

- `system_prompt.txt`: System behavior prompts
- `emotion_prompt.txt`: Emotion analysis prompts  
- `dialogue_prompt.txt`: Response generation prompts
- `emotion_map.json`: Emotion normalization mapping
- `requirements.txt`: Python dependencies

### Testing

Tests are located in `tests/` directory and use pytest framework. Run tests with `pytest tests/`.

## Important Notes

- The system requires `OPENAI_API_KEY` environment variable
- Emotion data is stored in structured JSON format in `memory/` directories
- The system maintains conversation history in `dialogue_history.jsonl`
- Logging is configured to write to `app.log`
- Frontend is served from `static/index.html`