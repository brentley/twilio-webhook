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
        # Convert the data to a string if it's not already
        if not isinstance(data, str):
            data = json.dumps(data)

        # Save the data to S3
        s3.put_object(Bucket=BUCKET_NAME, Key=filename, Body=data)
    except Exception as e:
        # Log any exceptions that occur
        print(f"An error occurred: {str(e)}")

def save_json_and_content(json_data, prefix):
    """
    Saves the entire JSON data, the 'content' value, and the content in a sender-named file.
    :param json_data: The JSON data received.
    :param prefix: The prefix for the S3 file naming.
    """
    # Generate a timestamp for the filenames
    timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

    # Filename for the entire JSON data
    json_filename = f'{prefix}_{timestamp}.json'
    # Save the entire JSON
    save_to_s3(json_data, json_filename)

    # Extract the 'content' value and save it as a separate text file, if available
    content = json_data.get('content')
    if content is not None:
        text_filename = f'{prefix}_content_{timestamp}.txt'
        save_to_s3(content, text_filename)

        # Save the content in a file named after the sender
        sender_name = json_data.get('sender', 'unknown_sender')
        sender_filename = f'{sender_name}_content.txt'
        save_to_s3(content, sender_filename)

@app.route('/', methods=['POST'])
def receive_data():
    """
    Endpoint to receive JSON data via POST requests.
    Saves the data, the 'content' field, and the content in a sender-named file.
    """
    if request.is_json:
        # Extract JSON data from the request
        data = request.get_json()

        # Save the received JSON data and its content
        save_json_and_content(data, "json_data")

        # Respond with a success message
        return jsonify({"status": "JSON data and content saved"})
    else:
        # Respond with an error message for non-JSON requests
        return jsonify({"status": "Invalid request, expecting JSON"})

@app.route('/', methods=['GET'])
def display_last_message():
    """
    Endpoint to fetch and display the most recent 'content' file,
    or if not available, the most recent JSON formatted file.
    """
    try:
        # Retrieve the list of files saved in S3
        files = s3.list_objects_v2(Bucket=BUCKET_NAME)['Contents']

        # Sort files by last modified date
        sorted_files = sorted(files, key=lambda x: x['LastModified'], reverse=True)

        # Try to find the most recent 'content' file
        content_file = next((f for f in sorted_files if f['Key'].startswith('json_data_content_')), None)

        if content_file:
            # Fetch and display the content file
            file_content = s3.get_object(Bucket=BUCKET_NAME, Key=content_file['Key'])['Body'].read().decode('utf-8')
        else:
            # If no content file, find the most recent JSON file
            json_file = next((f for f in sorted_files if f['Key'].startswith('json_data_') and f['Key'].endswith('.json')), None)
            if json_file:
                # Fetch and display the JSON file
                file_content = s3.get_object(Bucket=BUCKET_NAME, Key=json_file['Key'])['Body'].read().decode('utf-8')
                file_content = json.dumps(json.loads(file_content), indent=4)
            else:
                return "No content or JSON files available."

        # Construct HTML to display the file content
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
        # Log and return any exceptions that occur
        return str(e)

if __name__ == '__main__':
    # Run the Flask app on port 5001
    app.run(debug=True, host='0.0.0.0', port=5001)

