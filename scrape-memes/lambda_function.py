'''
This AWS Lambda function scrapes the top 20 daily memes from r/memes using \
PRAW (Python Reddit API Wrapper) and stores them in a DynamoDB table. \
It handles various media types including images, GIFs, and videos.
'''

import boto3
import praw
import json
import os
from datetime import datetime

# get Reddit API credentials
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = "lambda-roody-bot/0.1"


def lambda_handler(event, context):
    '''
    Scrapes r/memes to retrieve data on the top 20 memes

    The keys for each post are:
        - date (str)(PK): date in YYYY-MM-DD format
        - index (int)(SK): ranking from 1-20 

    The fields for each post are:
        - title (str): Title of the Reddit post
        - author(str): Author of the Reddit post
        - url (str): URL of the meme image/post
        - thumbnail (str): URL of the thumbnail image used in the pdf
        - post_created_at (str): Post creation date in iso format
        - upvotes (int): Number of upvotes
        - awards (int): Number of awards received
        - media_type (str): Type of media, either 'gif', 'video'
    '''
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
