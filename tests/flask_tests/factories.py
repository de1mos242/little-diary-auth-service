from uuid import uuid4

import factory

from auth_api.models import User, InternalUser, GoogleUser


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


class GoogleUserFactory(factory.Factory):
    class Meta:
        model = GoogleUser

    email = factory.Sequence(lambda n: "user%d@mail.com" % n)
    name = factory.Sequence(lambda n: "user name %d" % n)
    family_name = factory.Sequence(lambda n: "user family name %d" % n)
    given_name = factory.Sequence(lambda n: "user given name %d" % n)
    picture = factory.Sequence(lambda n: "user picture url %d" % n)
    google_user_id = factory.Sequence(lambda n: "google user id %d" % n)
    locale = 'en'

    user = factory.SubFactory(UserFactory, username=name)
