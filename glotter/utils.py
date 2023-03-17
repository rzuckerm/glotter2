import sys


def quote(value: str) -> str:
    """
    Enclose a value in quotes

    :param value: Value to enclosed
    :return: Quoted value

    """

    if '"' in value:
        if "'" in value:
            quote_chars = '"""'
            if value.startswith('"'):
                value = f"\\{value}"
        else:
            quote_chars = "'"
    else:
        quote_chars = '"'

    return f"{quote_chars}{value}{quote_chars}"


def indent(value: str, num_spaces: int) -> str:
    """
    Indent each line of a string by a specified number of spaces

    :param value: String to indent
    :param num_spaces: Number of spaces to indent
    :return: Indented string
    """

    spaces = " " * num_spaces
    return "".join(f"{spaces}{line}" for line in value.splitlines(keepends=True))


def error_and_exit(msg):
    print(msg)
    sys.exit(1)
