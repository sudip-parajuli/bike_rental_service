
from decouple import config

# Default to local settings if not specified
if config('DJANGO_ENV', default='local') == 'production':
    from .production import *
else:
    from .local import *
