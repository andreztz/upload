


def parse_header_options(header):
    if not header:
        return None, {}
    parts = header.split(';')
    content_type, opts = parts[0].lower(), parts[1:]
    options = {k.strip(): v.strip('"')
        for k, sep, v in
        (option.partition('=') for option in opts)
    }
    return content_type, options
