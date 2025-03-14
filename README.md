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

## Setup Instructions

### Prerequisites

- Coolify installed and running
- Git repository access (if using private repositories)
- Docker installed on the host machine

### Deployment Steps

<details>
<summary><b>1. Clone the repository</b> (click to expand)</summary>

```bash
git clone https://github.com/yourusername/OpenWebui.git
cd OpenWebui
```
</details>

<details>
<summary><b>2. Set up environment variables</b> (click to expand)</summary>

For security reasons, the `.env` file is not included in the repository. You need to create it based on the provided template:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the environment variables with your actual values
nano .env
```

Make sure to set the following required variables in your `.env` file:

- `COOLIFY_URL`: URL of your Coolify instance
- `COOLIFY_API_KEY`: Your Coolify API key
- `COOLIFY_PROJECT_ID`: ID of your Coolify project

</details>

<details>
<summary><b>Available environment variables</b> (click to expand)</summary>

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
| COOLIFY_URL | URL of your Coolify instance | |
| COOLIFY_API_KEY | Your Coolify API key | |
| COOLIFY_PROJECT_ID | ID of the Coolify project | |
| ENABLE_AUTH | Enable authentication | false |
| MEMORY_LIMIT | Container memory limit | 2048m |
| CPU_LIMIT | Container CPU limit | 1.0 |
| LOG_LEVEL | Logging level | info |
| COOLIFY_HEALTHCHECK_PATH | Path for health check | /api/v1/health |
| COOLIFY_HEALTHCHECK_PORT | Port for health check | 8080 |
</details>

<details>
<summary><b>3. Deploy with Coolify</b> (click to expand)</summary>

- In Coolify dashboard, create a new service
- Select "Docker Compose" as the deployment type
- Point to the directory containing this repository
- Coolify will automatically detect the docker-compose.yml file
- Deploy the service
</details>

<details>
<summary><b>4. Access your application</b> (click to expand)</summary>

Once deployed, Coolify will provide a public URL for your application. The backend API will be available at:

```
https://your-coolify-url.example.com/api/v1/
```
</details>

### Production Deployment Notes

<details>
<summary><b>Security best practices for production</b> (click to expand)</summary>

1. **Never commit the `.env` file to version control**
   - The `.env` file is included in `.gitignore` to prevent accidental commits
   - Always use the `.env.example` as a template and create your own `.env` file

2. **Use strong, unique values for sensitive variables**
   - Generate a strong random string for `JWT_SECRET` if authentication is enabled
   - Use a dedicated API key for Coolify with minimal required permissions

3. **Consider using a secrets management solution**
   - For more advanced deployments, consider using Docker secrets or a dedicated secrets manager
   - Coolify supports environment variable injection from its dashboard
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

## Customization

<details>
<summary><b>Configuration options</b> (click to expand)</summary>

- To use a different repository, update the `REPO_URL` and `REPO_BRANCH` in the `.env` file
- To add additional dependencies, update the `requirements.txt` file
- To change resource limits, update the `MEMORY_LIMIT` and `CPU_LIMIT` in the `.env` file
- To customize the VM environment, modify the allowed commands in the `VMController` class
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

## Troubleshooting

<details>
<summary><b>Common issues and solutions</b> (click to expand)</summary>

1. Check Coolify logs for error messages
2. Verify that the health check endpoint is responding
3. Ensure your repository is accessible from the Coolify server
4. Check the container logs for any Python errors
5. Verify that the VM controller is properly configured with the correct environment variables
6. Make sure all required environment variables are set in your `.env` file
</details> 