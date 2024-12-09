from fakts import base_models, models, enums
from oauth2_provider.generators import generate_client_id, generate_client_secret
from fakts import logic


def create_website_client(
    release: models.Release,
    composition: models.Composition,
    config: base_models.WebsiteClientConfig,
):
    """This function creates a website client. This type of client is used for
    websites that want to register with the lok instance."""

    tenant = config.get_tenant()
    user = None  # is public app so no user

    try:
        client = models.Client.objects.get(
            tenant=tenant, release=release, kind=enums.ClientKindVanilla.WEBSITE.value
        )
        if client.token != config.token:
            client.token = config.token
        client.tenant = tenant
        client.composition = composition
        client.public = config.public
        client.save()

        client.oauth2_client.name = f"@{release.app.identifier}:{release.version}"
        client.oauth2_client.user = None
        client.oauth2_client.client_type = "public"
        client.oauth2_client.algorithm = models.Application.RS256_ALGORITHM
        client.oauth2_client.authorization_grant_type = (
            models.Application.GRANT_AUTHORIZATION_CODE
        )
        client.oauth2_client.redirect_uris = " ".join(config.redirect_uris)
        client.oauth2_client.client_id = client.client_id
        client.oauth2_client.client_secret = client.client_secret
        client.oauth2_client.save()
        return client

    except models.Client.DoesNotExist:
        client_secret = generate_client_secret()
        client_id = generate_client_id()

        oauth2_client = models.Application.objects.create(
            client_type="public",
            algorithm=models.Application.RS256_ALGORITHM,
            name=f"@{release.app.identifier}:{release.version}",
            authorization_grant_type=models.Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=" ".join(config.redirect_uris),
            client_id=client_id,
            client_secret=client_secret,
        )

        return models.Client.objects.create(
            release=release,
            tenant=tenant,
            kind=enums.ClientKindVanilla.WEBSITE.value,
            token=config.token,
            client_id=client_id,
            client_secret=client_secret,
            oauth2_client=oauth2_client,
            redirect_uris=" ".join(config.redirect_uris),
            public=config.public,
            composition=composition,
        )


def create_desktop_client(
    release: models.Release,
    composition: models.Composition,
    config: base_models.WebsiteClientConfig,
):

    tenant = config.get_tenant()
    user = None  # is public app so no user

    try:
        client = models.Client.objects.get(
            tenant=tenant, release=release, kind=enums.ClientKindVanilla.DESKTOP.value
        )
        if client.token != config.token:
            client.token = config.token
        client.tenant = tenant
        client.composition = composition
        client.save()

        client.oauth2_client.name = f"@{release.app.identifier}:{release.version}"
        client.oauth2_client.user = None
        client.oauth2_client.client_type = "public"
        client.oauth2_client.algorithm = models.Application.RS256_ALGORITHM
        client.oauth2_client.authorization_grant_type = (
            models.Application.GRANT_AUTHORIZATION_CODE
        )
        client.oauth2_client.redirect_uris = " ".join(
            ["http://127.0.0.1/", "http://127.0.0.1/callback"]
        )
        client.oauth2_client.client_id = client.client_id
        client.oauth2_client.client_secret = client.client_secret
        client.oauth2_client.save()
        return client

    except models.Client.DoesNotExist:
        client_secret = generate_client_secret()
        client_id = generate_client_id()

        oauth2_client = models.Application.objects.create(
            client_type="public",
            algorithm=models.Application.RS256_ALGORITHM,
            name=f"@{release.app.identifier}:{release.version}",
            authorization_grant_type=models.Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=" ".join(["http://127.0.0.1/", "http://127.0.0.1/callback"]),
            client_id=client_id,
            client_secret=client_secret,
        )

        return models.Client.objects.create(
            release=release,
            tenant=tenant,
            kind=enums.ClientKindVanilla.DESKTOP.value,
            token=config.token,
            client_id=client_id,
            client_secret=client_secret,
            oauth2_client=oauth2_client,
            redirect_uris=" ".join(["http://127.0.0.1/", "http://127.0.0.1/callback"]),
            composition=composition,
        )


def create_development_client(
    release: models.Release,
    composition: models.Composition,
    config: base_models.DevelopmentClientConfig,
):

    tenant = config.get_tenant()
    user = config.get_user()
    print(tenant, user, composition)

    try:
        client = models.Client.objects.get(
            user=user, release=release, kind=enums.ClientKindVanilla.DEVELOPMENT.value
        )
        if client.token != config.token:
            client.token = config.token
        client.tenant = tenant
        client.composition = composition
        client.save()

        client.oauth2_client.name = f"@{release.app.identifier}:{release.version}"
        client.oauth2_client.user = config.get_user()
        client.oauth2_client.client_type = "confidential"
        client.oauth2_client.algorithm = models.Application.RS256_ALGORITHM
        client.oauth2_client.authorization_grant_type = (
            models.Application.GRANT_CLIENT_CREDENTIALS
        )
        client.oauth2_client.redirect_uris = " "
        client.oauth2_client.client_id = client.client_id
        client.oauth2_client.client_secret = client.client_secret
        client.oauth2_client.save()
        return client

    except models.Client.DoesNotExist:
        print("Did not exist", user, release)
        client_secret = generate_client_secret()
        client_id = generate_client_id()

        oauth2_client = models.Application.objects.create(
            user=user,
            client_type="confidential",
            algorithm=models.Application.RS256_ALGORITHM,
            name=f"@{release.app.identifier}:{release.version}",
            authorization_grant_type=models.Application.GRANT_CLIENT_CREDENTIALS,
            redirect_uris="",
            client_id=client_id,
            client_secret=client_secret,
        )

        return models.Client.objects.create(
            release=release,
            user=user,
            tenant=user,
            token=config.token,
            kind=enums.ClientKindVanilla.DEVELOPMENT.value,
            client_id=client_id,
            client_secret=client_secret,
            oauth2_client=oauth2_client,
            redirect_uris="",
            public=False,
            composition=composition,
        )


def create_client(
    manifest: base_models.Manifest,
    config: base_models.ClientConfig,
):
    from .utils import download_logo

    try:
        logo = download_logo(manifest.logo) if manifest.logo else None
    except Exception as e:
        raise ValueError(f"Could not download logo {e}")

    app, _ = models.App.objects.get_or_create(identifier=manifest.identifier)
    release, _ = models.Release.objects.update_or_create(
        app=app,
        version=manifest.version,
        defaults={
            "logo": logo,
            "scopes": manifest.scopes,
            "requirements": manifest.dict()["requirements"],
        },
    )

    composition = logic.auto_create_composition(manifest)

    print(config)

    if config.kind == enums.ClientKindVanilla.WEBSITE.value:
        return create_website_client(release, composition, config)

    if config.kind == enums.ClientKindVanilla.DEVELOPMENT.value:
        return create_development_client(release, composition, config)

    if config.kind == enums.ClientKindVanilla.DESKTOP.value:
        return create_desktop_client(release, composition, config)

    raise NotImplementedError(f"No such client kind {config.kind} exists")
