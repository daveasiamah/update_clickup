import uvicorn
from fastapi import FastAPI

from clickup_api import ClickUpAccessor
from slack_bot import send_slack_message

app = FastAPI()

clickup_accessor = ClickUpAccessor()

space_id = "90080537790"
list_id = "900802489450"


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/tasks/open/{member_id}")
async def fetch_member_open_tasks(member_id: str):
    tasks = await clickup_accessor.get_member_tasks(list_id, member_id)

    return {
        "message": "Member open tasks fetched from ClickUp",
        "tasks": tasks
    }


@app.get("/fetch-assigned-tasks")
async def fetch_assigned_tasks():
    tasks = await clickup_accessor.get_tasks(list_id)
    list_id = tasks[0]["list"]["id"]

    list_members = await clickup_accessor.get_list_members(list_id)
    print(f"DEBUGPRINT[1]: main.py:25: list_members={list_members}")

    tasks_with_assignees = []

    if tasks:
        for task in tasks:
            if task["assignees"] != []:
                tasks_with_assignees.append(task)

        print(
            f"DEBUGPRINT[1]: main.py:38: tasks_with_assignees={tasks_with_assignees}"
        )

        return {
            "message": "Tasks fetched from ClickUp and sent to Slack.",
            "tasks_with_assignees": tasks_with_assignees,
        }


@app.get("/fetch-clickup-tasks")
async def fetch_clickup_tasks():
    list_id = "900802489450"
    # tasks = await clickup_accessor.get_all_space_tasks(space_id)
    tasks = await clickup_accessor.get_tasks(list_id)
    list_id = tasks[0]["list"]["id"]

    list_members = await clickup_accessor.get_list_members(list_id)
    print(f"DEBUGPRINT[1]: main.py:25: list_members={list_members}")

    pending_tasks = []
    members_with_tasks = []
    members_without_tasks = []

    if tasks:
        for task in tasks:
            if task["assignees"] != []:
                members_with_tasks.extend([
                    assignee["id"] for assignee in task["assignees"]
                    if assignee["id"] not in members_with_tasks
                ])

            if task["assignees"] == []:
                pending_tasks.append(task)

        print(f"DEBUGPRINT[1]: main.py:38: pending_tasks={pending_tasks}")

        print(
            f"DEBUGPRINT[2]: main.py:38: members_with_tasks={members_with_tasks}"
        )

        members_without_tasks = [
            member for member in list_members
            if member not in members_with_tasks
        ]

        print(
            f"DEBUGPRINT[3]: main.py:45: members_without_tasks={members_without_tasks}"
        )

        # task_id = pending_tasks[0]["id"]
        # print(f"DEBUGPRINT[4]: main.py:45: task_id={task_id}")
        # updated_task = await clickup_accessor.update_task(
        #     task_id,
        #     {
        #         "assignees": {
        #             "add": [
        #                members_without_tasks[0]
        #             ]
        #         }
        #     }
        # )
        #
        # print(
        #     f"DEBUGPRINT[4]: main.py:45: updated_task={updated_task}"
        # )

        # Send tasks to Slack bot
        # tasks_message = "\n".join([
        #     f"Task: {task['name']}\n"
        #     f"Task Status: {task['status']}\n"
        #     f"Task Assignees: {task['assignees']}\n\n"
        #     for task in pending_tasks
        # ])
        # print(tasks_message)
        # channel = "#testing_clickup_update"  # Replace with the desired Slack channel
        # send_slack_message(channel, tasks_message)
        return {"message": "Tasks fetched from ClickUp and sent to Slack."}
    else:
        return {"message": "No tasks found in ClickUp space."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
