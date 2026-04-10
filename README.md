# Daily Stock News Agent

Automated agent that finds the most interesting stock market news every trading day and logs it.

## How it works

1. **Fetches** articles from multiple financial RSS feeds (Yahoo Finance, CNBC, MarketWatch)
2. **Scores** each article based on keyword relevance, content signals, and engagement indicators
3. **Picks** the top story and writes it to `output/daily_news.md` and `output/latest.json`
4. **Creates** a GitHub Issue with the top story for easy tracking

## Schedule

Runs automatically via GitHub Actions every weekday at 18:00 UTC (after US market close). Can also be triggered manually from the Actions tab.

## Local usage

```bash
pip install -r requirements.txt
python src/stock_news_agent.py
```

## Output

- `output/daily_news.md` - Running log of top stories (newest first)
- `output/latest.json` - Structured JSON of the latest top story
- GitHub Issues labeled `stock-news` - One issue per trading day

## Running tests

```bash
pip install pytest
pytest tests/
```

## Project structure

```
src/stock_news_agent.py          # Main agent script
tests/test_stock_news_agent.py   # Unit tests
.github/workflows/daily-stock-news.yml  # Cron workflow
output/                          # Generated output directory
```
