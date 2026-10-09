"""
Logs every query/response pair to a CSV file.

This isn't just for debugging -- it's the raw data for your evaluation
chapter. After a test session (or after your volunteer speakers try the
system), open logs/interactions.csv in Excel/pandas and you can directly
compute: intent-match rate, knowledge-base hit rate, average response
latency, and a breakdown of which queries went unanswered.
"""

import csv
import os
import time

from config import LOG_PATH


def log_interaction(query: str, intent: str, source: str, confidence: float, response_time_s: float) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    is_new = not os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(
                ["timestamp", "query", "intent", "source", "confidence", "response_time_s"]
            )
        writer.writerow(
            [
                time.strftime("%Y-%m-%d %H:%M:%S"),
                query,
                intent,
                source or "",
                round(confidence, 3),
                round(response_time_s, 3),
            ]
        )
