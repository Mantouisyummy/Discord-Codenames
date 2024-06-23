from logging import Logger

from disnake.ext.commands import Bot as OriginalBot

from core.classes.codenames_manager import CodenamesManager


class Bot(OriginalBot):
    def __init__(self, logger: Logger, **kwargs):
        super().__init__(**kwargs)

        self.logger = logger
        self.codenames_manager = CodenamesManager(self)

    async def on_ready(self):
        self.logger.info("The bot is ready! Logged in as %s" % self.user)


