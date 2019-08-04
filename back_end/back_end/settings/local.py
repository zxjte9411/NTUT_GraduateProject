from .base import *

SECRET_KEY = "w+x!%38z*inmj#bin7$(@hf7i@6&b%fgm4wz+=cd)c_7rst_$*"

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(BASE_DIR), 'Django_db.sqlite3'),
    }
}