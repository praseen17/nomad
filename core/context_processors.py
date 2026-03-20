from django.conf import settings


def nomad_context(request):
    """Global context available on all templates."""
    return {
        'FIREBASE_CONFIG': settings.FIREBASE_CONFIG,
        'NOMAD_VERSION': '1.0.0',
    }
