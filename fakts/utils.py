from uuid import uuid4
import collections.abc
from urllib.request import urlopen
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile


def update_nested(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_nested(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def download_logo(url: str) -> File:
    img_tmp = NamedTemporaryFile(delete=True)
    with urlopen(url) as uo:
        assert uo.status == 200
        img_tmp.write(uo.read())
        img_tmp.flush()
    return File(img_tmp)


def download_placeholder(identifier: str, version: str) -> File:
    return download_logo(
        f"https://eu.ui-avatars.com/api/?name={identifier}&background=random"
    )
