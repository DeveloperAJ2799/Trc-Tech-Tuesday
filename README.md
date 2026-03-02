# Tech News Agentic AI

A Python-based agent that searches for the latest "hot" tech news, extracts content from articles, and uses an LLM (GPT-4o) to summarize and rank them.

## Features
- **Real-time News Search**: Uses DuckDuckGo News to find the freshest tech updates.
- **Smart Extraction**: Uses `trafilatura` to pull clean text content from web pages.
- **AI Analysis**: Uses OpenAI's structured outputs to categorize, score, and summarize news.
- **Persistent Tracking**: Saves fetched articles in `articles.json` and resumes items where image generation was not completed.
- **Modular Design**: Easy to extend with new tools or different LLM providers.

## Setup

1. **Clone/Copy the files** into your project directory.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   - Rename `.env.example` to `.env`.
   - Add your `OPENAI_API_KEY`.

## Usage

Run the main script:
```bash
python main.py
```

## Project Structure
- `main.py`: CLI entry point.
- `agent.py`: Orchestration logic for the AI agent.
- `tools.py`: Search and extraction utilities.
- `models.py`: Data schemas for structured output.
- `article_store.py`: JSON persistence and status tracking for fetched/generated articles.
