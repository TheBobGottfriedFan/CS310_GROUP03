import os
from django.core.wsgi import get_wsgi_application
#patientportalsystems.settings can be replaced by the name of the folder then .settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'patientportalsystem.settings')
application = get_wsgi_application()
