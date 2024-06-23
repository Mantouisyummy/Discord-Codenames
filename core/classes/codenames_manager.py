from typing import TYPE_CHECKING, Dict

from disnake import Member

from core.classes.codenames import Codenames

if TYPE_CHECKING:
    from core.bot import Bot

class CodenamesManager:
    def __init__(self, bot: "Bot"):
        self.bot = bot
        self.games: Dict[int, "Codenames"] = {}

    def new(
            self,
            room_id: int
        ) -> "Codenames":

        if room_id in self.games:
            return self.games[room_id]

        self.games[room_id] = codenames = Codenames(room_id)

        self.bot.logger.debug('Created CodeNames Game with RoomId %d ', room_id)

        return codenames

    def get(self, room_id: int) -> "Codenames":
        return self.games.get(room_id, None)

    def find_all(self, member: Member) -> "Codenames":
        return [game for game in self.games.values() if member in game.players][0]