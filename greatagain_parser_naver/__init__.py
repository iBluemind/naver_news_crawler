from raven import Client
import asyncio

from config import SENTRY_DSN
client = Client(SENTRY_DSN)
