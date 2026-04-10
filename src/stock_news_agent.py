"""
Daily Stock News Agent

Fetches stock market news from multiple RSS feeds, scores them by relevance
and engagement signals, and outputs the most interesting story of the day.
"""

import datetime
import json
import os
import re
import sys
from pathlib import Path

import feedparser

# RSS feeds from major financial news sources
NEWS_FEEDS = [
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^DJI&region=US&lang=en-US",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^IXIC&region=US&lang=en-US",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # CNBC Top News
    "https://www.cnbc.com/id/10001147/device/rss/rss.html",  # CNBC Markets
    "https://feeds.marketwatch.com/marketwatch/topstories/",
    "https://feeds.marketwatch.com/marketwatch/marketpulse/",
]

# Keywords that boost a story's score (market-moving topics)
HIGH_INTEREST_KEYWORDS = [
    "fed", "federal reserve", "interest rate", "inflation", "recession",
    "earnings", "ipo", "merger", "acquisition", "crash", "rally", "surge",
    "plunge", "record", "billion", "trillion", "sec", "regulation",
    "layoffs", "bankruptcy", "ai", "nvidia", "tesla", "apple", "amazon",
    "microsoft", "google", "meta", "bitcoin", "crypto", "oil", "gold",
    "s&p 500", "dow jones", "nasdaq", "volatility", "breakout",
]


def fetch_articles() -> list[dict]:
    """Fetch articles from all configured RSS feeds."""
    articles = []
    seen_titles = set()

    for feed_url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                if not title or title.lower() in seen_titles:
                    continue
                seen_titles.add(title.lower())

                summary = entry.get("summary", entry.get("description", "")).strip()
                # Strip HTML tags from summary
                summary = re.sub(r"<[^>]+>", "", summary).strip()

                published = entry.get("published", entry.get("updated", ""))
                link = entry.get("link", "")
                source = feed.feed.get("title", feed_url)

                articles.append({
                    "title": title,
                    "summary": summary,
                    "published": published,
                    "link": link,
                    "source": source,
                })
        except Exception as e:
            print(f"Warning: failed to fetch {feed_url}: {e}", file=sys.stderr)

    return articles


def score_article(article: dict) -> float:
    """
    Score an article based on keyword relevance and content signals.

    Higher score = more interesting / market-relevant.
    """
    score = 0.0
    text = f"{article['title']} {article['summary']}".lower()

    # Keyword matches
    for keyword in HIGH_INTEREST_KEYWORDS:
        if keyword in text:
            score += 2.0

    # Bonus for longer, more substantive summaries
    word_count = len(text.split())
    if word_count > 50:
        score += 3.0
    elif word_count > 25:
        score += 1.5

    # Bonus for numbers in title (usually signals concrete data)
    if re.search(r"\d+%|\$[\d.]+", article["title"]):
        score += 2.0

    # Bonus for exclamation or question marks (engagement signals)
    if "?" in article["title"] or "!" in article["title"]:
        score += 1.0

    return score


def pick_top_story(articles: list[dict]) -> dict | None:
    """Return the highest-scored article."""
    if not articles:
        return None

    scored = [(score_article(a), a) for a in articles]
    scored.sort(key=lambda x: x[0], reverse=True)

    top_score, top_article = scored[0]
    top_article["score"] = top_score
    return top_article


def format_markdown(article: dict, date_str: str) -> str:
    """Format the top story as a markdown section."""
    lines = [
        f"## {date_str} - Top Stock Market Story",
        "",
        f"### {article['title']}",
        "",
        f"**Source:** {article['source']}",
        "",
    ]
    if article.get("summary"):
        lines.extend([article["summary"], ""])
    if article.get("link"):
        lines.extend([f"[Read full article]({article['link']})", ""])
    if article.get("published"):
        lines.extend([f"*Published: {article['published']}*", ""])

    lines.append(f"*Relevance score: {article.get('score', 0):.1f}*")
    lines.append("")
    return "\n".join(lines)


def append_to_log(content: str, log_path: Path) -> None:
    """Append today's story to the running log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)

    existing = ""
    if log_path.exists():
        existing = log_path.read_text()

    # Prepend new content so latest is on top
    with open(log_path, "w") as f:
        f.write(content + "\n---\n\n" + existing)


def main() -> int:
    today = datetime.date.today().isoformat()
    print(f"Stock News Agent - {today}")
    print("=" * 40)

    print("Fetching articles from RSS feeds...")
    articles = fetch_articles()
    print(f"Found {len(articles)} unique articles.")

    if not articles:
        print("No articles found. Check network connectivity or feed URLs.")
        return 1

    top = pick_top_story(articles)
    if not top:
        print("Could not determine a top story.")
        return 1

    print(f"\nTop story: {top['title']}")
    print(f"Score: {top.get('score', 0):.1f}")
    print(f"Source: {top['source']}")

    # Generate markdown output
    md_content = format_markdown(top, today)

    # Write to log file
    project_root = Path(__file__).resolve().parent.parent
    log_path = project_root / "output" / "daily_news.md"
    append_to_log(md_content, log_path)
    print(f"\nAppended to {log_path}")

    # Also write structured JSON for programmatic use
    json_path = project_root / "output" / "latest.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w") as f:
        json.dump({"date": today, "top_story": top}, f, indent=2, ensure_ascii=False)
    print(f"Written to {json_path}")

    # Print for GitHub Actions step output
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as gh_out:
            # Escape newlines for GH Actions
            safe_title = top["title"].replace("\n", " ")
            gh_out.write(f"story_title={safe_title}\n")
            gh_out.write(f"story_link={top.get('link', '')}\n")
            gh_out.write(f"story_source={top.get('source', '')}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
