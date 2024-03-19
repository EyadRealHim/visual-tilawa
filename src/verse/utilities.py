def path2url(path, url):
    return f"{url}/{path}" if not str(path).startswith("//") else f"https:{path}"