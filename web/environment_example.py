import os

os.environ['SQUID_BOT_CLIENT_ID'] = "" # The Client ID from Discord
os.environ['SQUID_BOT_DATABASE_ENGINE'] = "django.db.backends.sqlite3" # Which django database enjine would you like?
os.environ['SQUID_BOT_DATABASE_HOST'] = "" # If a host is required
os.environ['SQUID_BOT_DATABASE_PORT'] = "" # If a port is required
os.environ['SQUID_BOT_DATABASE_NAME'] = "squidbot.db" # If a database name is required
os.environ['SQUID_BOT_DATABASE_USERNAME'] = "" # If a database username is required
os.environ['SQUID_BOT_DATABASE_PASSWORD'] = "" # If a database password is required
os.environ['SQUID_BOT_DEBUG_MODE'] = "true" # Only "false" disables debug mode
os.environ['SQUID_BOT_DJANGO_SECRET'] = "secret123" # A secret key only known to you and Django
os.environ['SQUID_BOT_EMAIL_PASSWORD'] = "" # Password to use when sending emails from django
os.environ['SQUID_BOT_OWNER_ID'] = "131224383640436736" # Replace with your own Discord ID
os.environ['SQUID_BOT_TOKEN'] = "" # The Token from Discord 
