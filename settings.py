# Settings for this app.

settings = dict(
    
    # You probably don't need to mess with these settings.
    http_host = 'localhost',
    http_port = 8080,
    mongo_host = 'localhost',
    mongo_port = 27017,
)

try:
    # pull in settings_local if it exists
    from settings_local import settings as s
    settings.update(s)
except ImportError:
    pass
