"""P14 · Each person's interface lives on the server, only for them."""

import pytest
from django.db import DatabaseError, transaction
from rest_framework.exceptions import APIException

from backend.tests.integration.test_shot09_documentary import (
    as_user,
    documentary_tenant as documentary_tenant,
)
from projects import interface

pytestmark = pytest.mark.rls_integration


def test_preferences_merge_and_stay_with_their_person(documentary_tenant):
    org, other, users, outsider = documentary_tenant
    with as_user(users["INSTALLER"]):
        assert interface.get_preferences(org, users["INSTALLER"]) == interface.DEFAULTS
        interface.save_preferences(org, users["INSTALLER"], {"density": "workshop"})
        saved = interface.save_preferences(org, users["INSTALLER"], {"text_size": "large"})
        assert saved == {**interface.DEFAULTS, "density": "workshop", "text_size": "large"}
        with pytest.raises(APIException):
            interface.save_preferences(org, users["INSTALLER"], {"accent": "pink"})
    with as_user(users["OWNER"]):
        # Another person in the same workshop sees only their own defaults.
        assert interface.get_preferences(org, users["INSTALLER"]) == interface.DEFAULTS
        assert interface.get_preferences(org, users["OWNER"]) == interface.DEFAULTS
    with as_user(outsider):
        with pytest.raises(DatabaseError), transaction.atomic():
            interface.save_preferences(org, outsider, {"density": "workshop"})
