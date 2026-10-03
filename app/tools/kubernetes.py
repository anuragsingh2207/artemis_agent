import json
import subprocess


def get_pods() -> str:
    """Get the current status of all pods in the Kubernetes cluster."""

    try:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-A", "-o", "json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )

        data = json.loads(result.stdout)

        pods = []

        for pod in data.get("items", []):
            metadata = pod.get("metadata", {})
            status = pod.get("status", {})

            container_statuses = status.get("containerStatuses", [])

            restarts = sum(
                container.get("restartCount", 0)
                for container in container_statuses
            )

            ready = sum(
                1
                for container in container_statuses
                if container.get("ready", False)
            )

            total = len(container_statuses)

            pods.append(
                {
                    "namespace": metadata.get("namespace"),
                    "name": metadata.get("name"),
                    "phase": status.get("phase"),
                    "ready": f"{ready}/{total}",
                    "restarts": restarts,
                }
            )

        return json.dumps(
            {
                "pod_count": len(pods),
                "pods": pods,
            },
            indent=2,
        )

    except subprocess.CalledProcessError as e:
        return json.dumps(
            {
                "error": "kubectl command failed",
                "details": e.stderr.strip(),
            }
        )

    except subprocess.TimeoutExpired:
        return json.dumps(
            {
                "error": "kubectl command timed out"
            }
        )

    except json.JSONDecodeError:
        return json.dumps(
            {
                "error": "Failed to parse Kubernetes response"
            }
        )

    except Exception as e:
        return json.dumps(
            {
                "error": "Unexpected error",
                "details": str(e),
            }
        )