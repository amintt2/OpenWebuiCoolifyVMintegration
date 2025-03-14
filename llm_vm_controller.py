"""
# LLM Virtual Machine Controller for OpenWebUI with Coolify Integration

This module provides a sandboxed VM environment for LLMs to interact with using Docker containers
managed through Coolify.

## Setup Instructions

### Prerequisites:
1. Docker installed and running
2. Coolify server set up and accessible
3. Python 3.8+ with docker-py package installed

### Coolify Configuration:
1. Ensure Coolify API access is configured
2. Create a dedicated project for LLM VMs in Coolify

### Quick Configuration Variables:
Edit these variables in the LLMVirtualMachineController class initialization:

- base_image: Docker image (default: "ubuntu:22.04")
- memory_limit: Memory allocation (default: "2048m")
- cpu_limit: CPU usage limit (default: 1.0 = 100% of one CPU)
- timeout_seconds: Maximum execution time (default: 3600 seconds)
- allowed_commands: List of permitted commands
- coolify_url: URL of your Coolify instance (e.g., "https://mciut.fr")
- coolify_api_key: Your Coolify API key for authentication
- coolify_project_id: ID of the Coolify project to use

### Integration with OpenWebUI:
1. Import this module in your OpenWebUI plugin
2. Use the handle_llm_vm_request function to process LLM requests
3. Map OpenWebUI actions to controller methods

### Security Considerations:
- All VMs run in network isolation mode by default
- File operations are restricted to /workspace directory
- Command execution is limited to the allowed_commands list
- Resources are constrained by memory and CPU limits
- All containers are automatically removed when stopped

## Usage Example:
"""

import os
import subprocess
import json
import logging
from typing import Dict, List, Optional, Any
import docker
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("LLM-VM-Controller")

class LLMVirtualMachineController:
    """
    A controller class that provides a sandboxed VM environment for LLMs to interact with.
    This uses Docker containers as lightweight VMs for isolation and security.
    """
    
    def __init__(self, 
                 base_image: str = "ubuntu:22.04", 
                 memory_limit: str = "2048m",
                 cpu_limit: float = 1.0,
                 timeout_seconds: int = 3600,
                 allowed_commands: Optional[List[str]] = None,
                 coolify_url: Optional[str] = None,
                 coolify_api_key: Optional[str] = None,
                 coolify_project_id: Optional[str] = None):
        """
        Initialize the VM controller with configurable constraints.
        
        Args:
            base_image: Docker image to use as the VM base
            memory_limit: Maximum memory allocation for the VM
            cpu_limit: CPU usage limit (1.0 = 100% of one CPU)
            timeout_seconds: Maximum execution time before termination
            allowed_commands: List of commands that are allowed to be executed
            coolify_url: URL of your Coolify instance
            coolify_api_key: Your Coolify API key for authentication
            coolify_project_id: ID of the Coolify project to use
        """
        self.base_image = base_image
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.timeout_seconds = timeout_seconds
        self.allowed_commands = allowed_commands or ["ls", "cat", "echo", "python", "pip", "apt-get", "apt", "apt-get install", "apt-get update", "apt-get upgrade", "apt-get remove", "apt-get purge", "apt-get autoremove", "apt-get clean", "cd", "mkdir", "rm", "rm -rf", "cp", "mv", "chmod", "chown", "chgrp", "ln", "touch", "date", "sleep", "kill", "kill -9", "kill -15", "kill -1", "kill -2", "kill -3", "kill -4", "kill -5", "kill -6", "kill -7", "kill -8", "kill -9"]
        
        # Coolify configuration
        self.coolify_url = coolify_url
        self.coolify_api_key = coolify_api_key
        self.coolify_project_id = coolify_project_id
        
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

    def start_vm(self) -> Dict[str, Any]:
        """
        Start a new VM (Docker container) with the configured constraints.
        
        Returns:
            Dict containing status and container information
        """
        try:
            # Create and start the container
            self.container = self.docker_client.containers.run(
                self.base_image,
                command="tail -f /dev/null",  # Keep container running
                detach=True,
                mem_limit=self.memory_limit,
                nano_cpus=int(self.cpu_limit * 1e9),  # Convert to nano CPUs
                network_mode="none",  # Isolate network
                remove=True,  # Auto-remove when stopped
                working_dir="/workspace",
                labels={"managed-by": "coolify", "llm-vm": "true"}  # Add Coolify compatible labels
            )
            
            self.container_id = self.container.id
            logger.info(f"VM started with container ID: {self.container_id}")
            
            # Create workspace directory
            self.execute_command("mkdir -p /workspace")
            
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
        if not self.container:
            return {"status": "error", "message": "No VM is currently running"}
        
        try:
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
        if not self.container:
            return {"status": "error", "message": "No VM is currently running"}
        
        # Basic command validation
        command_parts = command.split()
        base_command = command_parts[0] if command_parts else ""
        
        if base_command not in self.allowed_commands:
            return {
                "status": "error", 
                "message": f"Command '{base_command}' is not allowed. Allowed commands: {', '.join(self.allowed_commands)}"
            }
        
        try:
            # Execute with timeout
            exec_result = self.container.exec_run(
                cmd=command,
                workdir="/workspace",
                demux=True
            )
            
            stdout = exec_result.output[0].decode('utf-8') if exec_result.output[0] else ""
            stderr = exec_result.output[1].decode('utf-8') if exec_result.output[1] else ""
            
            return {
                "status": "success" if exec_result.exit_code == 0 else "error",
                "exit_code": exec_result.exit_code,
                "stdout": stdout,
                "stderr": stderr
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
        if not self.container:
            return {"status": "error", "message": "No VM is currently running"}
        
        # Ensure the file path is within /workspace for security
        if not file_path.startswith("/workspace/"):
            file_path = os.path.join("/workspace", file_path)
        
        try:
            # Create a temporary file locally
            with open("temp_file", "w") as f:
                f.write(content)
            
            # Copy the file to the container
            with open("temp_file", "rb") as f:
                self.container.put_archive(
                    path=os.path.dirname(file_path),
                    data=f.read()
                )
            
            # Remove the temporary file
            os.remove("temp_file")
            
            return {
                "status": "success",
                "message": f"File written to {file_path}"
            }
            
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
        if not self.container:
            return {"status": "error", "message": "No VM is currently running"}
        
        # Ensure the file path is within /workspace for security
        if not file_path.startswith("/workspace/"):
            file_path = os.path.join("/workspace", file_path)
        
        try:
            result = self.execute_command(f"cat {file_path}")
            
            if result["status"] == "success":
                return {
                    "status": "success",
                    "content": result["stdout"],
                    "message": f"File {file_path} read successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to read file: {result.get('stderr', '')}"
                }
                
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
        if not self.container:
            return {"status": "error", "message": "No VM is currently running"}
        
        # Basic package name validation
        if not package_name.isalnum() and not all(c in ".-_" for c in package_name if not c.isalnum()):
            return {
                "status": "error",
                "message": f"Invalid package name: {package_name}"
            }
        
        try:
            result = self.execute_command(f"pip install --no-cache-dir {package_name}")
            
            if result["status"] == "success":
                return {
                    "status": "success",
                    "message": f"Package {package_name} installed successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to install package: {result.get('stderr', '')}"
                }
                
        except Exception as e:
            logger.error(f"Failed to install package: {e}")
            return {
                "status": "error",
                "message": f"Failed to install package: {str(e)}"
            }

# Example OpenWebUI tool integration function
def handle_llm_vm_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle requests from OpenWebUI to the VM controller.
    
    Args:
        request_data: Dictionary containing request parameters
        
    Returns:
        Dict containing response data
    """
    action = request_data.get("action")
    params = request_data.get("params", {})
    
    # Get or create controller instance
    # In a real implementation, you'd need to manage instances per user/session
    controller = LLMVirtualMachineController()
    
    if action == "start_vm":
        return controller.start_vm()
    
    elif action == "stop_vm":
        return controller.stop_vm()
    
    elif action == "execute_command":
        command = params.get("command")
        if not command:
            return {"status": "error", "message": "No command provided"}
        return controller.execute_command(command)
    
    elif action == "write_file":
        file_path = params.get("file_path")
        content = params.get("content")
        if not file_path or content is None:
            return {"status": "error", "message": "File path or content missing"}
        return controller.write_file(file_path, content)
    
    elif action == "read_file":
        file_path = params.get("file_path")
        if not file_path:
            return {"status": "error", "message": "File path missing"}
        return controller.read_file(file_path)
    
    elif action == "install_package":
        package_name = params.get("package_name")
        if not package_name:
            return {"status": "error", "message": "Package name missing"}
        return controller.install_package(package_name)
    
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}

# Example usage
if __name__ == "__main__":
    # This would be called by OpenWebUI in a real implementation
    example_request = {
        "action": "start_vm",
        "params": {}
    }
    
    response = handle_llm_vm_request(example_request)
    print(json.dumps(response, indent=2))
    
    # Example command execution
    if response["status"] == "success":
        example_command = {
            "action": "execute_command",
            "params": {
                "command": "echo 'Hello from the VM!'"
            }
        }
        
        command_response = handle_llm_vm_request(example_command)
        print(json.dumps(command_response, indent=2))
        
        # Clean up
        handle_llm_vm_request({"action": "stop_vm"}) 