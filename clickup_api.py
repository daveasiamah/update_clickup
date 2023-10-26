import json
import logging
import os

import httpx
import requests
from aiohttp import ClientSession
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class ClickUpClient:

    def __init__(self, token: str = None):
        if not token and not os.getenv("CLICKUP_API_KEY"):
            raise EnvironmentError(
                "The 'CLICKUP_API_KEY' environment variable is not set. Please set it before proceeding."
            )
        self.token = token or os.getenv("CLICKUP_API_KEY")

    async def send_request(self,
                           url,
                           method="GET",
                           params=None,
                           data=None,
                           headers=None):
        headers = headers or {
            "Authorization": self.token,
            "Content-Type": "application/json",
        }

        async with ClientSession() as session:
            if method == "GET":
                async with session.get(url, params=params,
                                       headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
            elif method == "POST":
                async with session.post(url,
                                        params=params,
                                        data=data,
                                        headers=headers) as response:
                    response.raise_for_status()
                return await response.json()


class ClickUpAccessor:

    def __init__(self):
        self.client = ClickUpClient()

    async def get_teams(self, team_id: str):
        url = "https://api.clickup.com/api/v2/group"
        query = {
            "team_id": team_id,
        }
        logger.info(f"Getting teams from ClickUp with team_id: {team_id}")
        response = await self.client.send_request(url, params=query)
        logger.info(
            f"Got {len(response['groups'])} teams from ClickUp with team_id: {team_id}"
        )
        return response

    async def get_task_status_history(self, task_id: str):
        url = "https://api.clickup.com/api/v2/task/" + task_id + "/time_in_status"
        response = await self.client.send_request(url)
        return response

    async def get_folders(self, space_id: str):
        print(f"Getting folders from ClickUp with space_id: {space_id}")
        url = "https://api.clickup.com/api/v2/space/" + space_id + "/folder"

        query = {"archived": "false"}
        res = requests.get(
            url,
            params=query,
            headers={"Authorization": os.getenv("CLICKUP_API_KEY")})

        return res.json()

        logger.info(f"Getting folders from ClickUp with space_id: {space_id}")
        # folders = await self.client.send_request(url, params=query)
        # logger.info(
        #     f"Got {len(folders['folders'])} folders from ClickUp with space_id: {space_id}"
        # )

        # return folders

    async def get_list(self, folder_id):
        url = "https://api.clickup.com/api/v2/folder/" + folder_id + "/list"

        query = {"archived": "false"}

        res = requests.get(
            url,
            params=query,
            headers={"Authorization": os.getenv("CLICKUP_API_KEY")})

        return res.json()

        # logger.info(f"Getting lists from ClickUp with folder_id: {folder_id}")
        # clickup_list = await self.client.send_request(url, params=query)
        # logger.info(
        #     f"Got {len(clickup_list['lists'])} lists from ClickUp with folder_id: {folder_id}"
        # )

        # return clickup_list

    async def get_all_space_tasks(self, space_id):
        """
        Get all tasks from a space
        :param space_id:
        :return:
        """
        list_ids = []
        tasks = []

        clickup_folders = await self.get_folders(space_id)
        if clickup_folders:
            folder_ids = [
                folder["id"] for folder in clickup_folders["folders"]
            ]
        else:
            return []

        print(f"Getting lists from Clickup with folder_ids: {folder_ids}")
        for folder_id in folder_ids:
            clickup_list = await self.get_list(folder_id)
            if clickup_list:
                list_ids.extend([list["id"] for list in clickup_list["lists"]])

        print(f"Getting tasks from ClickUp with list_ids: {list_ids}")
        for list_id in list_ids:
            tasks_list = await self.get_tasks(list_id)
            tasks.extend([task for task in tasks_list])

        return tasks

    async def get_tasks(self, list_id, include_subtasks=True):
        url = "https://api.clickup.com/api/v2/list/" + list_id + "/task"

        query = {
            "subtasks": include_subtasks,
        }

        res = requests.get(
            url,
            params=query,
            headers={"Authorization": os.getenv("CLICKUP_API_KEY")})

        # print(res.json())
        response = res.json()

        tasks = response["tasks"]

        filtered_tasks = self.filter_tasks(tasks)

        return filtered_tasks

    async def get_member_tasks(self, list_id, member_id, include_subtasks=True):
        url = "https://api.clickup.com/api/v2/list/" + list_id + "/task" + "?assignees[]=" + member_id + "&statuses[]=to%20do&statuses[]=in%20progress"

        query = {
            "subtasks": include_subtasks,
        }

        res = requests.get(
            url,
            params=query,
            headers={"Authorization": os.getenv("CLICKUP_API_KEY")})

        response = res.json()

        tasks = response["tasks"]

        filtered_tasks = self.filter_tasks(tasks)

        return filtered_tasks

    async def get_list_members(self, list_id):
        url = "https://api.clickup.com/api/v2/list/" + list_id + "/member"
        memebers_ids = []

        query = {"archived": "false"}

        res = requests.get(
            url,
            params=query,
            headers={"Authorization": os.getenv("CLICKUP_API_KEY")})

        response = res.json()

        print(f"Getting members from ClickUp in list with list_id: {list_id}")
        members = response["members"]

        memebers_ids.extend([member["id"] for member in members])

        return memebers_ids

    async def update_task(self, task_id: str, data):
        url = "https://api.clickup.com/api/v2/task/" + task_id

        payload = json.dumps(data)

        res = requests.put(
            url,
            data=payload,
            headers={
                "Authorization": os.getenv("CLICKUP_API_KEY"),
                "Content-Type": "application/json"
            }
        )

        response = res.json()

        return response

    @staticmethod
    def filter_tasks(tasks):
        filtered_tasks = []

        for task in tasks:
            filtered_task = {
                "id": task["id"],
                "name": task["name"],
                "description": task["description"],
                "date_created": task["date_created"],
                "assignees": [
                    {"id": assignee["id"], "username": assignee["username"]}
                    for assignee in task["assignees"]
                ],
                "due_date": task["due_date"] if task["due_date"] else "",
                "status": task["status"]["status"],
                "list": task["list"],
            }
            filtered_tasks.append(filtered_task)

        return filtered_tasks
