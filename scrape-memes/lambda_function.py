import boto3
import praw
import json
import os
from datetime import datetime

# Reddit API credentials (use environment variables in Lambda)
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = "lambda-roody-bot/0.1"


def lambda_handler(event, context):
    # Initialize PRAW client
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )

    # Get top posts from r/memes
    memes = reddit.subreddit("memes")
    data = []
    # Retrieve data from each post
    for index, submission in enumerate(memes.top(time_filter="day", limit=20)):
        post = {}
        post['_date'] = datetime.today().strftime('%Y-%m-%d')
        post['_id'] = index
        try:
            created_datetime = datetime.fromtimestamp(submission.created)
            post['post_created_at'] = created_datetime.isoformat()
            post['author'] = submission.author.name
            post['title'] = submission.title
            post['upvotes'] = submission.ups
            post['awards'] = submission.total_awards_received
            post['url'] = submission.url
            if ".gif" in submission.url:
                post['thumbnail'] = submission.thumbnail
                post['media_type'] = "gif"
            elif any(ext in submission.url for ext in [".png", ".jpeg", ".jpg"]):
                post['thumbnail'] = submission.url
            else:
                post['thumbnail'] = submission.preview['images'][0]['source']['url']
                post['media_type'] = "video"
            data.append(post)
        except AttributeError as e:
            print(f"Skipping post due to missing attribute: {e}")

    print("Initializing DB...")
    table_name = 'memes'
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    print("Writing to DB...")
    with table.batch_writer() as batch_writer:
        for post in data:
            print("> batch writing: {}".format(post['title']))
            batch_writer.put_item(Item=post)

    result = f"Success. Added {len(data)} item to {table_name}."

    return {
        "statusCode": 200,
        'message': result,
        "body": json.dumps(post),
    }
