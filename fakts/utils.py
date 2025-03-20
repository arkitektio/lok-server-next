from uuid import uuid4
import collections.abc
from urllib.request import urlopen
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from karakter.datalayer import get_current_datalayer, Datalayer
from karakter.models import MediaStore
from django.conf import settings
from django.core.cache import cache

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
        assert uo.status == 200
        content_type = uo.headers.get('Content-Type', '')
        assert content_type == 'image/png', f"Expected PNG image, got {content_type}"
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
    
   
        


def download_placeholder(identifier: str, version: str) -> File:
    """Download a placeholder logo from a URL and return a Django File object, that can be
    uses directly in a model."""
    return download_logo(
        f"https://eu.ui-avatars.com/api/?name={identifier}&background=random"
    )



