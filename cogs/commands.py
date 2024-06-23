from disnake.ext import commands

from disnake import (
    ApplicationCommandInteraction,
    ButtonStyle,
    Embed,
    Colour,
    Option,
    OptionType,
)

from disnake.ui import Button, ActionRow

from core.bot import Bot
from core.embeds import SuccessEmbed

import random


class Commands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.slash_command(name="codenames")
    async def codenames(self, inter):
        pass

    @codenames.sub_command(name="create", description="create a new game of codenames")
    async def codenames_create(self, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()

        room_id = random.randint(100000, 999999)
        codenames = self.bot.codenames_manager.get(room_id)

        if codenames:
            await interaction.response.send_message("Game already exists in this room!")
            return

        codenames = self.bot.codenames_manager.new(room_id)

        codenames.join(interaction.user)

        await codenames.update_display(message=await interaction.original_response())

    @codenames.sub_command(
        name="join",
        description="join a game of codenames",
        options=[
            Option(
                name="room_id",
                description="The room id of the game",
                type=OptionType.integer,
                required=True,
            )
        ],
    )
    async def join(self, interaction: ApplicationCommandInteraction, room_id: int):
        codenames = self.bot.codenames_manager.get(room_id)
        if codenames is None:
            return await interaction.response.send_message("Room not found!")

        await interaction.response.defer()

        codenames.join(interaction.user)
        await interaction.edit_original_response(
            embed=SuccessEmbed("You have joined the game!")
        )
        await codenames.update_display(message=(await interaction.original_response()))

    @codenames.sub_command(
        name="test",
        description="test command",
    )
    async def test(self, interaction: ApplicationCommandInteraction):
        if interaction.user.id != self.bot.owner_id:
            return await interaction.response.send_message(
                "You are not the owner of the bot!"
            )
        codename = self.bot.codenames_manager.new(000000)
        codename.blue_spymaster = interaction.user
        codename.join(interaction.user)
        await codename.start(interaction)

    @codenames.sub_command(
        name="switchrole",
        description="admin command",
        options=[
            Option(
                name="role",
                choices=["blue_spymaster", "blue_operative", "red_spymaster", "red_operative"],
                required=True
            )
        ]
    )
    async def switchrole(self, interaction: ApplicationCommandInteraction, role: str):
        if interaction.user.id != self.bot.owner_id:
            return await interaction.response.send_message(
                "You are not the owner of the bot!"
            )
        codename = self.bot.codenames_manager.get(000000)
        codename._switch_role(role, interaction.user)
        await codename.update_display(mode="game")
        await interaction.response.send_message("Switched role!", ephemeral=True)

    @codenames.sub_command(
        name="hint",
        description="give a hint to your team",
        options=[
            Option(
                name="word",
                description="The word you want to give a hint for",
                type=OptionType.string,
                required=True,
            ),
            Option(
                name="number",
                description="The number of words the hint applies to",
                type=OptionType.integer,
                choices={str(i): i for i in range(1, 10)},
                required=True,
            ),
        ],
    )
    async def hint(
        self,
        interaction: ApplicationCommandInteraction,
        word: str,
        number: int,
    ):
        codename = self.bot.codenames_manager.find_all(interaction.user)

        if codename.current_spymaster != interaction.user:
            return await interaction.response.send_message(
                "You are not the spymaster!", ephemeral=True
            )

        await codename.give_hint(word, number, interaction)
        await interaction.response.send_message("Hint given!", ephemeral=True)
        await codename.update_display(mode="game")

def setup(bot):
    bot.add_cog(Commands(bot))
