'''
This AWS Lambda function generates a PDF report of the top memes from r/memes subreddit \
that have been scraped and stored in a DynamoDB table. The function:

Note: reportlab is not included in requirements.txt, as a layer is being used in AWS Lambda.
Layer: arn:aws:lambda:ap-southeast-1:770693421928:layer:Klayers-p311-reportlab:8
This is done due to a dependency issue with PIL, seen here:
https://stackoverflow.com/questions/57197283/aws-lambda-cannot-import-name-imaging-from-pil

'''


from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from io import BytesIO
from PIL import Image
import requests
import base64
import boto3

# Get AWS dynamodb table - memes
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('memes')


def get_pil_image_from_url(url):
    try:
        response = requests.get(url)
        img_data = BytesIO(response.content)
        img_data.seek(0)
        img = Image.open(img_data)
        return img
    except requests.exceptions.RequestException as e:
        print(f"Download failed: {e}")
    except Exception as e:
        print(f"Image processing error: {e}")


def create_pdf(data):
    """
    Creates a pdf and returns a buffer object containing the pdf

    Args:
        data (list[dict]): A list of dictionaries containing meme post data. Each dictionary should contain:
            - title (str): Title of the Reddit post
            - url (str): URL of the meme image/post
            - thumbnail (str): URL of the thumbnail image used in the pdf
            - post_created_at (str): Post creation date in iso format
            - upvotes (int): Number of upvotes
            - awards (int): Number of awards received
            - media_type (str): Type of media, either 'gif', 'video'

    Returns:
        BytesIO: A buffer object containing the generated PDF data

    Note:
        - Urls represent a link for the user to visit the post, and thumbnails are pictures used in the report
        - Images are downloaded from URLs and resized to fit the PDF
    """
    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
    _, height = letter
    y_position = height - 50  # Starting position

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, y_position, "Top r/memes Posts")
    y_position -= 35

    for index, post in enumerate(data, 1):
        # Avoids writing beyond the page, adds a new page if needed
        if y_position < 200 or index % 2 == 1 and index > 1:
            pdf.showPage()
            y_position = height - 50
            pdf.setFont("Helvetica", 12)

        # Write post details
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(
            50, y_position, f"{index}. {post['title']}")
        y_position -= 20

        # Author, date, upvotes, awards
        pdf.setFont("Helvetica-Oblique", 12)
        pdf.drawString(
            50, y_position, f"By {post['author']} on {post['post_created_at']} | ⬆ {post['upvotes']} upvotes | ⭐ {post['awards']} awards")
        y_position -= 15

        # Url
        pdf.setFillColorRGB(0, 0, 1)  # Blue for hyperlink
        pdf.setFont("Helvetica-Oblique", 10)
        pdf.drawString(50, y_position, post['url'])
        pdf.setFillColorRGB(0, 0, 0)  # Reset color
        y_position -= 20  # Space before image

        if 'media_type' in post:
            y_position += 5
            pdf.drawString(50, y_position, f"({post['media_type']})")
            y_position -= 5

        try:
            # Download image and save as JPEG to reduce space
            img_data = get_pil_image_from_url(post['url'])
            buffer = BytesIO()
            img_data.save(buffer, format='JPEG', quality=85,
                          optimize=True, progressive=True)
            buffer.seek(0)
            img_data = ImageReader(buffer)

            # Resize img_data to fit into pdf
            img_width, img_height = img_data.getSize()
            fixed_height = 280
            scaled_width = fixed_height/img_height*img_width
            img_x = 50
            img_y = y_position - fixed_height
            pdf.drawImage(img_data, img_x, img_y,
                          height=fixed_height, width=scaled_width)

            y_position -= fixed_height  # Move cursor down after the image

        except Exception as e:
            print(f"Error displaying image: {e}")
            pdf.setFont("Helvetica-Oblique", 12)
            y_position -= 15

        y_position -= 20  # Extra space between posts

    pdf.save()
    pdf_buffer.seek(0)
    return pdf_buffer


def lambda_handler(event, context):
    # Select items with primary key as todays date in %Y-%m-%d format
    today = datetime.today().strftime('%Y-%m-%d')
    data = table.query(
        KeyConditionExpression='#date = :date_val',  # Use a placeholder
        ExpressionAttributeNames={
            '#date': '_date'  # Map "#date" to the actual attribute "_date"
        },
        ExpressionAttributeValues={
            ':date_val': today
        }
    )

    # No memes found
    if len(data['Items']) == 0 or len(data['Items']) < 20:
        return {
            "statusCode": 404,
            "message": "No records found with today's date."
        }

    pdf_buffer = create_pdf(data['Items'])

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/pdf",
            "Content-Disposition": "inline; filename=reddit_memes.pdf",
        },
        "body": base64.b64encode(pdf_buffer.read()).decode("utf-8"),
        "isBase64Encoded": True
    }
