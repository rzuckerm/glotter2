All of Glotter2's global settings are set in a file called `.glotter.yml` using [YAML syntax](https://yaml.org/)
This file can be placed anywhere in the filesystem of your project, but it is recommended to place it at the root.

There are two root level sections.

## Settings

Settings are generic global settings.
The following shows what settings are available and their purpose.

### Acronym Scheme

**Required**  
**Format**: `acronym_scheme: "value"`  
**Default**: two_letter_limit  

#### Description

The acronym scheme determines how the Glotter2 should handle file names that contain acronyms.

#### Values

`upper` - All acronyms are expected to be upper case.
`lower` - All acronyms are expected to be lower case
`two_letter_limit` - If an acronym is two letters or less and the project naming scheme is pascal or camel, the the acronym is expected to be upper case. Otherwise it is expected lower case.

### Project Root

**Optional**  
**Format**: `project_root: "path/to/root"`  
**Default**: The directory containing your `.glotter.yml`  

#### Description

Project root is the path to the root of your project.
It can be absolute or relative from the path of the `.glotter.yml`.
This is used as the root directory when scanning the filesystem for scripts and tests.

### Source Root

**Optional**  
**Format**: `source_root: "path/to/root"`  
**Default**: the value of `project_root`  

#### Description

Source root is the path to the directory containing all of the scripts to run execute with Glotter2.
It can be absolute or relative from `project_root`.

## Projects

The projects section contains all of the information about each "project" that is implemented in your project.
Each project has:
- a project key
- a list of words that make up the name of the project depending on naming scheme
- a list of the words in the word list that are acronyms
- a flag of whether the project will require command line arguments

### Format

The format for a project is as follows:
```yml
projectkey:
  words:
    - "words"
    - "in"
    - "project"
  acronyms:
    - "acronyms"
    - "in"
    - "project"
  requires_parameters: true
```
So for example. Let's say I have three projects named FileIO, Factorial, and HelloWorld.
FileIO contains an acronym.
Factorial requires parameters.
My `projects` section would look like this:

```yml
projects
  fileio:
    words:
      - "file"
      - "io"
    acronyms:
      - "io"
    requires_parameters: false
  factorial:
    words:
      - "factorial"
    requires_parameters: true
  helloworld:
    words:
      - "hello"
      - "world"
    requires_parameters: false
```

## Example

The following is an example of a full `.glotter.yml`

```yml
settings:
  acronym_scheme: "two_letter_limit"
  project_root: "./my_project"
  source_root: "./sources"

projects
  fileio:
    words:
      - "file"
      - "io"
    acronyms:
      - "io"
    requires_parameters: false
  factorial:
    words:
      - "factorial"
    requires_parameters: true
  helloworld:
    words:
      - "hello"
      - "world"
    requires_parameters: false
```
