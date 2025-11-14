from fakts import base_models, models, enums
from fakts import logic
from authapp.models import generate_client_id, generate_client_secret


def create_development_client(release: models.Release, config: base_models.DevelopmentClientConfig, manifest: base_models.Manifest, node: models.ComputeNode | None = None):
    tenant = config.get_tenant()
    user = config.get_user()
    organization = config.get_organization()

    try:
        client = models.Client.objects.get(user=user, release=release, organization=organization, node=node, kind=enums.ClientKindVanilla.DEVELOPMENT.value)
        if client.token != config.token:
            client.token = config.token
        client.tenant = tenant
        client.node = node
        client.public_sources = [t.dict() for t in manifest.public_sources] if manifest.public_sources else []
        client.save()

        return client

    except models.Client.DoesNotExist:
        print("Did not exist", user, release)
        client_secret = generate_client_secret()
        client_id = generate_client_id()

        oauth2_client = models.OAuth2Client.objects.create(
            user=user,
            client_id=client_id,
            client_secret=client_secret,
            organization=config.get_organization(),
        )

        return models.Client.objects.create(
            release=release,
            user=user,
            tenant=user,
            node=node,
            token=config.token,
            kind=enums.ClientKindVanilla.DEVELOPMENT.value,
            oauth2_client=oauth2_client,
            redirect_uris="",
            public=False,
            logo=release.logo,
            organization=organization,
            public_sources=[t.dict() for t in manifest.public_sources] if manifest.public_sources else [],
        )


def create_client(manifest: base_models.Manifest, config: base_models.ClientConfig, user: models.AbstractUser, organization: models.Organization):
    from .utils import download_logo

    try:
        logo = download_logo(manifest.logo) if manifest.logo else None
    except Exception as e:
        raise ValueError(f"Could not download logo {e}")

    app, _ = models.App.objects.get_or_create(identifier=manifest.identifier)
    if logo:
        app.logo = logo
        app.save()

    release, _ = models.Release.objects.update_or_create(
        app=app,
        version=manifest.version,
        defaults={
            "logo": logo,
            "scopes": manifest.scopes,
            "requirements": manifest.dict()["requirements"],
        },
    )

    if manifest.node_id:
        node = models.ComputeNode.objects.get_or_create(organization=organization, node_id=manifest.node_id)[0]
    else:
        node = None

    print(config)

    if config.kind == enums.ClientKindVanilla.DEVELOPMENT.value:
        client = create_development_client(release, config, manifest, node=node)
    else:
        raise ValueError(f"Client kind {config.kind} not supported yet")

    client = logic.auto_compose(client, manifest, user, node=node)
    return client
