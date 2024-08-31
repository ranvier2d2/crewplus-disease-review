from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from uuid import uuid4
import sqlite3
import json
from disease_review.crew import DiseaseReviewCrew
from threading import local
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load the .env file
load_dotenv()

app = FastAPI()
security = HTTPBearer()

# Thread-local storage
thread_local = local()

def get_db():
    if not hasattr(thread_local, "conn"):
        thread_local.conn = sqlite3.connect('tasks.db')
        thread_local.c = thread_local.conn.cursor()
        thread_local.c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id TEXT PRIMARY KEY, status TEXT, result TEXT)''')
        thread_local.conn.commit()
    return thread_local.conn, thread_local.c

class Input(BaseModel):
    topic: str

class KickoffRequest(BaseModel):
    inputs: Input
    taskWebhookUrl: str = ""
    stepWebhookUrl: str = ""
    crewWebhookUrl: str = ""

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "6ce0a076d321":
        logger.warning(f"Invalid token attempt: {credentials.credentials}")
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials

@app.get("/inputs")
async def get_inputs(token: HTTPAuthorizationCredentials = Depends(verify_token)):
    logger.info("Inputs endpoint accessed")
    return {"inputs": ["topic"]}

@app.post("/kickoff")
async def kickoff(request: KickoffRequest, background_tasks: BackgroundTasks, token: HTTPAuthorizationCredentials = Depends(verify_token)):
    task_id = str(uuid4())
    logger.info(f"Kickoff requested for topic: {request.inputs.topic}. Task ID: {task_id}")
    background_tasks.add_task(run_crew, task_id, request.inputs.topic)
    return {"task_id": task_id}

@app.get("/status/{task_id}")
async def get_status(task_id: str, token: HTTPAuthorizationCredentials = Depends(verify_token)):
    logger.info(f"Status requested for task ID: {task_id}")
    conn, c = get_db()
    c.execute("SELECT status, result FROM tasks WHERE id=?", (task_id,))
    row = c.fetchone()
    if row is None:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    status, result = row
    logger.info(f"Status for task {task_id}: {status}")
    return {"state": status, "result": result}

def process_crew_output(result, task_id: str, topic: str, file_content: str):
    return {
        "state": "SUCCESS",
        "task_id": task_id,
        "topic": topic,
        "result": file_content,
    }

def run_crew(task_id: str, topic: str):
    logger.info(f"Starting crew execution for task {task_id}, topic: {topic}")
    conn, c = get_db()
    c.execute("INSERT INTO tasks (id, status, result) VALUES (?, ?, ?)", (task_id, "RUNNING", None))
    conn.commit()
    
    try:
        crew = DiseaseReviewCrew()
        logger.info(f"Crew initialized for task {task_id}")
        result = crew.crew().kickoff(inputs={"topic": topic})
        logger.info(f"Crew execution completed for task {task_id}")
        
        # Read the output file
        output_file_path = 'final_report.md'
        if os.path.exists(output_file_path):
            with open(output_file_path, 'r') as file:
                file_content = file.read()
        else:
            file_content = "Output file not found"
        
        processed_result = process_crew_output(result, task_id, topic, file_content)
        
        c.execute("UPDATE tasks SET status=?, result=? WHERE id=?", ("SUCCESS", json.dumps(processed_result), task_id))
        conn.commit()
        logger.info(f"Task {task_id} completed successfully")
    except Exception as e:
        logger.error(f"Error in task {task_id}: {str(e)}", exc_info=True)
        error_result = {
            "state": "FAILED",
            "task_id": task_id,
            "topic": topic,
            "result": str(e)
        }
        c.execute("UPDATE tasks SET status=?, result=? WHERE id=?", ("FAILED", json.dumps(error_result), task_id))
        conn.commit()

def start():
    logger.info("Starting FastAPI application")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Log the OPENAI_API_KEY to check if it's loaded correctly (mask most of it for security)
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    masked_key = f"{api_key[:4]}...{api_key[-4:]}"
    logger.info(f"OPENAI_API_KEY loaded: {masked_key}")
else:
    logger.warning("OPENAI_API_KEY not found in environment variables")