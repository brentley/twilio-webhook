from flask import Flask, request, jsonify, render_template_string
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

def save_to_s3(data, filename):
    """
    Saves data to an S3 bucket with the given filename.

    :param data: The data to be saved.
    :param filename: The filename for the S3 object.
    """
    try:
        # Convert the data to a string if it's not
        if not isinstance(data, str):
            data = json.dumps(data)

        # Save the data to S3
        s3.put_object(Bucket=BUCKET_NAME, Key=filename, Body=data)
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def save_json_and_content(json_data, prefix):
    """
    Saves the JSON data and the 'content' value from it to the S3 bucket.

    :param json_data: The JSON data received.
    :param prefix: The prefix for the S3 file naming.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    json_filename = f'{prefix}_{timestamp}.json'
    text_filename = f'{prefix}_content_{timestamp}.txt'

    # Save the entire JSON
    save_to_s3(json_data, json_filename)

    # Extract the 'content' value and save it as a text file
    content = json_data.get('content', '')
    save_to_s3(content, text_filename)

@app.route('/', methods=['POST'])
def receive_data():
    """
    Endpoint to receive JSON data, save it, and also save its 'content' field separately.
    """
    if request.is_json:
        data = request.get_json()
        save_json_and_content(data, "json_data")
        return jsonify({"status": "JSON data and content saved"})
    else:
        return jsonify({"status": "Invalid request, expecting JSON"})

@app.route('/', methods=['GET'])
def display_last_message():
    """
    Endpoint to fetch and display the most recent message saved in S3.
    """
    try:
        # Retrieve the list of files saved in S3
        files = s3.list_objects_v2(Bucket=BUCKET_NAME)['Contents']

        # Sort and retrieve the most recent file
        recent_file = sorted(files, key=lambda x: x['LastModified'], reverse=True)[0]

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
        return str(e)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
