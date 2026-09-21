import logging
import subprocess


logger = logging.getLogger("AgentSandbox")


class DockerSandboxRunner:
    def execute_in_sandbox(self, script_path: str):
        logger.info(
            f"Isolating and executing script in Docker container: {script_path}"
        )
        command = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{script_path}:/app/script.py",
            "python:3.11-slim",
            "python",
            "/app/script.py",
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as error:
            return f"Sandbox execution error: {str(error)}"
