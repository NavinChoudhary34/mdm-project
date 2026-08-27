from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """
    Lets users authenticate with either their username or their email address
    in the same "username" field the login endpoint accepts.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        try:
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # Extremely unlikely given the unique constraints, but fail closed.
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
