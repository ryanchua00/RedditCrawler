import requests
import base64
import boto3
import json
import os

# Get environment variables and aws lambda client
BOT_TOKEN = os.getenv("BOT_TOKEN")
lambda_client = boto3.client('lambda')


def sendMessage(chat_id, message):
    """
    The function `sendMessage` sends a message to a specified chat ID using the Telegram API.

    :chat_id:
    The Telegram unique identifier for the chat where you want to send the message.

    :message:
    The text string that will be sent to the specified chat.
    """
    reply = {
        "chat_id": chat_id,
        "text": message
    }
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(url, json=reply)

    print(f"*** sendMessage Response : {response.json()}")


def sendDocument(chat_id, data, filename="reddit_memes.pdf"):
    """
    The function `sendDocument` sends a document to a specified chat ID using the Telegram API.

    :chat_id:
    The Telegram unique identifier for the chat where you want to send the document.

    :data:
    The base64 encoded pdf data that will be sent to the specified chat.

    :filename:
    Optional text string that the pdf will be named as.
    """
    pdf_bytes = base64.b64decode(data)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    files = {
        "document": (filename, pdf_bytes, "application/pdf")
    }
    chat_data = {
        "chat_id": chat_id
    }
    response = requests.post(url, files=files, data=chat_data)

    print(f"*** sendDocument Response : {response.json()}")


def lambda_handler(event, context):
    print("*** Received event")

    chat_id = event['message']['from']['id']
    user_name = event['message']['from']['username']
    message_text = event['message']['text']

    print(f"*** chat id: {chat_id}")
    print(f"*** user name: {user_name}")
    print(f"*** message text: {message_text}")

    # Filter response based on message
    if message_text == "/getmemes":
        # Call scrape-memes
        response_get = lambda_client.invoke(
            FunctionName='scrape-memes',
            InvocationType='RequestResponse'
        )
        sendMessage(chat_id, "Top daily memes gathered 👍")
    elif message_text == "/getreport":
        sendMessage(chat_id, "Generating a report... 📝")
        # Call get-memes
        response_get = lambda_client.invoke(
            FunctionName='get-memes',
            InvocationType='RequestResponse'
        )
        response_payload = response_get['Payload'].read().decode('utf-8')
        report_data = json.loads(response_payload)
        sendDocument(chat_id, report_data["body"])
    else:
        # Default response
        message_text = "Hello! Use /getmemes followed by /getreport to get started."
        sendMessage(chat_id, message_text)

    return {
        'statusCode': 200,
        'body': json.dumps('Message processed successfully')
    }
