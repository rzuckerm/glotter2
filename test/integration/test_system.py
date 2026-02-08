from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import yaml

TEST_DATA_DIR = Path("test/integration/data/system-test").resolve()

pytestmark = pytest.mark.skipif(
    shutil.which("docker") is None, reason="docker executable is not found"
)


@dataclass
class DockerInfo:
    docker_image: str
    language: str
    filenames: list[str] = field(default_factory=list)


def get_docker_info_list() -> list[DockerInfo]:
    docker_info_list = []
    for root, _, files in os.walk(TEST_DATA_DIR):
        if "testinfo.yml" in files:
            with Path(root, "testinfo.yml").open(encoding="utf-8") as f:
                contents = yaml.safe_load(f)

            extension = contents["folder"]["extension"]
            container_info = contents["container"]
            docker_info_list.append(
                DockerInfo(
                    docker_image=f"{container_info['image']}:{container_info['tag']}",
                    language=Path(root).name,
                    filenames=[
                        Path(root, file_).name for file_ in files if file_.endswith(extension)
                    ],
                )
            )

    return docker_info_list


def get_language_params() -> list:
    docker_info_list = get_docker_info_list()
    projects = json.loads(Path(TEST_DATA_DIR, "expected_result.json").read_text(encoding="utf-8"))
    return [
        pytest.param(
            docker_info.language,
            filename,
            projects[_filename_to_project(filename)],
            id=f"{docker_info.language}/{filename}",
        )
        for docker_info in docker_info_list
        for filename in docker_info.filenames
    ]


def _filename_to_project(filename: str) -> str:
    return Path(filename).stem.lower().replace("_", "").replace("-", "")


@pytest.mark.parametrize(("language", "filename", "project_info"), get_language_params())
def test_run(language: str, filename: str, project_info: dict[str, str], project_dir: str):
    cmd = ["glotter", "run", "-l", language, "-s", filename]
    if "input" in project_info:
        with subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, encoding="utf-8"
        ) as proc:
            stdout, _ = proc.communicate(f"{project_info['input']}\n")

        assert proc.returncode == 0
    else:
        stdout = subprocess.run(cmd, capture_output=True, check=True, encoding="utf-8").stdout

    assert project_info["expected_output"] in stdout


def test_test_pass(project_dir: str):
    result = subprocess.run(["glotter", "test"], capture_output=True, check=False, encoding="utf-8")

    assert result.returncode == 0
    for param in get_language_params():
        language, filename, _ = param.values
        assert f"{language}/{filename}" in result.stdout


def test_test_fail(project_dir: str):
    for root, _, files in os.walk(project_dir):
        if "testinfo.yml" in files:
            for filename in files:
                if _filename_to_project(filename) == "helloworld":
                    path = Path(root, filename)
                    contents = path.read_text(encoding="utf-8")
                    path.write_text(contents.replace("Hello", "Goodbye"), encoding="utf-8")

    result = subprocess.run(["glotter", "test"], capture_output=True, check=False, encoding="utf-8")

    assert result.returncode != 0
    assert "FAIL" in result.stdout


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
        encoding="utf-8",
        check=True,
    ).stdout.splitlines()
    for docker_info in docker_info_list:
        if docker_info.docker_image in loaded_docker_images:
            subprocess.run(["docker", "rmi", docker_info.docker_image], check=True)


@pytest.fixture
def project_dir(tmp_dir_chdir: str) -> str:
    for root, _, files in os.walk(TEST_DATA_DIR):
        dest_dir_path = Path(tmp_dir_chdir) / Path(root).relative_to(TEST_DATA_DIR)
        dest_dir_path.mkdir(parents=True, exist_ok=True)
        for filename in files:
            shutil.copy(Path(root, filename), dest_dir_path / filename)

    return tmp_dir_chdir
