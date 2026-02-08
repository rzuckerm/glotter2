from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml
import pytest

TEST_DATA_DIR = Path("test/integration/data/system-test").resolve()

@pytest.fixture(scope="module", autouse=True)
def remove_docker_images():
    _remove_docker_images()
    try:
        yield
    finally:
        _remove_docker_images()

def get_docker_images() -> list[str]:
    docker_images = []
    for root, _, files in os.walk(TEST_DATA_DIR):
        if "testinfo.yml" in files:
            with Path(root, "testinfo.yml").open(encoding="utf-8") as f:
                folder_info = yaml.safe_load(f)["folder"]

            docker_images.append(f"{folder_info['image']}:{folder_info['tag']}")

    return docker_images

def _remove_docker_images() -> None:
    docker_images = get_docker_images()
    loaded_docker_images = subprocess.run(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"], capture_output=True, check=True).stdout.splitlines()
    for docker_image in docker_images:
        if docker_image in loaded_docker_images:
            subprocess.run(["docker", "rmi", docker_image], check=True)
