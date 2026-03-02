import argparse
import time
import schedule
from agent import TechNewsAgent, CriticAgent
from image_gen import create_instagram_story
from instagram_upload import upload_story
from article_store import (
    build_image_path,
    get_pending_image_article,
    mark_critic_feedback,
    mark_image_failure,
    mark_image_generated,
    upsert_articles,
)

DEFAULT_QUERY = "latest hot tech news"
DEFAULT_MAX_RESULTS = 10


def _prompt_run_config(default_query: str, default_max_results: int) -> tuple[str, int]:
    query_input = input(f"News query [{default_query}]: ").strip()
    query = query_input or default_query

    max_results_input = input(f"How many results to fetch [{default_max_results}]: ").strip()
    if not max_results_input:
        return query, default_max_results

    try:
        value = int(max_results_input)
        if value < 1:
            raise ValueError
        return query, value
    except ValueError:
        print(f"Invalid number '{max_results_input}', using default {default_max_results}.")
        return query, default_max_results


def job(query: str = DEFAULT_QUERY, max_results: int = DEFAULT_MAX_RESULTS):
    print("\n--- Running Tech News Instagram Job ---")
    try:
        pending_article = get_pending_image_article()

        # 1. If we already fetched news but didn't generate an image, resume that first.
        if pending_article:
            print(f"Resuming pending article: {pending_article.get('title', 'Untitled')}")
        else:
            print("No pending article found. Fetching fresh news...")
            agent = TechNewsAgent()
            report = agent.get_hot_news(query=query, max_results=max_results)

            if not report.articles:
                print("No articles found.")
                return

            inserted = upsert_articles(report.articles)
            print(f"Stored/updated {len(report.articles)} articles in articles.json ({inserted} new).")
            pending_article = get_pending_image_article()

            if not pending_article:
                print("No pending article available for image generation.")
                return

        # 2. Critic Review (or reuse previously saved critic output)
        status = pending_article.get("status", {})
        if (
            status.get("critic_done")
            and pending_article.get("final_title")
            and pending_article.get("final_summary")
        ):
            title_to_use = pending_article["final_title"]
            summary_to_use = pending_article["final_summary"]
            print("Using previously saved critic output.")
        else:
            critic = CriticAgent()
            feedback = critic.critique_article(
                pending_article.get("title", ""),
                pending_article.get("summary") or "",
            )
            
            print(f"Critic Approved? {feedback.approved}")
            print(f"Critic Feedback: {feedback.feedback}")

            title_to_use = (
                feedback.improved_title
                if feedback.improved_title and not feedback.approved
                else pending_article.get("title", "")
            )
            summary_to_use = (
                feedback.improved_summary
                if feedback.improved_summary and not feedback.approved
                else pending_article.get("summary")
            )
            
            print(f"Final Title: {title_to_use}")
            print(f"Final Summary: {summary_to_use}")
            mark_critic_feedback(
                pending_article["id"],
                feedback,
                title_to_use,
                summary_to_use or "Click to read more!",
            )

        # 3. Generate Image
        image_path = build_image_path(pending_article["id"])
        generated_path = create_instagram_story(
            title_to_use,
            summary_to_use or "Click to read more!",
            pending_article.get("source") or "Unknown",
            image_path,
            pending_article.get("image_url"),
        )

        if generated_path:
            mark_image_generated(pending_article["id"], generated_path)
        else:
            mark_image_failure(pending_article["id"], "Image generation returned no output path.")
            print("Image generation failed. Article stays pending for retry.")
            return
        
        # 4. Upload to Instagram
        # upload_story(generated_path)
        print("Job Complete (Image Generated, Upload Skipped)!\n")
        
    except Exception as e:
        if "pending_article" in locals() and pending_article:
            mark_image_failure(pending_article["id"], str(e))
        print(f"Error in job pipeline: {e}")

def main():
    parser = argparse.ArgumentParser(description="Tech News Instagram Story Agent")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="News search query")
    parser.add_argument(
        "--max-results",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help="Number of news items to fetch when searching",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for query and max results at startup",
    )
    args = parser.parse_args()

    query = args.query
    max_results = args.max_results if args.max_results > 0 else DEFAULT_MAX_RESULTS
    if args.max_results <= 0:
        print(f"Invalid --max-results '{args.max_results}', using {DEFAULT_MAX_RESULTS}.")

    if args.interactive:
        query, max_results = _prompt_run_config(query, max_results)

    print("Instagram Story Tech News Agent Started!")
    print("Scheduling job for every Tuesday at 10:00 AM...")
    print(f"Search config: query='{query}', max_results={max_results}")
    
    # Schedule for every Tuesday at 10:00 AM local time
    schedule.every().tuesday.at("10:00").do(job, query, max_results)
    
    # ---------------------------------------------------------
    # NOTE: Comment the line below if you want schedule-only execution.
    # ---------------------------------------------------------
    job(query, max_results)
    
    print("Waiting for scheduled tasks. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
