Each directory that contains code that you want Glotter2 to recognize requires a file named `testinfo.yml`.
This file contains settings pertinent only to the current directory but does not affect child directories.

There are two root level sections.

## Folder

`folder` is data about the files in the directory that helps Glotter2 find them.

It has the following settings.

### Extension

`extension` is the file extension of files that Glotter2 will recognize in this directory.

### Naming

`naming` refers to the naming scheme that Glotter2 will use to find files in this directory.

The following are valid values.

| Name | Example | Description |
| --- | --- | --- |
| hyphen | hello-world | hyphen separated |
| underscore | hello_world | underscore separated |
| camel | helloWorld | each word starts with a capital _excluding_ the first, no separation |
| pascal | HelloWorld | each word starts with a capital _including_ the first, no separation |
| lower | helloworld | lower case, no separation |

## Container

`container` contains settings that help Glotter2 know how to build and run sources in this directory.

It has the following settings.

### Image

`image` is the docker image to use to run the source file.

### Tag

`tag` is the specific tag of the docker image to use to run the source file.

### Build

`build` is command that is run inside of docker in order to build the source.
This setting is optional as not all languages require a build step.

### CMD

`cmd` is the command that is run inside of docker in order to run the source (after it is built if necessary).

## Templating

[Jinja templating](https://palletsprojects.com/p/jinja/) can be used in the `build` or `cmd` setting of `container` in order to refer to the source by name or extension.

The following values are available.

| Jinja Format | Description |
| source.name | the name of the source file excluding extension |
| source.extension | the extension of the source file |
| source.path | the path to the source file excluding the name of the source and its extension |
| source.full_path | the full path to the source file including its name and extension |

## Example

The following is an example `testinfo.yml` file for a directory containing sources in go.

```yml
folder:
  extension: ".go"
  naming: "hyphen"

container:
  image: "golang"
  tag: "1.12-alpine"
  build: "go build -o {{ source.name }} {{ source.name}}{{ source.extension }}"
  cmd: "./{{ source.name }}"
```