import os
import shutil
import tempfile
from datetime import datetime, timedelta
from uuid import uuid4 as uuid

import docker

from glotter.singleton import Singleton


class ContainerFactory(metaclass=Singleton):
    def __init__(self, docker_client=None):
        """
        Initialize a ContainerFactory. This class is a singleton.

        :param docker_client: optionally set the docker client. Defaults to setting from the environment
        """
        self._containers = {}
        self._volume_dis = {}
        self._client = docker_client or docker.from_env()
        self._api_client = self._client.api

    def get_container(self, source):
        """
        Returns a running container for a give source. This will return an existing container if one exists
        or create a new one if necessary

        :param source: the source to use inside the container
        :return: a running container specific to the source
        """
        key = source.full_path

        tmp_dir = tempfile.mkdtemp()
        os.chmod(tmp_dir, 0o777)
        shutil.copy(source.full_path, tmp_dir)
        self._volume_dis[key] = tmp_dir

        image = self.get_image(source.test_info.container_info)
        volume_info = {tmp_dir: {"bind": "/src", "mode": "rw"}}
        if key not in self._containers:
            self._containers[key] = self._client.containers.run(
                image=image,
                name=f"{source.name}_{uuid().hex}",
                command="sleep 1h",
                working_dir="/src",
                volumes=volume_info,
                detach=True,
            )
        return self._containers[key]

    def get_image(self, container_info, quiet=False, parallel=False):
        """
        Pull a docker image

        :param container_info: metadata about the image to pull
        :param quiet: whether to print output while downloading
        :param parallel: whether image download is occurring in parallel
        :return: a docker image
        """
        images = self._client.images.list(
            name=f"{container_info.image}:{str(container_info.tag)}"
        )
        if len(images) == 1:
            return images[0]
        if not quiet:
            end_char = "\n" if parallel else ""
            print(
                f"Pulling {container_info.image}:{container_info.tag}... ",
                end=end_char,
                flush=True,
            )
        last_update = datetime.now()
        for _ in self._api_client.pull(
            repository=container_info.image,
            tag=str(container_info.tag),
            stream=True,
            decode=True,
        ):
            if (
                not quiet
                and not parallel
                and datetime.now() - last_update > timedelta(seconds=5)
            ):
                print("... ", end="", flush=True)
                last_update = datetime.now()
        if not quiet:
            if parallel:
                print(
                    f"... done pulling {container_info.image}:{container_info.tag}",
                    flush=True,
                )
            else:
                print("done", flush=True)

        images = self._client.images.list(
            name=f"{container_info.image}:{str(container_info.tag)}"
        )
        if len(images) == 1:
            return images[0]

        return None

    def remove_image(self, container_info):
        """
        Remove a docker image

        :param container_info: metadata about the image to remove
        """

        image_name = f"{container_info.image}:{str(container_info.tag)}"
        images = self._client.images.list(
            name=f"{container_info.image}:{str(container_info.tag)}"
        )
        if len(images) == 1:
            print(f"Removing {image_name}", flush=True)
            self._client.images.remove(image=image_name, force=True)

    def cleanup(self, source):
        """
        Cleanup docker container and temporary folder. Also remove both from their
        respective dictionaries

        :param source: source for determining what to cleanup
        """
        key = source.full_path

        self._containers[key].remove(v=True, force=True)
        shutil.rmtree(self._volume_dis[key], ignore_errors=True)

        del self._volume_dis[key]
        del self._containers[key]
