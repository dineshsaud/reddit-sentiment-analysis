from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import praw


def fetch_reddit_posts():

    reddit = praw.Reddit(
        client_id="r94GjVVAvjzUEbwIAUqosQ",
        client_secret="wLkmfiRTXGXuXXBRQ1ISAYvseDJ_mA",
        user_agent="airflow-reddit-sentiment/0.1 by u/Forward-Image-613"
    )

    subreddit = reddit.subreddit("depression")
    posts = []

    for post in subreddit.hot(limit=50):
        posts.append({
            "id": post.id,
            "title": post.title,
            "selftext": post.selftext,
            "score": post.score,
            "created_utc": post.created_utc
        })

    df = pd.DataFrame(posts)
    df.to_csv("/opt/airflow/data/reddit_posts.csv", index=False)
    print("Saved reddit_posts.csv")




def perform_sentiment_analysis():
    import pandas as pd
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    import nltk

    nltk.download("vader_lexicon")

    df = pd.read_csv("/opt/airflow/data/reddit_posts.csv")

    # Combine title + selftext
    df["full_text"] = df["title"].fillna('') + " " + df["selftext"].fillna('')

    sia = SentimentIntensityAnalyzer()

    def get_sentiment(text):
        score = sia.polarity_scores(text)["compound"]
        if score >= 0.05:
            return "Positive"
        elif score <= -0.05:
            return "Negative"
        else:
            return "Neutral"

    df["sentiment"] = df["full_text"].apply(get_sentiment)
    df.to_csv("/opt/airflow/data/reddit_sentiment.csv", index=False)
    print(" Saved reddit_sentiment.csv")

with DAG(
    dag_id="sentiment_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@once",
    catchup=False,
    tags=["sentiment", "reddit", "twitter"]
) as dag:

    fetch_reddit = PythonOperator(
        task_id="fetch_reddit_posts",
        python_callable=fetch_reddit_posts
    )

    analyze_sentiment = PythonOperator(
        task_id="perform_sentiment_analysis",
        python_callable=perform_sentiment_analysis
    )

    fetch_reddit >> analyze_sentiment


