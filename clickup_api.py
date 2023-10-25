import requests

# ClickUp API credentials
clickup_token = "pk_49396220_LS5FMHDLTVF3S6AEGQNLNZTV2NKEBODL"

import json
import logging
import os

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)
token = clickup_token


class ClickUpClient:
    def __init__(self, token: str = None):
        async def send_request(
            self, url, method="GET", params=None, data=None, headers=None
        ):
            headers = headers or {
                "Authorization": token,
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, params=params, headers=headers)
                elif method == "POST":
                    response = await client.post(
                        url, params=params, data=data, headers=headers
                    )
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code, detail=response.text
                    )
                return response.json()


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

    async def get_folders(self, space_id):
        url = "https://api.clickup.com/api/v2/space/" + space_id + "/folder"

        query = {"archived": "false"}
        logger.info(f"Getting folders from ClickUp with space_id: {space_id}")
        folders = await self.client.send_request(url, params=query)
        logger.info(
            f"Got {len(folders['folders'])} folders from ClickUp with space_id: {space_id}"
        )

        return folders

    async def get_list(self, folder_id):
        url = "https://api.clickup.com/api/v2/folder/" + folder_id + "/list"

        query = {"archived": "false"}

        logger.info(f"Getting lists from ClickUp with folder_id: {folder_id}")
        clickup_list = await self.client.send_request(url, params=query)
        logger.info(
            f"Got {len(clickup_list['lists'])} lists from ClickUp with folder_id: {folder_id}"
        )

        return clickup_list

    async def get_all_space_tasks(self, space_id, collection_name):
        """
        Get all tasks from a space and insert them in ChromaDB
        :param space_id:
        :param collection_name:
        :return:
        """
        list_ids = []
        task_ids = []

        clickup_folders = await self.get_folders(space_id)
        if clickup_folders.get("folders"):
            folder_ids = [folder["id"] for folder in clickup_folders["folders"]]
        else:
            return []

        for folder_id in folder_ids:
            clickup_list = await self.get_list(folder_id)
            if clickup_list.get("lists"):
                list_ids.extend([list["id"] for list in clickup_list["lists"]])

        logger.info(f"Getting tasks from ClickUp with list_ids: {list_ids}")
        for list_id in list_ids:
            res = await self.get_tasks(list_id, collection_name)
            task_ids.extend([task["id"] for task in res])

        return task_ids

    async def get_tasks(self, list_id, collection_name, include_subtasks=True):
        url = "https://api.clickup.com/api/v2/list/" + list_id + "/task"

        query = {
            "subtasks": include_subtasks,
        }

        logger.info(f"Getting tasks from ClickUp with list_id: {list_id}")
        tasks = await self.client.send_request(url, params=query)
        if tasks.get("tasks"):
            if not tasks["tasks"]:
                logger.info(f"Got 0 tasks from ClickUp with list_id: {list_id}")
                return []
            logger.info(
                f"Got {len(tasks['tasks'])} tasks from ClickUp with list_id: {list_id}"
            )
            tasks = tasks["tasks"]
        # Get each task's status history
        else:
            logger.info(f"Got 0 tasks from ClickUp with list_id: {list_id}")
            return []
        try:
            for task in tasks:
                task_status_history = await self.get_task_status_history(task["id"])
                filtered_status_history = {
                    "current_status": {
                        "status": task_status_history["current_status"]["status"],
                        "total_time": task_status_history["current_status"][
                            "total_time"
                        ],
                    },
                    "status_history": [
                        {"status": entry["status"], "total_time": entry["total_time"]}
                        for entry in task_status_history["status_history"]
                    ],
                }
                task["status_history"] = filtered_status_history
        except HTTPException as e:
            logger.error(e)
            raise HTTPException(
                status_code=500, detail="Failed to get task status history"
            )

        filtered_tasks = self.filter_tasks(tasks)
        filtered_tasks_strings = [json.dumps(task) for task in filtered_tasks]

        collection_metadata = {
            "date_created": [task["date_created"] for task in filtered_tasks],
            "sprint": [task["list"]["name"] for task in tasks],
            "status_history": [json.dumps(task["status_history"]) for task in tasks],
        }

        collection_metadata_array = [
            {"date_created": date, "sprint": sprint, "status_history": history}
            for date, sprint, history in zip(
                collection_metadata["date_created"],
                collection_metadata["sprint"],
                collection_metadata["status_history"],
            )
        ]

        logger.info(
            f"Upserting {len(filtered_tasks_strings)} "
            f"tasks to ChromaDB with collection_name: {collection_name}"
        )
        self._get_collection(collection_name).upsert(
            documents=filtered_tasks_strings,
            metadatas=collection_metadata_array,
            ids=[task_id for task_id in [task["id"] for task in filtered_tasks]],
        )
        logger.info(
            f"Upserted {len(filtered_tasks_strings)} tasks to ChromaDB with collection_name: {collection_name}"
        )

        return filtered_tasks

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
            }
            filtered_tasks.append(filtered_task)

        return filtered_tasks
