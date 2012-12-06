from os import path

# tornado specific
torn_settings = dict(
    port = 6488,
    db_name = "",
    db_uri  = "",
    db_user = "",
    db_pass = "",
    mongo_db = 'Two_Pick_Too_Drunk',
    mongo_host = 'localhost',
    mongo_port = 27017,
    login_url="/auth/login",
    static_path = path.join(path.dirname(__file__), "tornapp/static"),
    template_path = path.join(path.dirname(__file__), "tornapp/templates"),
    cookie_secret = "SOMETHING HERE",
    debug = False,
    debug_pdb = False,
)

try:
    # pull in settings_local if it exists
    from settings_local import settings as s
    settings.update(s)
except ImportError:
    pass

try:
    from settings_prod import torn_settings as ts
except:
    from settings_dev import torn_settings as ts
torn_settings.update(ts)

