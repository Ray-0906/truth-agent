"""Shared configuration values for the news & information verification agents."""

from dataclasses import dataclass

MODEL = "gemini-2.0-flash"


@dataclass(frozen=True)
class StateKeys:
    """Centralized session.state keys used across the workflow."""

    # News lane
    NEWS_API: str = "news_api_signal"
    NEWS_FACT: str = "news_fact_checker_signal"
    NEWS_PERPLEXITY: str = "news_perplexity_signal"
    NEWS_SUMMARY: str = "news_check_summary"

    # Fact lane
    FACT_PRIMARY: str = "fact_primary_signal"
    FACT_PERPLEXITY: str = "fact_perplexity_signal"
    FACT_SUMMARY: str = "fact_check_summary"

    # Scam lane
    SCAM_SENTIMENT: str = "scam_sentiment_signal"
    SCAM_PERPLEXITY: str = "scam_perplexity_signal"
    SCAM_LINK: str = "scam_link_signal"
    SCAM_SUMMARY: str = "scam_check_summary"

    # Final response
    FINAL_REPORT: str = "final_report"


STATE_KEYS = StateKeys()
