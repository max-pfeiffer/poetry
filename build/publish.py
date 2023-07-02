import click
import docker
from build.constants import (
    TARGET_ARCHITECTURES,
    PYTHON_POETRY_IMAGE_NAME,
)
from build.images import PythonPoetryImage

from docker.client import DockerClient


@click.command()
@click.option(
    "--docker-hub-username",
    envvar="DOCKER_HUB_USERNAME",
    help="Docker Hub username",
)
@click.option(
    "--docker-hub-password",
    envvar="DOCKER_HUB_PASSWORD",
    help="Docker Hub password",
)
@click.option(
    "--version-tag", envvar="GIT_TAG_NAME", required=True, help="Version Tag"
)
@click.option("--registry", envvar="REGISTRY", help="Docker registry")
def main(
    docker_hub_username: str,
    docker_hub_password: str,
    version_tag: str,
    registry: str,
) -> None:
    docker_client: DockerClient = docker.from_env()

    for target_architecture in TARGET_ARCHITECTURES:
        new_python_poetry_image: PythonPoetryImage = PythonPoetryImage(
            docker_client, None, target_architecture, version_tag
        )

        # Delete old existing images
        for old_image in docker_client.images.list(
            new_python_poetry_image.image_name
        ):
            for tag in old_image.tags:
                docker_client.images.remove(tag, force=True)

        new_python_poetry_image.build()

        # https://docs.docker.com/engine/reference/commandline/push/
        # https://docs.docker.com/engine/reference/commandline/tag/
        # https://docs.docker.com/engine/reference/commandline/image_tag/
        if docker_hub_username and docker_hub_password:
            login_kwargs: dict = {
                "username": docker_hub_username,
                "password": docker_hub_password,
            }
            if registry:
                login_kwargs["registry"] = registry

            docker_client.login(**login_kwargs)

        if registry:
            repository: str = f"{registry}/{new_python_poetry_image.image_name}"
        else:
            repository: str = new_python_poetry_image.image_name

        for line in docker_client.images.push(
            repository,
            tag=new_python_poetry_image.image_tag,
            stream=True,
            decode=True,
        ):
            print(line)
    docker_client.close()


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
