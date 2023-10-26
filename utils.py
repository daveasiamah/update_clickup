# https://api.clickup.com/api/v2/team/team_id/user/user_id
# app.add_event_handler("startup", fetch_clickup_tasks)

# # Endpoint to receive Slack data
# @app.post("/slack/events")
# def receive_slack_data(data: dict):
#     # Process Slack data here
#     user = data.get("user")
#     message = data.get("message")

#     # Example processing: assuming the message contains task ID and new description
#     task_id, new_description = parse_slack_message(message)

#     # Extracted information, now pass it to ClickUp API functions
#     clickup_response = update_clickup_task(task_id, new_description)

#     return {"message": f"Task {task_id} updated: {clickup_response}"}

# # Function to parse Slack message and extract task ID and new description
# def parse_slack_message(message):
#     # Logic to parse the message and extract task ID and new description
#     # Example: message format "Update task <task_id> with description <description>"
#     # Parse task_id and description from the message
#     task_id = "TASK_ID"  # Extracted task ID
#     new_description = "New task description"  # Extracted new description
#     return task_id, new_description

# # Function to update task description in ClickUp
# def update_clickup_task(task_id, new_description):
#     clickup_token = "YOUR_CLICKUP_API_TOKEN"
#     url = f"https://api.clickup.com/api/v2/task/{task_id}"
#     headers = {"Authorization": clickup_token, "Content-Type": "application/json"}
#     data = {"description": new_description}
#     response = requests.put(url, headers=headers, json=data)
#     return response.json()
