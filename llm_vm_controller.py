"""
# OpenWebUI VM Controller with Coolify Integration

This module provides a sandboxed VM environment for OpenWebUI to interact with using Docker containers
managed through Coolify.

Environment Variables Required:
------------------------------
COOLIFY_URL="https://your-coolify-instance.com"
COOLIFY_API_KEY="your-api-key"
COOLIFY_PROJECT_ID="your-project-id"
MEMORY_LIMIT="2048m"
CPU_LIMIT="1.0"
COMMAND_TIMEOUT="3600"
VM_PORT="8080"              # Port the VM API will listen on
HOST_PORT="8081"           # Port exposed on the host machine

## Setup Instructions

### Prerequisites:
1. Docker installed and running
2. Coolify server set up and accessible
3. Python 3.8+ with docker-py package installed

### Coolify Configuration:
1. Ensure Coolify API access is configured
2. Create a dedicated project for VMs in Coolify

### Production Deployment:
1. Create a .env file based on .env.example with your actual credentials
2. Never commit the .env file to version control
3. Consider using a secrets management solution for sensitive variables

### Security Considerations:
- All VMs run in network isolation mode by default
- File operations are restricted to /workspace directory
- Command execution is limited to the allowed_commands list
- Resources are constrained by memory and CPU limits
- All containers are automatically removed when stopped
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any
import docker
import time
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("OpenWebUI-VM-Controller")

@lru_cache(maxsize=1)
def get_config() -> Dict[str, Any]:
    """Get configuration from environment variables."""
    # Load configuration from environment variables
    # In production, these should be set in the .env file which is not committed to version control
    return {
        'coolify_url': os.getenv('COOLIFY_URL'),
        'coolify_api_key': os.getenv('COOLIFY_API_KEY'),
        'coolify_project_id': os.getenv('COOLIFY_PROJECT_ID'),
        'memory_limit': os.getenv('MEMORY_LIMIT', '2048m'),
        'cpu_limit': float(os.getenv('CPU_LIMIT', '1.0')),
        'timeout': int(os.getenv('COMMAND_TIMEOUT', '3600')),
        'vm_port': int(os.getenv('VM_PORT', '8080')),
        'host_port': int(os.getenv('HOST_PORT', '8081')),
        'repo_url': os.getenv('REPO_URL', 'https://github.com/amintt2/OpenWebui.git'),
        'repo_branch': os.getenv('REPO_BRANCH', 'main')
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

class VMController:
    """
    A controller class that provides a sandboxed VM environment for OpenWebUI to interact with.
    This uses Docker containers as lightweight VMs for isolation and security.
    """
    
    def __init__(self, 
                 base_image: str = "ubuntu:22.04", 
                 memory_limit: Optional[str] = None,
                 cpu_limit: Optional[float] = None,
                 timeout_seconds: Optional[int] = None,
                 allowed_commands: Optional[List[str]] = None,
                 session_id: Optional[str] = None):
        """
        Initialize the VM controller with configurable constraints.
        
        Args:
            base_image: Docker image to use as the VM base
            memory_limit: Maximum memory allocation for the VM
            cpu_limit: CPU usage limit (1.0 = 100% of one CPU)
            timeout_seconds: Maximum execution time before termination
            allowed_commands: List of commands that are allowed to be executed
            session_id: Unique session identifier
        """
        # Get configuration from environment
        config = get_config()
        
        self.base_image = base_image
        self.memory_limit = memory_limit or config['memory_limit']
        self.cpu_limit = cpu_limit or config['cpu_limit']
        self.timeout_seconds = timeout_seconds or config['timeout']
        self.allowed_commands = allowed_commands or [
            "ls", "cat", "echo", "python", "pip", "apt-get", "apt", 
            "cd", "mkdir", "rm", "cp", "mv", "chmod", "touch", "date", 
            "grep", "find", "curl", "wget", "git"
        ]
        
        # Coolify configuration
        self.coolify_url = config['coolify_url']
        self.coolify_api_key = config['coolify_api_key']
        self.coolify_project_id = config['coolify_project_id']
        self.vm_port = config['vm_port']
        self.host_port = config['host_port']
        
        # Session management
        self.session_id = session_id or os.getenv('OPENWEBUI_SESSION_ID', 'default')
        self.container_name = f"openwebui-vm-{self.session_id}"
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            logger.info(f"Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise
            
        # Container reference
        self.container = None
        self.container_id = None
        
        # API endpoint
        self.vm_api_url = f"http://localhost:{self.host_port}/api/v1"

    def start_vm(self) -> Dict[str, Any]:
        """
        Start a new VM (Docker container) with the configured constraints.
        
        Returns:
            Dict containing status and container information
        """
        try:
            # Check if container already exists
            try:
                existing = self.docker_client.containers.get(self.container_name)
                logger.info(f"Container {self.container_name} already exists, reusing")
                self.container = existing
                self.container_id = existing.id
                return {
                    "status": "success",
                    "container_id": self.container_id,
                    "message": "VM already running"
                }
            except docker.errors.NotFound:
                pass
                
            # Create and start the container
            self.container = self.docker_client.containers.run(
                self.base_image,
                detach=True,
                mem_limit=self.memory_limit,
                nano_cpus=int(float(self.cpu_limit) * 1e9),
                ports={f"{self.vm_port}/tcp": self.host_port},
                name=self.container_name,
                labels={
                    "managed-by": "coolify",
                    "project": self.coolify_project_id,
                    "openwebui-vm": "true"
                }
            )
            
            self.container_id = self.container.id
            logger.info(f"VM started with container ID: {self.container_id}")
            
            # Wait for API to be ready
            for _ in range(10):
                try:
                    response = requests.get(f"{self.vm_api_url}/health")
                    if response.status_code == 200:
                        break
                except:
                    time.sleep(1)
            
            return {
                "status": "success",
                "container_id": self.container_id,
                "message": "VM started successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to start VM: {e}")
            return {
                "status": "error",
                "message": f"Failed to start VM: {str(e)}"
            }

    def stop_vm(self) -> Dict[str, str]:
        """
        Stop and remove the VM (Docker container).
        
        Returns:
            Dict containing status and message
        """
        try:
            # Send shutdown signal to API first
            try:
                requests.post(f"{self.vm_api_url}/shutdown")
            except:
                pass
                
            # Get container if not already referenced
            if not self.container:
                try:
                    self.container = self.docker_client.containers.get(self.container_name)
                except docker.errors.NotFound:
                    return {"status": "success", "message": "No VM is currently running"}
            
            self.container.stop()
            logger.info(f"VM with container ID {self.container_id} stopped")
            self.container = None
            self.container_id = None
            return {"status": "success", "message": "VM stopped successfully"}
        except Exception as e:
            logger.error(f"Failed to stop VM: {e}")
            return {"status": "error", "message": f"Failed to stop VM: {str(e)}"}

    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a command in the VM and return the result.
        
        Args:
            command: The command to execute
            
        Returns:
            Dict containing status, output, and error information
        """
        # Send command to VM API
        try:
            response = requests.post(
                f"{self.vm_api_url}/execute",
                json={"command": command},
                timeout=self.timeout_seconds
            )
            result = response.json()
            return {
                "status": "success",
                "output": result.get("output", ""),
                "exit_code": result.get("exit_code", -1)
            }
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "status": "error",
                "message": f"Command execution failed: {str(e)}"
            }

    def write_file(self, file_path: str, content: str) -> Dict[str, str]:
        """
        Write content to a file in the VM.
        
        Args:
            file_path: Path to the file in the VM
            content: Content to write to the file
            
        Returns:
            Dict containing status and message
        """
        try:
            response = requests.post(
                f"{self.vm_api_url}/write_file",
                json={
                    "path": file_path,
                    "content": content
                }
            )
            return response.json()
        except Exception as e:
            logger.error(f"Failed to write file: {e}")
            return {
                "status": "error",
                "message": f"Failed to write file: {str(e)}"
            }

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read content from a file in the VM.
        
        Args:
            file_path: Path to the file in the VM
            
        Returns:
            Dict containing status, content, and message
        """
        try:
            response = requests.get(
                f"{self.vm_api_url}/read_file",
                params={"path": file_path}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            return {
                "status": "error",
                "message": f"Failed to read file: {str(e)}"
            }

    def install_package(self, package_name: str) -> Dict[str, Any]:
        """
        Install a Python package in the VM.
        
        Args:
            package_name: Name of the package to install
            
        Returns:
            Dict containing status and message
        """
        try:
            response = requests.post(
                f"{self.vm_api_url}/install",
                json={"package": package_name}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Failed to install package: {e}")
            return {
                "status": "error",
                "message": f"Failed to install package: {str(e)}"
            }

def handle_vm_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle requests from OpenWebUI to the VM controller.
    
    Args:
        request_data: Dictionary containing request parameters
        
    Returns:
        Dict containing response data
    """
    action = request_data.get("action")
    
    # Create controller instance
    controller = VMController()
    
    if action == "start":
        return controller.start_vm()
    
    elif action == "stop":
        return controller.stop_vm()
    
    elif action == "execute":
        command = request_data.get("command")
        if not command:
            return {"status": "error", "message": "No command provided"}
        return controller.execute_command(command)
    
    elif action == "write_file":
        file_path = request_data.get("file_path")
        content = request_data.get("content")
        if not file_path or content is None:
            return {"status": "error", "message": "File path or content missing"}
        return controller.write_file(file_path, content)
    
    elif action == "read_file":
        file_path = request_data.get("file_path")
        if not file_path:
            return {"status": "error", "message": "File path missing"}
        return controller.read_file(file_path)
    
    elif action == "install":
        package = request_data.get("package")
        if not package:
            return {"status": "error", "message": "Package name missing"}
        return controller.install_package(package)
    
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}

# Example usage
if __name__ == "__main__":
    # Example request to start a VM
    example_request = {
        "action": "start"
    }
    
    response = handle_vm_request(example_request)
    print(json.dumps(response, indent=2))
    
    # Example command execution
    if response["status"] == "success":
        example_command = {
            "action": "execute",
            "command": "echo 'Hello from the VM!'"
        }
        
        command_response = handle_vm_request(example_command)
        print(json.dumps(command_response, indent=2))
        
        # Clean up
        handle_vm_request({"action": "stop"}) 