from flask import Flask, request, Response, render_template_string
import boto3
from datetime import datetime
import os

# Initialize Flask application
app = Flask(__name__)

# Initialize boto3 client for S3 interactions
s3 = boto3.client('s3')

# Retrieve the S3 bucket name from an environment variable
BUCKET_NAME = os.environ.get("DB_NAME")

def save_message_to_s3(message, prefix):
    """
    Saves an SMS message to an S3 bucket.

    :param message: The content of the SMS message.
    :param prefix: The prefix for the S3 file naming.
    """
    try:
        # Create a unique filename with a timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        filename = f'{prefix}_{timestamp}.txt'

        # Save the file to S3
        s3.put_object(Bucket=BUCKET_NAME, Key=filename, Body=message)
    except Exception as e:
        # Log any exceptions that occur
        print(f"An error occurred: {str(e)}")

@app.route('/', methods=['POST'])
def receive_sms():
    """
    Endpoint to receive SMS from Twilio, save it to S3, and respond with empty TwiML.
    """
    message_body = request.form.get('Body', '')  # Extract the message content from the request
    save_message_to_s3(message_body, "sms")  # Save the SMS message to S3

    # Return an empty TwiML response to acknowledge receipt of the message
    return Response('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', mimetype='text/xml')

@app.route('/', methods=['GET'])
def display_last_message():
    """
    Endpoint to fetch and display the most recent message saved in S3.
    """
    try:
        # Retrieve the list of files saved in S3 under the 'sms_' prefix
        files = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix='sms_')['Contents']

        # Sort and retrieve the most recent file
        recent_file = sorted(files, key=lambda x: x['LastModified'], reverse=True)[0]

        # Fetch the content of the most recent file
        file_content = s3.get_object(Bucket=BUCKET_NAME, Key=recent_file['Key'])['Body'].read().decode('utf-8')

        # Construct HTML to display the message content
        html_content = f"""
        <!doctype html>
        <html>
            <head>
                <title>Last Message Received</title>
            </head>
            <body>
                <h1>Most Recent Message</h1>
                <p>{file_content}</p>
            </body>
        </html>
        """
        return render_template_string(html_content)
    except Exception as e:
        # If an error occurs, return the error message
        return str(e)

if __name__ == '__main__':
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5001)

