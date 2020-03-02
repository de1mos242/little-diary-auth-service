from uuid import uuid4

import factory
from pytest_factoryboy import register

from auth_api.models import User


@register
class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: "user%d" % n)
    email = factory.Sequence(lambda n: "user%d@mail.com" % n)
    password = "mypwd"
    external_uuid = factory.LazyFunction(uuid4)
