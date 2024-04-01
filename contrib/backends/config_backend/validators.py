from django.core.exceptions import ValidationError
from fakts.base_models import LinkingContext, LinkingRequest, Manifest, LinkingClient
from jinja2 import Template, TemplateSyntaxError, TemplateError, StrictUndefined
import yaml

def is_valid_jinja2_template(template_string, render_context=None):
    """ Checks if a template string is a valid Jinja2 template. And if it is,
    it checks if it is a valid YAML file, wher rendered with a fakt context If it is not, it raises a ValueError"""
    try:
        template = Template(template_string, undefined=StrictUndefined)
        try:
            rendered_template = template.render(render_context )
            yaml.safe_load(rendered_template)
        except (TemplateError, yaml.YAMLError) as e:
            raise ValueError(f"Rendering error: {e}") from e
    except TemplateSyntaxError as e:
        raise ValueError(f"Template syntax error: {e}") from e
    


def jinja2_yaml_template_validator(value):
    """ Validates that a string is a valid Jinja2 template. And if it is,
    it checks if it is a valid YAML file, wher rendered with a fakt context If it is not, it raises a ValidationError
    """
    

    fake_context = LinkingContext(
        request=LinkingRequest(
            host="example.com",
            port="443",
            is_secure=True,
        ),
        manifest=Manifest(
            identifier="com.example.app",
            version="1.0",
            scopes=["scope1", "scope2"],
            redirect_uris=["https://example.com"],
        ),
        client=LinkingClient(
            client_id="@client_id",
            client_secret="@client_secret",
            client_type="@client_type",
            authorization_grant_type="authorization_grant_type",
            name="@name",
        ),
    )


    try:
        is_valid_jinja2_template(value, fake_context.dict())
    except ValidationError as e:
        raise ValueError(e)
    
    return value


def fake_load_yaml(value):
    """ Loads a string as a YAML file. If it is not a valid YAML file, it raises a ValidationError"""



    try:
        return yaml.safe_load(value)
    except yaml.YAMLError as e:
        raise ValidationError(f"YAML error: {e}") from e