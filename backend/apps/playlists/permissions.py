from rest_framework.permissions import BasePermission


class IsPlaylistOwner(BasePermission):
    """Only the playlist's owner may read or write it. Used on all private-playlist endpoints —
    never trust a playlist id from the client without checking ownership server-side."""

    def has_object_permission(self, request, view, obj):
        # `obj` is either a Playlist (has .user) or a PlaylistMovie (has .playlist.user).
        owner = obj.user if hasattr(obj, 'user') else obj.playlist.user
        return bool(request.user and request.user.is_authenticated and owner_id(owner) == request.user.id)


def owner_id(user_obj):
    return user_obj.id
