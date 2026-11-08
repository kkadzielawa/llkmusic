"""Database-backed limits for public endpoints that send email."""

import ipaddress
import json
import math
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .models import SubmissionGuard


MAX_PUBLIC_SUBMISSION_BYTES = 64 * 1024


class SubmissionRejected(Exception):
    def __init__(self, message, status=429, retry_after=None):
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after


def _key(*parts):
    # Never store the visitor's raw IP address, email, message, or token here.
    return salted_hmac(
        'pages.public-submissions', json.dumps(parts, sort_keys=True), algorithm='sha256',
    ).hexdigest()


def client_address(request):
    address = request.META.get('REMOTE_ADDR', '')
    if settings.TRUST_PROXY_IP:
        address = request.META.get('HTTP_X_REAL_IP') or address
    try:
        parsed = ipaddress.ip_address(address)
        if parsed.version == 6:
            return str(ipaddress.ip_network(f'{parsed}/64', strict=False))
        return str(parsed)
    except ValueError:
        return 'unknown'


def _limit(identity, kind, limit, window):
    now = timezone.now()
    bucket = int(now.timestamp()) // window
    expires_at = now + timedelta(seconds=(bucket + 1) * window - now.timestamp())
    key = _key(kind, identity, bucket)
    guard, _ = SubmissionGuard.objects.get_or_create(
        key=key, defaults={'expires_at': expires_at},
    )
    # A conditional UPDATE stays atomic across Gunicorn workers and threads.
    if not SubmissionGuard.objects.filter(key=key, hits__lt=limit).update(hits=F('hits') + 1):
        raise SubmissionRejected(
            'Too many submissions. Please try again later.',
            retry_after=max(1, math.ceil((guard.expires_at - now).total_seconds())),
        )


def limit_public_request(request):
    if int(request.META.get('CONTENT_LENGTH') or 0) > MAX_PUBLIC_SUBMISSION_BYTES:
        raise SubmissionRejected('This submission is too large. Please shorten it and try again.', status=413)
    # Bound cleanup work; expired rows are never needed for enforcement.
    expired = list(SubmissionGuard.objects.filter(
        expires_at__lte=timezone.now(),
    ).values_list('key', flat=True)[:100])
    if expired:
        SubmissionGuard.objects.filter(key__in=expired).delete()
    _limit(
        client_address(request), 'ip',
        settings.PUBLIC_FORM_IP_LIMIT, settings.PUBLIC_FORM_IP_WINDOW,
    )


def claim_submission(scope, token, payload, email):
    _limit(
        email.strip().casefold(), 'email',
        settings.PUBLIC_FORM_EMAIL_LIMIT, settings.PUBLIC_FORM_EMAIL_WINDOW,
    )
    now = timezone.now()
    claims = [
        (_key('token', scope, token), settings.PUBLIC_FORM_MAX_SECONDS),
        (_key('duplicate', scope, payload), settings.PUBLIC_FORM_DUPLICATE_SECONDS),
    ]
    with transaction.atomic():
        for key, lifetime in claims:
            # Expiry is checked here too, even if request cleanup was bounded.
            SubmissionGuard.objects.filter(key=key, expires_at__lte=now).delete()
            _, created = SubmissionGuard.objects.get_or_create(
                key=key, defaults={'expires_at': now + timedelta(seconds=lifetime)},
            )
            if not created:
                raise SubmissionRejected(
                    'This submission has already been received. Please avoid sending it again.',
                    status=409,
                )
    return [key for key, _ in claims]


def release_submission(keys):
    """Allow a genuine retry when contact email delivery fails."""
    SubmissionGuard.objects.filter(key__in=keys).delete()
