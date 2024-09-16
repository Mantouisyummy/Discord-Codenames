from typing import TYPE_CHECKING, Dict

from disnake import Member

from core.classes.codenames import Codenames

if TYPE_CHECKING:
    from core.bot import Bot


class CodenamesManager:
    def __init__(self, bot: "Bot"):
        self.bot = bot
        self.games: Dict[int, "Codenames"] = {}

    def new(self, owner: Member) -> "Codenames":
        if owner.id in self.games:
            return self.games[owner.id]

        self.games[owner.id] = codenames = Codenames(owner)

        self.bot.logger.debug("Created CodeNames Game with UserID %d ", owner.id)

        return codenames

    def get(self, user_id: int) -> "Codenames":
        return self.games.get(user_id, None)

    def find_all(self, user: Member) -> "Codenames":
        return [game for game in self.games.values() if user in game.players][0]
