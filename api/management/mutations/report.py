import logging

import strawberry
from kante.types import Info

from fakts import models as fakts_models
from api.management import types
from api.management.authz import assert_member, get_or_denied

logger = logging.getLogger(__name__)


@strawberry.input
class ResolveReportInput:
    id: strawberry.ID
    note: str | None = None


def resolve_report(info: Info, input: ResolveReportInput) -> types.ManagementReport:
    """Acknowledge a client report.

    This is triage, not repair: it deliberately leaves `client.functional` alone,
    so the record of what the client actually said is preserved. What it changes
    is attention — resolving a client's *latest* report takes it off the
    dashboard's "apps reporting problems" list until the client reports again.

    Any member of the owning organization may acknowledge, since any member can
    already see the report.
    """
    report = get_or_denied(fakts_models.Report.objects, pk=input.id)
    assert_member(info, report.client.organization)
    report.resolve(info.context.request.user, input.note)
    return report


@strawberry.input
class UnresolveReportInput:
    id: strawberry.ID


def unresolve_report(info: Info, input: UnresolveReportInput) -> types.ManagementReport:
    """Reopen an acknowledged report, putting the client back on the action list
    if this is its latest report."""
    report = get_or_denied(fakts_models.Report.objects, pk=input.id)
    assert_member(info, report.client.organization)
    report.unresolve()
    return report
