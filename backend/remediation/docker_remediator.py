import subprocess


def restart_container(container_name: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["docker", "restart", container_name],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )

        if result.returncode == 0:
            return True, result.stdout.strip()

        error = result.stderr.strip() or result.stdout.strip()
        return False, error

    except subprocess.TimeoutExpired:
        return False, "Docker restart timed out."

    except FileNotFoundError:
        return False, "Docker CLI was not found."
