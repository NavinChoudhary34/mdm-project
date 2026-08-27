from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model. We extend AbstractUser (rather than AbstractBaseUser) so we
    keep Django's battle-tested username/password/permissions machinery, but we
    enforce a unique email since login is allowed via email OR username.
    """
    email = models.EmailField(unique=True)

    # Small profile extension — kept on the User model itself since it's 1:1 and
    # simple; a separate Profile model would be overkill for these two fields.
    bio = models.TextField(blank=True, default='')
    avatar_url = models.URLField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username
