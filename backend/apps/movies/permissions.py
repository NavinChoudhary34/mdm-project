from rest_framework.permissions import SAFE_METHODS, BasePermission


class MoviePermission(BasePermission):
    """
    Permissions for movies.

    GET:
        - Anyone can view catalog movies.
        - Anyone can view public uploaded movies.
        - Authenticated users can view their own private movies.

    POST:
        - Any authenticated user can create/upload a movie.

    PUT/PATCH/DELETE:
        - Only the owner of an uploaded movie can modify/delete it.
        - Catalog/TMDB movies (owner=None) cannot be modified/deleted by users.
    """

    def has_permission(self, request, view):
        # Anyone can browse movies.
        if request.method in SAFE_METHODS:
            return True

        # Creating/updating/deleting requires authentication.
        return bool(
            request.user
            and request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        # Reading:
        # queryset filtering in views.py already controls which movies
        # are visible. If the object reached this point, allow reading.
        if request.method in SAFE_METHODS:
            return True

        # Only the owner can modify/delete their uploaded movie.
        if obj.owner is None:
            return False

        return obj.owner == request.user