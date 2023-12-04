from flask import Flask, request, Response, render_template_string, jsonify
import boto3
from datetime import datetime
import os
import json

# Initialize Flask application
app = Flask(__name__)

# Initialize boto3 client for S3 interactions
s3 = boto3.client('s3')

# Retrieve the S3 bucket name from an environment variable
BUCKET_NAME = os.environ.get("DB_NAME")

def save_message_to_s3(message, prefix, is_json=False):
    """
    Saves an SMS message or JSON data to an S3 bucket.

    :param message: The content of the SMS message or JSON data.
    :param prefix: The prefix for the S3 file naming.
    :param is_json: Boolean indicating if the message is JSON.
    """
    try:
        # Create a unique filename with a timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        file_extension = 'json' if is_json else 'txt'
        filename = f'{prefix}_{timestamp}.{file_extension}'

        # Convert the message to a string if it's JSON
        if is_json:
            message = json.dumps(message)

        # Save the file to S3
        s3.put_object(Bucket=BUCKET_NAME, Key=filename, Body=message)
    except Exception as e:
        # Log any exceptions that occur
        print(f"An error occurred: {str(e)}")

@app.route('/', methods=['POST'])
def receive_sms():
    """
    Endpoint to receive SMS or JSON from a client, save it to S3, and respond accordingly.
    """
    if request.is_json:
        # Handle JSON data
        data = request.get_json()
        save_message_to_s3(data, "json_data", is_json=True)
        return jsonify({"status": "JSON data received and saved"})
    else:
        # Handle regular text data
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
        # Retrieve the list of files saved in S3 under the 'sms_' and 'json_data' prefixes
        sms_files = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix='sms_')['Contents']
        json_files = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix='json_data_')['Contents']
        all_files = sms_files + json_files

        # Sort and retrieve the most recent file
        recent_file = sorted(all_files, key=lambda x: x['LastModified'], reverse=True)[0]

        # Fetch the content of the most recent file
        file_content = s3.get_object(Bucket=BUCKET_NAME, Key=recent_file['Key'])['Body'].read().decode('utf-8')

        # Check if the file is JSON and format display accordingly
        if recent_file['Key'].endswith('.json'):
            file_content = json.loads(file_content)
            file_content = json.dumps(file_content, indent=4)

        # Construct HTML to display the message content
        html_content = f"""
        <!doctype html>
        <html>
            <head>
                <title>Last Message Received</title>
            </head>
            <body>
                <h1>Most Recent Message</h1>
                <pre>{file_content}</pre>
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
