"""Shared authorization for the device-code `decline_*` mutations.

All four `decline_*_device_code` mutations took a device code by primary key and
set `denied = True` with no check beyond "is authenticated". Primary keys are
sequential, so any authenticated account could walk them and deny every pending
device, service, hub or mesh enrolment in the deployment.

The legitimate caller always holds the *code* — it is what the device displayed
and what the configure URL carries (`/configure/{code}`), and the SPA looks the
id up from it via `deviceCodeByCode`. Requiring the code as proof turns an
enumerable id into an unguessable capability, which is the property the accept
path gets from `assert_member`.

`code` is required: an id-only decline was accepted (with a warning) while the
deployed SPA still sent only the id; that fallback is gone, which is what
actually closes the enumeration.
"""

import logging

from graphql import GraphQLError

from api.management.authz import DENIED

logger = logging.getLogger(__name__)


def resolve_declinable_device_code(model, *, device_code_id, code):
    """Fetch a device code for declining, requiring proof-of-possession.

    ``code`` must match the stored code, so a caller who guessed an id cannot
    deny someone else's enrolment.
    """
    try:
        instance = model.objects.get(id=device_code_id)
    except model.DoesNotExist:
        raise GraphQLError(DENIED)

    if code is None or instance.code != code:
        raise GraphQLError(DENIED)

    return instance
