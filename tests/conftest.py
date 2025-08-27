import pytest
import boto3
import moto
from moto import mock_aws
import os
import django
from django.conf import settings

from karakter.signals import create_role


# Configure Django settings for tests
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rekuest.settings_test')
    django.setup()



from django.contrib.auth import get_user_model
from karakter.models import  Organization, User, Membership, Role
from authapp.models import OAuth2Client
from lok_server.schema import schema
from kante.context import HttpContext, UniversalRequest

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

    user = User.objects.create(username="testuser", password="testpass")

    org = Organization.objects.create(slug="testorg")


    x = Membership.objects.create(user=user, organization=org)
    x.roles.add(create_role(identifier="admin", organization=org))
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
        type="http"
    )


@pytest.fixture
def authenticated_context(db, testing_org):
    user = User.objects.create(username="fart", password="123456789")
    client = OAuth2Client.objects.create(client_id="oinsoins", organization=testing_org, user=user)

    return create_auth_context(user, testing_org, client)
