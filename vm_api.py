"""
VM API Server - Handles communication between OpenWebUI and the VM
"""

from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
import subprocess
import os

app = FastAPI()

class CommandRequest(BaseModel):
    command: str

class FileRequest(BaseModel):
    path: str
    content: str

class PackageRequest(BaseModel):
    package: str

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/execute")
async def execute_command(request: CommandRequest):
    try:
        process = subprocess.run(
            request.command,
            shell=True,
            capture_output=True,
            text=True,
            cwd="/workspace"
        )
        return {
            "output": process.stdout + process.stderr,
            "exit_code": process.returncode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/write_file")
async def write_file(request: FileRequest):
    try:
        path = os.path.join("/workspace", request.path.lstrip("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(request.content)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/read_file")
async def read_file(path: str):
    try:
        path = os.path.join("/workspace", path.lstrip("/"))
        with open(path, "r") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/install")
async def install_package(request: PackageRequest):
    try:
        process = subprocess.run(
            f"pip install --user {request.package}",
            shell=True,
            capture_output=True,
            text=True
        )
        return {
            "output": process.stdout + process.stderr,
            "exit_code": process.returncode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/shutdown")
async def shutdown():
    return {"status": "shutting down"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("VM_PORT", "8080"))) 