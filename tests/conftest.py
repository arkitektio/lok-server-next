import pytest
import boto3
from moto import mock_aws
import os

from django.contrib.auth import get_user_model
from karakter.models import Organization, User, Membership
from karakter.managers import create_role
from authapp.models import OAuth2Client
from kante.context import HttpContext, UniversalRequest

# Make the factories importable as `pytest` fixtures-adjacent helpers.
from tests import factories  # noqa: F401


@pytest.fixture(autouse=True)
def _reset_ionscale_repo():
    """Give every test a fresh ionscale repository with no leaked state.

    The test settings point ``IONSCALE_REPOSITORY`` at ``FakeIonscaleRepository``,
    so the rebuilt repo is the in-memory fake — no CLI, no binary, no network.
    """
    from ionscale.repo import reset_ionscale_repo

    reset_ionscale_repo()
    yield
    reset_ionscale_repo()


@pytest.fixture
def ionscale_repo():
    """The active (fake) ionscale repository, for seeding data and asserting calls."""
    from ionscale.repo import get_ionscale_repo

    return get_ionscale_repo()


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def s3(aws_credentials):
    with mock_aws():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def create_bucket1(s3):
    s3.create_bucket(Bucket="babanana")


@pytest.fixture
def create_bucket2(s3):
    s3.create_bucket(Bucket="cabanana")


@pytest.fixture
def testing_org(db):
    """An organization owned by ``testuser`` with the default roles.

    Creating the ``User`` triggers the signal that builds a personal default
    organization; creating the ``Organization`` with an owner triggers the
    signal that seeds default roles/scopes and makes the owner an admin.
    """
    user = User.objects.create(username="testuser", password="testpass")
    org = Organization.objects.create(slug="testorg", name="Test Org", owner=user)
    # ``ensure_owner_is_admin`` (org post_save signal) already added the admin
    # role; this keeps the helper explicit/idempotent for readers.
    membership = Membership.objects.get(user=user, organization=org)
    membership.roles.add(create_role(organization=org, identifier="admin"))
    return org


def create_auth_context(user: User, organization: Organization, client: OAuth2Client) -> HttpContext:
    return HttpContext(
        request=UniversalRequest(
            _extensions={"token": "token"},
            _client=client,  # type: ignore
            _user=user,  # type: ignore
            _organization=organization,  # type: ignore
        ),
        headers={"Authorization": "Bearer token"},
        type="http",
    )


@pytest.fixture
def authenticated_context(db, testing_org) -> HttpContext:
    user = User.objects.create(username="fart", password="123456789")
    membership, _ = Membership.objects.get_or_create(user=user, organization=testing_org)
    client = OAuth2Client.objects.create(client_id="oinsoins", membership=membership)
    return create_auth_context(user, testing_org, client)
