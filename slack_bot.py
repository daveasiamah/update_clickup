import os
import slack_sdk
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

# Slack Bot Setup
slack_token = os.getenv("SLACK_BOT_TOKEN")
client = slack_sdk.WebClient(token=slack_token)


# Function to send a message to Slack channel
def send_slack_message(channel, message):
    try:
        response = client.chat_postMessage(channel=channel, text=message)
        return response
    except SlackApiError as e:
        print(f"Error sending message to Slack: {e.response['error']}")


# Example usage
# send_slack_message("#testing_clickup_updates", "Hello from Slack Bot!")
