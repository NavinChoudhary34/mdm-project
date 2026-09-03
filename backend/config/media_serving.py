"""
Serves files under MEDIA_ROOT (uploaded posters/videos) during development,
the same way Django's own django.views.static.serve() does - except this
one actually honors HTTP Range requests.

Why this exists: browsers seek within a <video> by requesting a specific
byte range (an HTTP "Range" header) rather than re-downloading the whole
file. Django's built-in static.serve() has no Range support at all - it
always returns the full file with a 200, no matter what the browser asked
for - so seeking (skip back/forward, dragging the scrub bar) silently does
nothing. This view uses RangedFileResponse (django-ranged-response) to
return a proper 206 Partial Content response with Content-Range headers,
which is what makes video seeking actually work.

Only used when DEBUG=True (see config/urls.py). In production, whatever
serves your media (e.g. S3/Cloudflare R2, or nginx) should already handle
Range requests natively.
"""

import mimetypes
import posixpath
from pathlib import Path

from django.http import Http404
from django.utils._os import safe_join
from ranged_response import RangedFileResponse


def serve_media(request, path, document_root=None):
    path = posixpath.normpath(path).lstrip('/')
    fullpath = Path(safe_join(document_root, path))

    if fullpath.is_dir() or not fullpath.exists():
        raise Http404('"%s" does not exist' % fullpath)

    content_type, encoding = mimetypes.guess_type(str(fullpath))
    content_type = content_type or 'application/octet-stream'

    response = RangedFileResponse(request, fullpath.open('rb'), content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{fullpath.name}"'
    if encoding:
        response['Content-Encoding'] = encoding
    return response
