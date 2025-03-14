"""
# LLM VM Tool for OpenWebUI

Environment Variables Required:
------------------------------
COOLIFY_URL="https://your-coolify-instance.com"
COOLIFY_API_KEY="your-api-key"
COOLIFY_PROJECT_ID="your-project-id"
DOCKER_MEMORY_LIMIT="2048m"
DOCKER_CPU_LIMIT="1.0"
COMMAND_TIMEOUT="3600"
VM_PORT="8080"              # Port the VM API will listen on
HOST_PORT="8081"           # Port exposed on the host machine

Tool Description:
----------------
This tool provides LLMs with access to a sandboxed Ubuntu VM environment
managed through Coolify for executing commands and running code.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any
import docker
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LLM-VM-Tool")

@lru_cache(maxsize=1)
def get_config() -> Dict[str, Any]:
    """Get configuration from environment variables."""
    return {
        'coolify_url': os.getenv('COOLIFY_URL'),
        'coolify_api_key': os.getenv('COOLIFY_API_KEY'),
        'coolify_project_id': os.getenv('COOLIFY_PROJECT_ID'),
        'memory_limit': os.getenv('DOCKER_MEMORY_LIMIT', '2048m'),
        'cpu_limit': float(os.getenv('DOCKER_CPU_LIMIT', '1.0')),
        'timeout': int(os.getenv('COMMAND_TIMEOUT', '3600')),
        'vm_port': int(os.getenv('VM_PORT', '8080')),
        'host_port': int(os.getenv('HOST_PORT', '8081'))
    }

def tool_specification():
    """OpenWebUI tool specification"""
    return {
        "name": "ubuntu-vm",
        "description": "Provides access to a sandboxed Ubuntu VM for executing commands and running code",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["start", "stop", "execute", "write_file", "read_file", "install"],
                    "description": "Action to perform in the VM"
                },
                "command": {
                    "type": "string",
                    "description": "Command to execute (for 'execute' action)"
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to file (for file operations)"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (for 'write_file' action)"
                },
                "package": {
                    "type": "string",
                    "description": "Package name to install (for 'install' action)"
                }
            },
            "required": ["action"]
        }
    }

def handle_tool_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tool calls from OpenWebUI"""
    config = get_config()
    action = params.get("action")
    
    try:
        client = docker.from_env()
        container_name = f"llm-vm-{os.getenv('OPENWEBUI_SESSION_ID', 'default')}"
        vm_api_url = f"http://localhost:{config['host_port']}/api/v1"
        
        if action == "start":
            # Start container with port mapping
            container = client.containers.run(
                "llm-ubuntu-vm:latest",
                name=container_name,
                detach=True,
                mem_limit=config['memory_limit'],
                nano_cpus=int(float(config['cpu_limit']) * 1e9),
                ports={f"{config['vm_port']}/tcp": config['host_port']},
                labels={
                    "managed-by": "coolify",
                    "project": config['coolify_project_id']
                }
            )
            
            # Wait for API to be ready
            import time
            for _ in range(10):
                try:
                    response = requests.get(f"{vm_api_url}/health")
                    if response.status_code == 200:
                        break
                except:
                    time.sleep(1)
            
            return {"status": "success", "message": f"VM started: {container.id[:12]}"}
            
        elif action == "stop":
            # Send shutdown signal to API first
            try:
                requests.post(f"{vm_api_url}/shutdown")
            except:
                pass
            
            container = client.containers.get(container_name)
            container.stop()
            return {"status": "success", "message": "VM stopped"}
            
        elif action == "execute":
            command = params.get("command")
            if not command:
                return {"status": "error", "message": "No command provided"}
            
            # Send command to VM API
            response = requests.post(
                f"{vm_api_url}/execute",
                json={"command": command}
            )
            result = response.json()
            return {
                "status": "success",
                "output": result.get("output", ""),
                "exit_code": result.get("exit_code", -1)
            }
            
        elif action == "write_file":
            response = requests.post(
                f"{vm_api_url}/write_file",
                json={
                    "path": params.get("file_path"),
                    "content": params.get("content")
                }
            )
            return response.json()
            
        elif action == "read_file":
            response = requests.get(
                f"{vm_api_url}/read_file",
                params={"path": params.get("file_path")}
            )
            return response.json()
            
        elif action == "install":
            response = requests.post(
                f"{vm_api_url}/install",
                json={"package": params.get("package")}
            )
            return response.json()
            
    except Exception as e:
        logger.error(f"Tool error: {str(e)}")
        return {"status": "error", "message": str(e)} 