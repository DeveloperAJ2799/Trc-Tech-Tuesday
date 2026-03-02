import os
import json
from groq import Groq
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from tools import search_tech_news, extract_article_content
from models import NewsReport, CriticFeedback

load_dotenv()

class TechNewsAgent:
    def __init__(self, model="openai/gpt-oss-120b"):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = model

    def get_hot_news(self, query="latest hot tech news", max_results: int = 5) -> NewsReport:
        print(f"Searching for: {query} (max_results={max_results})...")
        raw_results = search_tech_news(query, max_results=max_results)
        
        if not raw_results:
            print("No news results found from DuckDuckGo.")
            return NewsReport(articles=[], trending_topics=[])

        print(f"Extracting content from {len(raw_results)} articles in parallel...")
        
        def process_article(res):
            content = extract_article_content(res['url'])
            snippet = content[:1500] if content else res.get('body', '')
            return {
                "title": res['title'],
                "url": res['url'],
                "image_url": res.get('image', ''),
                "source": res.get('source', 'Unknown'),
                "snippet": snippet
            }

        with ThreadPoolExecutor(max_workers=5) as executor:
            processed_articles = list(executor.map(process_article, raw_results))

        print("Analyzing news with Groq AI...")
        prompt = f"""
        You are an expert tech news curator. Analyze the following news snippets and:
        1. Filter for the most impactful and "hot" tech news (AI, breakthrough hardware, major industry shifts).
        2. Score them on relevance (0-1).
        3. Provide a concise summary for each.
        4. Identify overall trending topics.

        Data:
        {json.dumps(processed_articles, indent=2)}

        Return ONLY a JSON object with this exact structure:
        {{
            "articles": [
                {{"title": "...", "url": "...", "image_url": "...", "summary": "...", "source": "...", "published_date": "...", "relevance_score": 0.9}}
            ],
            "trending_topics": ["...", "..."]
        }}
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a tech news aggregator agent that outputs raw JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        report_json = response.choices[0].message.content
        return NewsReport.model_validate_json(report_json)


class CriticAgent:
    def __init__(self, model="openai/gpt-oss-120b"):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = model

    def critique_article(self, article_title: str, article_summary: str) -> CriticFeedback:
        print(f"Critiquing: '{article_title}'...")
        prompt = f"""
        You are a harsh but fair social media editor. Review the following tech news headline and summary for an Instagram Story.
        It needs to be punchy, engaging, and clear.
        
        Original Title: {article_title}
        Original Summary: {article_summary}

        If it's already great, approve it. If not, provide an improved title and summary.
        
        Return ONLY a JSON object with this exact structure:
        {{
            "approved": true/false,
            "feedback": "...",
            "improved_title": "...",
            "improved_summary": "..."
        }}
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a social media editor that outputs raw JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        critic_json = response.choices[0].message.content
        return CriticFeedback.model_validate_json(critic_json)
