from fastapi import FastAPI
import requests
import uvicorn
import logging

from clickup_api import ClickUpAccessor
from slack_bot import send_slack_message

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI()

clickup_accessor = ClickUpAccessor()

space_id = 37307414


@app.get("/fetch-clickup-tasks/{space_id}")
async def fetch_clickup_tasks(space_id: str):
    tasks = await clickup_accessor.get_all_space_tasks(space_id, "")
    if tasks:
        # Send tasks to Slack bot
        channel = "#testing_clickup_update"  # Replace with the desired Slack channel
        tasks_message = "\n".join([f"Task: {task['name']}" for task in tasks])
        send_slack_message(channel, tasks_message)
        return {"message": "Tasks fetched from ClickUp and sent to Slack."}
    else:
        return {"message": "No tasks found in ClickUp space."}


fetch_clickup_tasks(37307414)


# Endpoint to receive Slack data
@app.post("/slack/events")
def receive_slack_data(data: dict):
    # Process Slack data here
    user = data.get("user")
    message = data.get("message")

    # Example processing: assuming the message contains task ID and new description
    task_id, new_description = parse_slack_message(message)

    # Extracted information, now pass it to ClickUp API functions
    clickup_response = update_clickup_task(task_id, new_description)

    return {"message": f"Task {task_id} updated: {clickup_response}"}


# Function to parse Slack message and extract task ID and new description
def parse_slack_message(message):
    # Logic to parse the message and extract task ID and new description
    # Example: message format "Update task <task_id> with description <description>"
    # Parse task_id and description from the message
    task_id = "TASK_ID"  # Extracted task ID
    new_description = "New task description"  # Extracted new description
    return task_id, new_description


# Function to update task description in ClickUp
def update_clickup_task(task_id, new_description):
    clickup_token = "YOUR_CLICKUP_API_TOKEN"
    url = f"https://api.clickup.com/api/v2/task/{task_id}"
    headers = {"Authorization": clickup_token, "Content-Type": "application/json"}
    data = {"description": new_description}
    response = requests.put(url, headers=headers, json=data)
    return response.json()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
