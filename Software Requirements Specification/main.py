from fastapi import FastAPI
from pydantic import BaseModel

import database
from agents import pipeline

app = FastAPI(title="Requirement Engineering Automation API")

database.init_db()


class RequirementInput(BaseModel):
    project_name: str
    raw_text: str


@app.post("/process")
def process_requirements(data: RequirementInput):
    project_id = database.create_project(data.project_name)

    result = pipeline.invoke({
        "raw_text": data.raw_text,
        "requirements": [],
        "classified": [],
        "document": ""
    })

    database.save_requirements(project_id, result["classified"])
    database.save_document(project_id, result["document"])

    return {
        "project_id": project_id,
        "requirements": result["classified"],
        "document": result["document"]
    }


@app.get("/projects")
def list_projects():
    return database.get_all_projects()


@app.get("/projects/{project_id}/requirements")
def project_requirements(project_id: int):
    return database.get_project_requirements(project_id)


@app.get("/projects/{project_id}/documents")
def project_documents(project_id: int):
    return database.get_project_documents(project_id)
