"""Tests for the stock news agent."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from stock_news_agent import score_article, pick_top_story, format_markdown


def make_article(title="Test Title", summary="Test summary", source="Test Source",
                 link="https://example.com", published="2026-01-01"):
    return {
        "title": title,
        "summary": summary,
        "link": link,
        "source": source,
        "published": published,
    }


class TestScoreArticle:
    def test_keyword_boost(self):
        article = make_article(
            title="Fed raises interest rate by 0.5%",
            summary="The Federal Reserve announced a rate hike today."
        )
        score = score_article(article)
        # Should match: fed, federal reserve, interest rate, plus % in title
        assert score > 0

    def test_no_keywords_low_score(self):
        article = make_article(
            title="Local bakery opens new branch",
            summary="A small bakery opened today."
        )
        score = score_article(article)
        assert score < 3

    def test_percentage_in_title_bonus(self):
        with_pct = make_article(title="Stock surges 15% after earnings")
        without_pct = make_article(title="Stock surges after earnings")
        assert score_article(with_pct) > score_article(without_pct)

    def test_longer_summary_bonus(self):
        short = make_article(summary="Brief.")
        long = make_article(summary=" ".join(["word"] * 60))
        assert score_article(long) > score_article(short)


class TestPickTopStory:
    def test_returns_none_for_empty(self):
        assert pick_top_story([]) is None

    def test_returns_highest_scored(self):
        boring = make_article(title="Nothing happened", summary="Quiet day.")
        exciting = make_article(
            title="Nvidia surges 20% on AI earnings record",
            summary="Nvidia reported record earnings driven by AI demand, "
                    "sending shares up 20% in after-hours trading. "
                    "The company beat analyst estimates by a wide margin."
        )
        result = pick_top_story([boring, exciting])
        assert result is not None
        assert "Nvidia" in result["title"]

    def test_single_article(self):
        article = make_article(title="Solo article")
        result = pick_top_story([article])
        assert result["title"] == "Solo article"


class TestFormatMarkdown:
    def test_contains_title(self):
        article = make_article(title="Big News", score=5.0)
        article["score"] = 5.0
        md = format_markdown(article, "2026-01-01")
        assert "Big News" in md
        assert "2026-01-01" in md

    def test_contains_link(self):
        article = make_article(link="https://example.com/story")
        article["score"] = 1.0
        md = format_markdown(article, "2026-01-01")
        assert "https://example.com/story" in md

    def test_contains_source(self):
        article = make_article(source="CNBC")
        article["score"] = 1.0
        md = format_markdown(article, "2026-01-01")
        assert "CNBC" in md
