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
