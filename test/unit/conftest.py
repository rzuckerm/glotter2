import os
import tempfile
from uuid import uuid4 as uuid

import pytest

from glotter import containerfactory
from glotter.project import Project
from glotter.singleton import Singleton
from glotter.source import Source
from glotter.testinfo import ContainerInfo

from .mockdocker import DockerMock


@pytest.fixture
def docker():
    docker_mock = DockerMock()
    docker_mock.clear()
    yield docker_mock
    docker_mock.clear()


@pytest.fixture
def factory(docker):
    return containerfactory.ContainerFactory(docker_client=docker)


@pytest.fixture
def container_info():
    iid = uuid().hex
    return ContainerInfo(
        image=f"image_{iid}",
        tag=f"tag_{iid}",
        cmd=f"cmd_{iid}",
    )


@pytest.fixture
def test_info_string_no_build():
    return """folder:
  extension: ".py"
  naming: "underscore"

container:
  image: "python"
  tag: "3.7-alpine"
  cmd: "python {{ source.name }}{{ source.extension }}"
"""


@pytest.fixture
def test_info_string_with_build():
    return """folder:
  extension: ".go"
  naming: "hyphen"

container:
  image: "golang"
  tag: "1.12-alpine"
  build: "go build -o {{ source.name }} {{ source.name}}{{ source.extension }}"
  cmd: "./{{ source.name }}"
"""


@pytest.fixture
def source_no_build(test_info_string_no_build):
    iid = uuid().hex
    return Source(
        name=f"sourcename_{iid}",
        language="python",
        path=f"sourcepath_{iid}",
        test_info_string=test_info_string_no_build,
    )


@pytest.fixture
def source_with_build(test_info_string_with_build):
    iid = uuid().hex
    return Source(
        name=f"sourcename_{iid}",
        language="go",
        path=f"sourcepath_{iid}",
        test_info_string=test_info_string_with_build,
    )


@pytest.fixture
def no_io(monkeypatch):
    monkeypatch.setattr("tempfile.mkdtemp", lambda *args, **kwargs: "TEMP_DIR")
    monkeypatch.setattr("os.chmod", lambda *args, **kwargs: "")
    monkeypatch.setattr("shutil.copy", lambda *args, **kwargs: "")
    monkeypatch.setattr("shutil.rmtree", lambda *args, **kwargs: "")


@pytest.fixture
def glotter_yml_projects():
    return {
        "baklava": Project(
            words=["baklava"],
            requires_parameters=False,
        ),
        "fileio": Project(words=["file", "io"], requires_parameters=False, acronyms=["io"]),
        "fibonacci": Project(words=["fibonacci"], requires_parameters=True),
        "helloworld": Project(words=["hello", "world"], requires_parameters=False),
    }


@pytest.fixture
def mock_projects(glotter_yml_projects, monkeypatch):
    return monkeypatch.setattr("glotter.settings.Settings.projects", glotter_yml_projects)


@pytest.fixture
def mock_sources(test_info_string_no_build):
    yield {
        "baklava": [
            Source(
                name="baklava.b",
                language="bar",
                path=os.path.join("archive", "b", "bar", "baklava.b"),
                test_info_string=test_info_string_no_build,
            ),
            Source(
                name="baklava.b",
                language="bart",
                path=os.path.join("archive", "b", "bart", "baklava.b"),
                test_info_string=test_info_string_no_build,
            ),
        ],
        "fileinputoutput": [
            Source(
                name="file-input-output.b",
                language="bart",
                path=os.path.join("archive", "b", "bart", "file-input-output.b"),
                test_info_string=test_info_string_no_build,
            ),
        ],
        "quine": [
            Source(
                name="quine.b",
                language="bar",
                path=os.path.join("archive", "b", "bar", "quine.b"),
                test_info_string=test_info_string_no_build,
            ),
            Source(
                name="quine.b",
                language="bart",
                path=os.path.join("archive", "b", "bart", "quine.b"),
                test_info_string=test_info_string_no_build,
            ),
            Source(
                name="Quine.cl",
                language="cool",
                path=os.path.join("archive", "c", "cool", "Quine.cl"),
                test_info_string=test_info_string_no_build,
            ),
        ],
    }


@pytest.fixture()
def temp_dir_chdir():
    curr_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp_dir_:
        tmp_dir = os.path.realpath(tmp_dir_)
        os.chdir(tmp_dir)
        try:
            yield tmp_dir
        finally:
            os.chdir(curr_cwd)


@pytest.fixture(autouse=True)
def clear_singleton():
    Singleton.clear()
    try:
        yield
    finally:
        Singleton.clear()
