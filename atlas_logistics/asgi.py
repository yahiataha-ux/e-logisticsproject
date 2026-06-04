"""
ASGI config for atlas_logistics project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import sys
from pathlib import Path

# Add the parent directory (django_app) to the Python path so atlas_logistics is importable
sys.path.append(str(Path(__file__).resolve().parent.parent))

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atlas_logistics.settings')

application = get_asgi_application()
app = application

