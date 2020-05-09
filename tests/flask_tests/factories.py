from uuid import uuid4

import factory

from auth_api.models import User, InternalUser


class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: "user%d" % n)
    external_uuid = factory.LazyFunction(uuid4)


class InternalUserFactory(factory.Factory):
    class Meta:
        model = InternalUser

    login = factory.Sequence(lambda n: "user%d" % n)
    email = factory.Sequence(lambda n: "user%d@mail.com" % n)
    password = "mypwd"
    user = factory.SubFactory(UserFactory, username=login)
