import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

STORE_PATH = "articles.json"
IMAGE_OUTPUT_DIR = "generated_stories"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _default_store() -> Dict[str, Any]:
    return {"version": 1, "articles": []}


def _article_id_from_url(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def _normalize_article(raw_article: Any) -> Dict[str, Any]:
    article = raw_article.model_dump() if hasattr(raw_article, "model_dump") else dict(raw_article)
    return {
        "title": article.get("title", ""),
        "url": article.get("url", ""),
        "image_url": article.get("image_url"),
        "summary": article.get("summary"),
        "source": article.get("source"),
        "published_date": article.get("published_date"),
        "relevance_score": float(article.get("relevance_score") or 0.0),
    }


def load_store(path: str = STORE_PATH) -> Dict[str, Any]:
    if not os.path.exists(path):
        return _default_store()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _default_store()

    if not isinstance(data, dict):
        return _default_store()
    if "articles" not in data or not isinstance(data["articles"], list):
        data["articles"] = []
    if "version" not in data:
        data["version"] = 1
    return data


def save_store(store: Dict[str, Any], path: str = STORE_PATH) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)


def upsert_articles(articles: List[Any], path: str = STORE_PATH) -> int:
    store = load_store(path)
    now = _utc_now_iso()
    by_id = {article.get("id"): article for article in store["articles"] if article.get("id")}
    inserted = 0

    for raw in articles:
        article = _normalize_article(raw)
        if not article["url"]:
            continue

        article_id = _article_id_from_url(article["url"])
        existing = by_id.get(article_id)

        if existing:
            existing.update(article)
            existing["updated_at"] = now
            status = existing.setdefault("status", {})
            status.setdefault("fetched_at", now)
            status.setdefault("critic_done", False)
            status.setdefault("image_generated", False)
            status.setdefault("image_path", None)
            status.setdefault("image_generated_at", None)
            status.setdefault("uploaded", False)
            status.setdefault("upload_attempted", False)
            status.setdefault("last_error", None)
            continue

        inserted += 1
        new_article = {
            "id": article_id,
            **article,
            "final_title": None,
            "final_summary": None,
            "critic_feedback": None,
            "status": {
                "fetched_at": now,
                "critic_done": False,
                "image_generated": False,
                "image_path": None,
                "image_generated_at": None,
                "uploaded": False,
                "upload_attempted": False,
                "last_error": None,
            },
            "updated_at": now,
        }
        store["articles"].append(new_article)
        by_id[article_id] = new_article

    save_store(store, path)
    return inserted


def get_pending_image_article(path: str = STORE_PATH) -> Optional[Dict[str, Any]]:
    store = load_store(path)
    pending = [
        article
        for article in store["articles"]
        if not article.get("status", {}).get("image_generated", False)
    ]
    if not pending:
        return None

    pending.sort(
        key=lambda item: (
            float(item.get("relevance_score") or 0.0),
            item.get("status", {}).get("fetched_at", ""),
        ),
        reverse=True,
    )
    return pending[0]


def mark_critic_feedback(
    article_id: str,
    feedback: Any,
    final_title: str,
    final_summary: str,
    path: str = STORE_PATH,
) -> bool:
    store = load_store(path)
    now = _utc_now_iso()

    for article in store["articles"]:
        if article.get("id") != article_id:
            continue
        article["critic_feedback"] = feedback.model_dump() if hasattr(feedback, "model_dump") else feedback
        article["final_title"] = final_title
        article["final_summary"] = final_summary
        article["updated_at"] = now
        status = article.setdefault("status", {})
        status["critic_done"] = True
        status["last_error"] = None
        save_store(store, path)
        return True

    return False


def mark_image_generated(article_id: str, image_path: str, path: str = STORE_PATH) -> bool:
    store = load_store(path)
    now = _utc_now_iso()

    for article in store["articles"]:
        if article.get("id") != article_id:
            continue
        status = article.setdefault("status", {})
        status["image_generated"] = True
        status["image_path"] = image_path
        status["image_generated_at"] = now
        status["last_error"] = None
        article["updated_at"] = now
        save_store(store, path)
        return True

    return False


def mark_image_failure(article_id: str, error_message: str, path: str = STORE_PATH) -> bool:
    store = load_store(path)
    now = _utc_now_iso()

    for article in store["articles"]:
        if article.get("id") != article_id:
            continue
        status = article.setdefault("status", {})
        status["image_generated"] = False
        status["last_error"] = error_message
        article["updated_at"] = now
        save_store(store, path)
        return True

    return False


def build_image_path(article_id: str, output_dir: str = IMAGE_OUTPUT_DIR) -> str:
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, f"{article_id}.jpg")
