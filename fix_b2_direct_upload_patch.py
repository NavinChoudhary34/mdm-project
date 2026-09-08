#!/usr/bin/env python3
"""
Fix the Claude B2 direct-upload patch for the current Movie Playlist Manager.

Run this from the PROJECT ROOT (folder containing backend/ and frontend/):

    python fix_b2_direct_upload_patch.py

It fixes the mismatches currently present in the project:
1. frontend/lib/endpoints.ts:
   Adds moviesApi.presignVideoUpload(), which the Add Movie page calls.

2. backend/apps/movies/urls.py:
   Registers /api/movies/presign/ for PresignVideoUploadView.

3. backend/apps/movies/serializers.py:
   Accepts video_file_key instead of requiring the 890 MB file in the
   Django multipart request, and maps that key to Movie.video_file.

The script creates .bak files before changing anything.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import sys


def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    sys.exit(1)


def backup(path: Path) -> None:
    backup = Path(str(path) + ".bak")
    if not backup.exists():
        shutil.copy2(path, backup)
        print(f"  backup: {backup}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count == 0:
        fail(f"Could not find expected block for {label}.")
    if count != 1:
        fail(f"Expected 1 match for {label}, found {count}.")
    return text.replace(old, new, 1)


def patch_endpoints(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text

    if "presignVideoUpload:" not in text:
        anchor = """  genres: () => api.get<Genre[]>('/movies/genres/'),

"""
        addition = """  presignVideoUpload: (filename: string, content_type?: string) =>
    api.post<{
      upload_url: string;
      key: string;
    }>('/movies/presign/', {
      filename,
      content_type: content_type || 'application/octet-stream',
    }),

"""
        text = replace_once(
            text,
            anchor,
            anchor + addition,
            "frontend moviesApi genres anchor",
        )

    if text != original:
        backup(path)
        path.write_text(text, encoding="utf-8", newline="\n")
        return True
    return False


def patch_urls(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text

    if "PresignVideoUploadView" not in text:
        old = """from .views import GenreListView, MovieDetailView, MovieListCreateView, MyMoviesView
"""
        new = """from .views import GenreListView, MovieDetailView, MovieListCreateView, MyMoviesView
from .presign import PresignVideoUploadView
"""
        text = replace_once(text, old, new, "movies/urls.py imports")

    if "name='movie-presign'" not in text:
        anchor = """urlpatterns = [
    path('', MovieListCreateView.as_view(), name='movie-list'),
"""
        addition = """    path(
        'presign/',
        PresignVideoUploadView.as_view(),
        name='movie-presign'
    ),
"""
        text = replace_once(
            text,
            anchor,
            """urlpatterns = [
    path('', MovieListCreateView.as_view(), name='movie-list'),
"""
            + addition,
            "movies/urls.py urlpatterns anchor",
        )

    if text != original:
        backup(path)
        path.write_text(text, encoding="utf-8", newline="\n")
        return True
    return False


def patch_serializers(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text

    old_field = """    video_file = serializers.FileField(
        required=False,
        allow_null=True
    )

"""
    new_field = """    # The browser uploads the large video directly to B2.
    # Django receives only the B2 object key.
    video_file_key = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

"""
    if "video_file_key = serializers.CharField(" not in text:
        text = replace_once(
            text,
            old_field,
            new_field,
            "MovieWriteSerializer video_file field",
        )

    # Add the field to Meta.fields immediately after video_file removal.
    old_fields = """            # Uploaded video
            'video_file',

            # Private/public
"""
    new_fields = """            # Uploaded video
            'video_file_key',

            # Private/public
"""
    if old_fields in text:
        text = text.replace(old_fields, new_fields, 1)

    # Add create/update logic to the serializer.
    # This makes the key become the actual FileField value.
    class_marker = """    class Meta:
        model = Movie
"""
    helper = """    def _save_video_key(self, validated_data):
        video_key = validated_data.pop('video_file_key', None)

        if video_key:
            validated_data['video_file'] = video_key

        return validated_data

    def create(self, validated_data):
        validated_data = self._save_video_key(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data = self._save_video_key(validated_data)
        return super().update(instance, validated_data)

"""
    if "_save_video_key" not in text:
        text = replace_once(
            text,
            class_marker,
            helper + class_marker,
            "MovieWriteSerializer create/update insertion",
        )

    if text != original:
        backup(path)
        path.write_text(text, encoding="utf-8", newline="\n")
        return True
    return False


def main() -> None:
    root = Path.cwd()

    if not (root / "backend").is_dir() or not (root / "frontend").is_dir():
        fail(
            "Run this script from your project root "
            "(it must contain backend/ and frontend/)."
        )

    required = [
        "backend/apps/movies/presign.py",
        "backend/apps/movies/urls.py",
        "backend/apps/movies/serializers.py",
        "frontend/lib/endpoints.ts",
        "frontend/app/(app)/movies/add/page.tsx",
    ]

    for rel in required:
        if not (root / rel).is_file():
            fail(f"Missing expected file: {rel}")

    changed = 0

    print("Applying B2 direct-upload compatibility fixes...")
    print()

    if patch_endpoints(root / "frontend/lib/endpoints.ts"):
        print("✓ frontend/lib/endpoints.ts")
        changed += 1
    else:
        print("• frontend/lib/endpoints.ts already fixed")

    if patch_urls(root / "backend/apps/movies/urls.py"):
        print("✓ backend/apps/movies/urls.py")
        changed += 1
    else:
        print("• backend/apps/movies/urls.py already fixed")

    if patch_serializers(root / "backend/apps/movies/serializers.py"):
        print("✓ backend/apps/movies/serializers.py")
        changed += 1
    else:
        print("• backend/apps/movies/serializers.py already fixed")

    print()
    print(f"Done. Changed {changed} file(s).")
    print()
    print("Recommended local checks:")
    print("  Frontend:  cd frontend && npm run build")
    print("  Backend:   cd backend && python manage.py check")
    print()
    print("After deployment, verify:")
    print("  POST /api/movies/presign/")
    print("  PUT <returned B2 URL>")
    print("  POST /api/movies/ with video_file_key=<returned key>")
    print()
    print("Backups are saved as *.bak.")


if __name__ == "__main__":
    main()
