import os

import pytest

from glotter import source


def get_hello_world(language):
    return {
        "python": "def main():\n  print('Hello, world!')\n\nif __name__ == '__main__':\n  main()",
        "go": 'package main\n\nimport "fmt"\n\nfunc main() {\n\tfmt.Println("Hello, World!")\n}',
    }[language]


def create_files_from_list(files):
    for file_path, contents in files.items():
        dir_ = os.path.dirname(file_path)
        if not os.path.isdir(dir_):
            os.makedirs(dir_)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(contents)


def get_files(tmp_dir, test_info_string_no_build, test_info_string_with_build):
    return {
        os.path.join(tmp_dir, "python", "testinfo.yml"): test_info_string_no_build,
        os.path.join(tmp_dir, "python", "hello_world.py"): get_hello_world("python"),
        os.path.join(tmp_dir, "go", "testinfo.yml"): test_info_string_with_build,
        os.path.join(tmp_dir, "go", "hello-world.go"): get_hello_world("go"),
    }


def test_get_sources_when_no_testinfo(
    tmp_dir, test_info_string_no_build, test_info_string_with_build, mock_projects
):
    files = {
        os.path.join(tmp_dir, "python", "helloworld.py"): get_hello_world("python"),
        os.path.join(tmp_dir, "go", "hello-world.go"): get_hello_world("go"),
    }
    create_files_from_list(files)
    sources = source.get_sources(tmp_dir)
    assert not any(sources.values())


def test_get_sources(
    tmp_dir,
    test_info_string_no_build,
    test_info_string_with_build,
    glotter_yml_projects,
    mock_projects,
):
    files = get_files(tmp_dir, test_info_string_no_build, test_info_string_with_build)
    create_files_from_list(files)
    sources = source.get_sources(tmp_dir)
    assert len(sources["helloworld"]) == 2
    assert source.BAD_SOURCES not in sources
    assert not any(
        source_list
        for project_type, source_list in sources.items()
        if project_type != "helloworld" and len(source_list) > 0
    )


@pytest.mark.parametrize(
    "bad_sources",
    [
        pytest.param({}, id="no-bad-sources"),
        pytest.param(
            {
                os.path.join("python", "foo.py"): "",
                os.path.join("python", "bar.py"): "",
                os.path.join("go", "helloworld.go"): "",
            },
            id="bad-sources",
        ),
    ],
)
def test_get_sources_with_check_bad_sources(
    bad_sources,
    tmp_dir,
    test_info_string_no_build,
    test_info_string_with_build,
    glotter_yml_projects,
    mock_projects,
):
    files = get_files(tmp_dir, test_info_string_no_build, test_info_string_with_build)
    for filename, contents in bad_sources.items():
        files[os.path.join(tmp_dir, filename)] = contents

    create_files_from_list(files)
    sources = source.get_sources(tmp_dir, check_bad_sources=True)

    expected_bad_sources = sorted(bad_sources)
    actual_bad_sources = sorted(sources[source.BAD_SOURCES])
    assert actual_bad_sources == expected_bad_sources
