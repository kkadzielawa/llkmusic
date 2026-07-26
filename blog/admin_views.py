from pathlib import Path
from uuid import uuid4

from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_POST


ALLOWED_IMAGE_TYPES = {
    'image/gif': '.gif',
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/webp': '.webp',
}
ALLOWED_AUDIO_TYPES = {
    'audio/mpeg': '.mp3',
    'audio/mp3': '.mp3',
    'audio/ogg': '.ogg',
    'audio/wav': '.wav',
    'audio/x-wav': '.wav',
    'audio/webm': '.webm',
}
MAX_MEDIA_UPLOAD_BYTES = 16 * 1024 * 1024


@staff_member_required
@require_POST
def upload_editor_media(request):
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'error': 'No media file was uploaded.'}, status=400)

    if uploaded_file.size > MAX_MEDIA_UPLOAD_BYTES:
        return JsonResponse({'error': 'Files must be 16 MB or smaller.'}, status=400)

    upload_type = 'image'
    extension = ALLOWED_IMAGE_TYPES.get(uploaded_file.content_type)
    if not extension:
        upload_type = 'audio'
        extension = ALLOWED_AUDIO_TYPES.get(uploaded_file.content_type)
    if not extension:
        return JsonResponse({'error': 'Upload an image or audio file.'}, status=400)

    stem = Path(uploaded_file.name).stem or f'blog-{upload_type}'
    filename = f'{get_valid_filename(stem)}-{uuid4().hex}{extension}'
    saved_path = default_storage.save(f'blog/editor/{upload_type}/{filename}', uploaded_file)
    return JsonResponse({
        'location': default_storage.url(saved_path),
        'type': upload_type,
    })


upload_editor_image = upload_editor_media
