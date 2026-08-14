from uuid import uuid4
import collections.abc
from urllib.request import urlopen
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from karakter.datalayer import get_current_datalayer
from karakter.models import MediaStore
from django.conf import settings

def update_nested(d, u):
    """Update a nested dictionary or similar mapping."""
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_nested(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def download_logo(url: str) -> File:
    """Download a logo from a URL and return a Django File object, that can be
    used directly in a model."""
    img_tmp = NamedTemporaryFile(delete=True)
    with urlopen(url) as uo:
        # Raises rather than asserts: this validates a *remote* response, and
        # `assert` is stripped under `python -O`, which would store whatever the
        # far end returned — an error page, or a non-image payload.
        if uo.status != 200:
            raise ValueError(f"Could not download logo from {url}: HTTP {uo.status}")
        content_type = uo.headers.get('Content-Type', '')
        if content_type != 'image/png':
            raise ValueError(f"Expected PNG image, got {content_type}")
        img_tmp.write(uo.read())
        img_tmp.flush()
        
        
       
     
    key = f"{uuid4()}.png"
    bucket = settings.MEDIA_BUCKET
    
    img_tmp.seek(0)
    
    store = MediaStore.objects.create(
        path=f"{bucket}/{key}", key=key, bucket=bucket
    )
    
    store.put_file(get_current_datalayer(), img_tmp)
        
    return store
