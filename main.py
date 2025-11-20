"""
main.py

Simple read-only Reddit client for collecting caregiving-related questions
from a few subreddits. This is meant to be used as input to a separate
NLP / clustering pipeline (e.g., in a Jupyter or Colab notebook).

Usage:
    - Set environment variables for Reddit API credentials:
        REDDIT_CLIENT_ID
        REDDIT_CLIENT_SECRET
        REDDIT_USERNAME
        REDDIT_PASSWORD
        REDDIT_USER_AGENT

    - Then run:
        python main.py
"""

import os
import sys
from typing import List, Dict

import praw
import pandas as pd


SUBREDDITS = [
    "eldercare",
    "caregivers",
    "agingparents",
    "dementia",
    "nursing",
    "premed",
]

SEARCH_QUERY = "care OR dementia OR help OR caregiver OR senior"
POST_LIMIT_PER_SUB = 50  # keep small for demo; can be tuned later
OUTPUT_CSV = "caregiving_reddit_posts.csv"


def get_reddit_client() -> praw.Reddit:
    """Create and return an authenticated, read-only Reddit client."""
    try:
        client_id = os.environ["REDDIT_CLIENT_ID"]
        client_secret = os.environ["REDDIT_CLIENT_SECRET"]
        username = os.environ["REDDIT_USERNAME"]
        password = os.environ["REDDIT_PASSWORD"]
        user_agent = os.environ.get(
            "REDDIT_USER_AGENT",
            "caregiving-intent-miner (read-only research script)",
        )
    except KeyError as e:
        print(f"Missing environment variable: {e}", file=sys.stderr)
        sys.exit(1)

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        username=username,
        password=password,
    )

    # Safety: enforce read-only mode
    reddit.read_only = True
    return reddit


def fetch_posts(reddit: praw.Reddit) -> List[Dict]:
    """Fetch posts from the configured subreddits using a simple search query."""
    results: List[Dict] = []

    for sub_name in SUBREDDITS:
        print(f"Fetching posts from r/{sub_name} ...")
        subreddit = reddit.subreddit(sub_name)

        # Use search to bias toward more question-like / relevant content
        for post in subreddit.search(SEARCH_QUERY, limit=POST_LIMIT_PER_SUB):
            # Skip stickied / very old / empty selftext if you want
            if post.stickied:
                continue

            text = f"{post.title}\n\n{post.selftext or ''}".strip()
            if not text:
                continue

            results.append(
                {
                    "subreddit": sub_name,
                    "id": post.id,
                    "title": post.title,
                    "body": post.selftext,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "created_utc": post.created_utc,
                    "permalink": f"https://www.reddit.com{post.permalink}",
                    "text": text,
                }
            )

    return results


def main() -> None:
    reddit = get_reddit_client()
    posts = fetch_posts(reddit)

    if not posts:
        print("No posts collected. Try adjusting SEARCH_QUERY or limits.")
        return

    df = pd.DataFrame(posts)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved {len(df)} posts to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
