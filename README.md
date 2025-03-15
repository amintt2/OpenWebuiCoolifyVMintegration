# OpenWebUI VM Integration for Coolify

This project provides a secure, sandboxed virtual machine environment for OpenWebUI, deployed through Coolify. It enables safe code execution, command running, and file operations within an isolated Ubuntu environment.

## Project Objectives

- **Secure Code Execution**: Provide a sandboxed environment for running user code without compromising the host system
- **Seamless Integration**: Connect OpenWebUI with a VM backend through a simple API interface
- **Coolify Deployment**: Leverage Coolify for easy deployment, scaling, and management
- **Environment Isolation**: Ensure complete isolation between user sessions and the host system
- **Resource Management**: Control CPU, memory, and disk usage to prevent abuse

The VM controller creates isolated Ubuntu containers that can execute code, install packages, and manage files while maintaining strict security boundaries.

## Features

- Ubuntu-based VM environment
- Automatic repository cloning
- Python environment with required dependencies
- Health check endpoint
- Ready for Coolify reverse proxy integration
- Configurable via environment variables
- Sandboxed VM execution environment for running code

## Setup Instructions for Coolify Deployment

### Prerequisites

- Coolify installed and running
- Access to the Coolify dashboard
- Git repository access (if using private repositories)

### Deployment Steps

<details>
<summary><b>1. Create a new Application in Coolify</b> (click to expand)</summary>

1. In your Coolify dashboard, click on "Create a new Application"
2. Select "Deploy any public Git repositories"
3. Enter the Repository URL: `https://github.com/amintt2/OpenWebuiCoolifyVMintegration`
4. Click "Check repository"
5. Configure the following settings:
   - Build Pack: Select "Docker Compose"
   - Branch: `main`
   - Base Directory: `/`
6. Click "Continue" to proceed to the next step
</details>

<details>
<summary><b>2. Configure Application Settings</b> (click to expand)</summary>

After creating the application, you'll be taken to the Configuration page. Here you need to configure several settings:

1. **General Settings**:
   - Verify that Build Pack is set to "Docker Compose"
   - Docker Compose Location: `/docker-compose.yml`
   - Leave the default build and start commands

2. **Environment Variables**:
   Configure the following required environment variables:
   
   | Variable | Description | Example Value |
   |----------|-------------|---------------|
   | VM_PORT | Port for the backend API | 8080 |
   | WORKSPACE_DIR | Directory for workspace files | /workspace |
   | REPO_URL | URL of the repository to clone | https://github.com/amintt2/OpenWebui.git |
   | REPO_BRANCH | Branch of the repository to clone | main |
   | API_HOST | Host to bind the API server | 0.0.0.0 |
   | API_TIMEOUT | API request timeout in seconds | 120 |
   | ENABLE_AUTH | Enable authentication | false |
   | LOG_LEVEL | Logging level | info |
   
   Note: The environment variables are already defined in the Coolify interface, you just need to provide appropriate values.

3. **Resource Limits** (optional):
   - Set memory and CPU limits as needed for your environment

4. **Healthcheck** (optional):
   - The healthcheck is already configured in the docker-compose.yml file
   - Path: `/api/v1/health`
   - Port: `8080`
</details>

<details>
<summary><b>3. Deploy the Application</b> (click to expand)</summary>

1. After configuring all settings, click the "Deploy" button
2. Coolify will build and deploy the application based on the docker-compose.yml file
3. You can monitor the deployment progress in the Deployments tab
4. Once deployed, the application will be available at the URL provided by Coolify
</details>

<details>
<summary><b>4. Access your application</b> (click to expand)</summary>

Once deployed, Coolify will provide a public URL for your application. The backend API will be available at:

```
https://your-coolify-url.example.com/api/v1/
```

You can test the health check endpoint to verify the deployment:

```
https://your-coolify-url.example.com/api/v1/health
```
</details>

### Available Environment Variables

<details>
<summary><b>Complete list of environment variables</b> (click to expand)</summary>

| Variable | Description | Default |
|----------|-------------|---------|
| VM_PORT | Port for the backend API | 8080 |
| WORKSPACE_DIR | Directory for workspace files | /workspace |
| REPO_URL | URL of the repository to clone | https://github.com/amintt2/OpenWebui.git |
| REPO_BRANCH | Branch of the repository to clone | main |
| API_HOST | Host to bind the API server | 0.0.0.0 |
| API_TIMEOUT | API request timeout in seconds | 120 |
| HOST_PORT | Port exposed on the host machine | 8081 |
| COMMAND_TIMEOUT | Maximum execution time for commands | 3600 |
| OPENWEBUI_SESSION_ID | Unique session identifier | default |
| COOLIFY_HEALTHCHECK_PATH | Path for health check | /api/v1/health |
| COOLIFY_HEALTHCHECK_PORT | Port for health check | 8080 |
| ENABLE_AUTH | Enable authentication | false |
| MEMORY_LIMIT | Container memory limit | 2048m |
| CPU_LIMIT | Container CPU limit | 1.0 |
| LOG_LEVEL | Logging level | info |
</details>

## VM Controller Architecture

The VM Controller is the core component that manages the creation, execution, and termination of virtual machine instances. It provides a secure API for interacting with the VM environment.

<details>
<summary><b>Key components</b> (click to expand)</summary>

- **Docker Container**: Each VM is a lightweight Docker container based on Ubuntu
- **API Server**: RESTful API for executing commands and managing files
- **Session Management**: Isolation between different user sessions
- **Resource Controls**: Limits on CPU, memory, and execution time
- **Security Boundaries**: Restricted command execution and file access
</details>

<details>
<summary><b>API endpoints</b> (click to expand)</summary>

- `POST /api/v1/execute` - Execute a command in the VM
- `POST /api/v1/write_file` - Write content to a file in the VM
- `GET /api/v1/read_file` - Read content from a file in the VM
- `POST /api/v1/install` - Install a Python package in the VM
</details>

<details>
<summary><b>Example usage</b> (click to expand)</summary>

```python
import requests

# Execute a command
response = requests.post(
    "https://your-coolify-url.example.com/api/v1/execute",
    json={"command": "echo 'Hello World'"}
)
print(response.json())
```
</details>

## Health Check

The backend includes a health check endpoint at `/api/v1/health` that Coolify uses to monitor the service status.

## Troubleshooting

<details>
<summary><b>Common issues and solutions</b> (click to expand)</summary>

1. **Deployment fails**:
   - Check the Coolify logs for error messages
   - Verify that all required environment variables are set correctly
   - Ensure the Docker Compose file is correctly detected

2. **Application starts but health check fails**:
   - Check if the VM_PORT is correctly set and matches the COOLIFY_HEALTHCHECK_PORT
   - Verify that the API server is running inside the container
   - Check container logs for any startup errors

3. **API endpoints not responding**:
   - Verify that the application is properly deployed and running
   - Check if the correct URL is being used to access the API
   - Ensure that the VM_PORT is correctly exposed in the docker-compose.yml

4. **Resource limitations**:
   - If the application is running slowly or crashing, consider increasing the MEMORY_LIMIT and CPU_LIMIT
</details>

## Security Considerations

<details>
<summary><b>Security measures</b> (click to expand)</summary>

- All VMs run in isolated environments
- File operations are restricted to the workspace directory
- Resource usage is constrained by memory and CPU limits
- Command execution is limited to a predefined set of allowed commands
- Environment variables with sensitive information are not committed to version control
</details> 