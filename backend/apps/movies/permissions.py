from rest_framework.permissions import SAFE_METHODS, BasePermission


class MoviePermission(BasePermission):
    """
    Movie permissions:

    - Anyone can perform safe/read-only requests.
    - Authenticated users can create movies.
    - Only the owner of a movie can update/delete it.
    - Staff users can manage any movie.
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
        # Anyone can view a movie that the view allows them to see.
        if request.method in SAFE_METHODS:
            return True

        # Staff can manage any movie.
        if request.user.is_staff:
            return True

        # Normal users can only modify/delete their own movies.
        return obj.owner_id == request.user.id