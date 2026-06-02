from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from authapp.models import OAuth2Client
from fakts.models import Client as FaktsClient
from karakter.models import Membership, Organization


User = get_user_model()


class OrganizationOAuthClientCleanupTests(TestCase):
    def test_deleting_organization_deletes_membership_oauth_clients(self):
        owner = User.objects.create_user(username="owner", password="secret")
        organization = Organization.objects.create(
            owner=owner,
            slug="demo-org",
            name="Demo Org",
        )
        membership = Membership.objects.get(user=owner, organization=organization)
        oauth_client = OAuth2Client.objects.create(
            membership=membership,
            client_id="client-id",
            client_secret="client-secret",
        )

        organization.delete()

        self.assertFalse(OAuth2Client.objects.filter(pk=oauth_client.pk).exists())


class TokenEndpointHardeningTests(TestCase):
    def test_client_credentials_with_orphaned_client_returns_invalid_client(self):
        oauth_client = OAuth2Client.objects.create(
            client_id="orphan-client-id",
            client_secret="orphan-client-secret",
        )

        response = self.client.post(
            reverse("token"),
            {
                "grant_type": "client_credentials",
                "client_id": oauth_client.client_id,
                "client_secret": oauth_client.client_secret,
            },
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_client")

    def test_deleting_organization_deletes_fakts_client_oauth_clients(self):
        owner = User.objects.create_user(username="owner2", password="secret")
        organization = Organization.objects.create(
            owner=owner,
            slug="demo-org-2",
            name="Demo Org 2",
        )
        oauth_client = OAuth2Client.objects.create(
            client_id="client-id-2",
            client_secret="client-secret-2",
        )
        FaktsClient.objects.create(
            oauth2_client=oauth_client,
            organization=organization,
            user=owner,
            tenant=owner,
            requirements_hash="",
        )

        organization.delete()

        self.assertFalse(OAuth2Client.objects.filter(pk=oauth_client.pk).exists())
