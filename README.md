# SMS Receiver and Display

## Overview

This project sets up a simple web server to receive SMS messages from Twilio, store them in an Amazon S3 bucket, and display the most recent message via a web page. It's perfect for logging and viewing messages from a Twilio phone number.

## How It Works

- The server receives an SMS message from Twilio, sent to a specific route.
- Upon receipt, the server saves the content of the SMS message to an S3 bucket, creating a new file with a timestamp.
- There is also a route available to view the most recent message by fetching it from the S3 bucket and displaying it on a web page.

## Prerequisites

- Python 3.x
- Flask
- Boto3 (for interacting with AWS S3)
- A Twilio account and a Twilio phone number that can receive SMS
- An AWS account and an S3 bucket for storing messages

## Setup

1. Clone the repository to your local machine or server.
2. Install the required Python packages using `pip install -r requirements.txt`.
3. Set up an environment variable `DB_NAME` containing your S3 bucket name.
4. Update the Twilio phone number's webhook URL to the route on your server that's set up to receive SMS messages.
5. Run the Flask application.
6. Send an SMS to your Twilio number and then visit the web page to view the message.

## Usage

To start the server, run:


python webhook.py


