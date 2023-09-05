from fakts import base_models
from fakts import models
import re
from jinja2 import Template, TemplateSyntaxError, TemplateError
import yaml
from pydantic import BaseModel, Field
import re
from typing import Optional
from fakts import fields, errors
from django.http import HttpRequest
from uuid import uuid4




def render_template(composition: models.Composition, context: base_models.LinkingContext) -> dict:
    return yaml.load(Template(composition.template).render(context), Loader=yaml.SafeLoader)


def create_api_token():
    return str(uuid4())


def create_device_code():
    return "".join([str(uuid4())[-1] for _ in range(8)])


def create_linking_context(request: HttpRequest, client: models.Client) -> base_models.LinkingContext:
    host_string = request.get_host().split(":")
    if len(host_string) == 2:
        host = host_string[0]
        port = host_string[1]
    else:
        host = host_string[0]
        port = None

    return base_models.LinkingContext(
        request=base_models.LinkingRequest(
            host=host,
            port=port,
            is_secure=request.is_secure(),
        ),
        manifest=base_models.Manifest(
            identifier=client.release.app.identifier,
            version=client.release.version,
            scopes=client.release.scopes,
        ),
        client=base_models.LinkingClient(
            client_id=client.client_id,
            client_secret=client.client_secret,
            client_type=client.oauth2_client.client_type,
            authorization_grant_type=client.oauth2_client.authorization_grant_type,
            name=client.oauth2_client.name,
            redirect_uris=client.oauth2_client.redirect_uris.split(" "),
        ),
    )





