from io import BytesIO

from requests import get

def path2url(path, url):
    return f"{url}/{path}" if not str(path).startswith("//") else f"https:{path}"

def GET(url: str, **kwargs):
    response = get(url, **kwargs)
    response.raise_for_status()

    return response

def virtual_io(url: str, **kwargs):
    return BytesIO(GET(url=url, **kwargs).content)