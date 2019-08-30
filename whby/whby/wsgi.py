"""
WSGI config for whby project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

setting_name = os.environ.get("SETTING_NAME") or "dev"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whby.settings.' + setting_name)

application = get_wsgi_application()
