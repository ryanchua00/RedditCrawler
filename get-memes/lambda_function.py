from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from PIL import Image
from datetime import datetime
import requests
import base64
import boto3

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
    return None


def create_pdf(data):
    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
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

        pdf.setFont("Helvetica-Oblique", 12)
        pdf.drawString(
            50, y_position, f"By {post['author']} on {post['post_created_at']} | ⬆ {post['upvotes']} upvotes | ⭐ {post['awards']} awards")
        y_position -= 15

        # Link (Optional, clickable in some PDF readers)
        pdf.setFillColorRGB(0, 0, 1)  # Blue for hyperlink
        pdf.setFont("Helvetica-Oblique", 10)

        if 'media_type' in post and post['media_type'] == "video":
            pdf.drawString(50, y_position, post['video_url'])
        elif 'media_type' in post and post['media_type'] == "gif":
            pdf.drawString(50, y_position, post['gif_url'])
        else:
            pdf.drawString(50, y_position, post['url'])
        pdf.setFillColorRGB(0, 0, 0)  # Reset color
        y_position -= 20  # Space before image

        if 'media_type' in post:
            y_position += 5
            pdf.drawString(50, y_position, f"({post['media_type']})")
            y_position -= 5

        # Download and add image
        # print(img_data.format, img_data.mode, img_data.size)
        # TODO: detect for ending with .jpeg instead
        try:
            img_data = get_pil_image_from_url(post['url'])
            buffer = BytesIO()
            img_data.save(buffer, format='JPEG', quality=85,
                          optimize=True, progressive=True)
            buffer.seek(0)
            img_data = ImageReader(buffer)

            # Resize jpeg
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
    # webbrowser.open(filename)  # Opens the PDF


def lambda_handler(event, context):

    # Select items with primary key
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

    if len(data['Items']) == 0 or len(data['Items']) < 20:
        return {
            "statusCode": 404,
            "message": "No records found with today's date."
        }

    pdf_buffer = create_pdf(data['Items'])
    # force
    # return data['Items']
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/pdf",
            "Content-Disposition": "inline; filename=reddit_memes.pdf",
        },
        "body": base64.b64encode(pdf_buffer.read()).decode("utf-8"),
        "isBase64Encoded": True
    }
