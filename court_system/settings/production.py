from .base import *

DEBUG = False

# Configure production database, allowed hosts, security headers here
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
