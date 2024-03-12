import docker
import re
import socket

def get_my_container(client: docker.DockerClient):

    container_id = socket.gethostname()

    try: 
        return client.containers.get(container_id)
    except docker.errors.NotFound:

        potential_container_id = None

        try:
            with open("/proc/self/cgroup", "r") as file:
                for line in file:
                    match = re.search(r'/docker/([a-f0-9]{64})$', line)
                    if match:
                        potential_container_id = match.group(1)
                        break

        except FileNotFoundError:
            raise Exception("Could not find container id")
        
        if potential_container_id:
            return client.containers.get(potential_container_id)
        else:
            raise Exception("Could not find container id")



def get_project_name(container):
    return container.labels.get("com.docker.compose.project")

client = docker.from_env()
container = get_my_container(client)

project_name = get_project_name(container)
print(project_name)
print(container)

def retrieve_sibling_containers(client: docker.DockerClient, project_name: str):
    # Filter containers by Docker Compose project label
    filters = {"label": f"com.docker.compose.project={project_name}"}
    containers = client.containers.list(all=True, filters=filters)
    return containers

sibling_containers = retrieve_sibling_containers(client, project_name)


for container in sibling_containers:
    labels = container.labels

    if "fakts.service" in labels:
        print(container.attrs["NetworkSettings"]["Ports"])


        print(container.name)
        print(labels["fakts.service"])
        print(container)