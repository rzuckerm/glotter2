from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import yaml

TEST_DATA_DIR = Path("test/integration/data/system-test").resolve()


@dataclass
class DockerInfo:
    docker_image: str
    language: str
    files: list[str] = field(default_factory=list)


def get_docker_info_list() -> list[DockerInfo]:
    docker_info_list = []
    for root, _, files in os.walk(TEST_DATA_DIR):
        if "testinfo.yml" in files:
            with Path(root, "testinfo.yml").open(encoding="utf-8") as f:
                contents = yaml.safe_load(f)

            extension = contents["folder_info"]["extension"]
            container_info = contents["container_info"]
            docker_info_list.append(
                DockerInfo(
                    docker_image=f"{container_info['image']}:{container_info['tag']}",
                    language=Path(root).name,
                    files=[str(Path(root, file_) for file_ in files if file_.endswith(extension))],
                )
            )

    return docker_info_list


@pytest.fixture(scope="module", autouse=True)
def remove_docker_images():
    _remove_docker_images()
    try:
        yield
    finally:
        _remove_docker_images()


def _remove_docker_images() -> None:
    docker_info_list = get_docker_info_list()
    loaded_docker_images = subprocess.run(
        ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    for docker_info in docker_info_list:
        if docker_info.docker_image in loaded_docker_images:
            subprocess.run(["docker", "rmi", docker_info.docker_image], check=True)
