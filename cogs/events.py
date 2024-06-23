from disnake.ext import commands

from disnake import MessageInteraction, ButtonStyle

from core.bot import Bot
from core.classes.codenames import Codenames


class Events(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    def check_all_roles(self, codename: "Codenames"):
        return all(
            [
                codename.blue_operative,
                codename.blue_spymaster,
                codename.red_operative,
                codename.red_spymaster,
            ]
        )

    @commands.Cog.listener()
    async def on_message_interaction(self, interaction: MessageInteraction):
        codename = self.bot.codenames_manager.get(
            int(interaction.data.custom_id.split("_")[-1])
        )

        if interaction.user not in codename.players:
            await interaction.response.send_message(
                "You are not in this game!", ephemeral=True
            )
            return

        custom_id = interaction.data.custom_id[: interaction.data.custom_id.rfind("_")]

        match custom_id:
            case "join_blue_spymaster":
                if (codename.red_spymaster or codename.red_operative) == interaction.user:
                    await interaction.response.send_message(
                        "You cannot join the red team as the spymaster if you are the blue team!",
                        ephemeral=True,
                    )
                    return

                if codename.blue_spymaster == interaction.user:
                    return await interaction.response.send_message(
                        "You already is the spymaster!", ephemeral=True
                    )

                if codename.blue_operative == interaction.user:
                    codename.blue_operative = None

                codename.blue_spymaster = interaction.user
                await interaction.response.send_message(
                    "You have joined the blue team as the spymaster!", ephemeral=True
                )
            case "join_blue_operative":
                if (codename.red_spymaster or codename.red_operative) == interaction.user:
                    await interaction.response.send_message(
                        "You cannot join the red team as the operative if you are the blue team!",
                        ephemeral=True,
                    )
                    return

                if codename.blue_operative == interaction.user:
                    return await interaction.response.send_message(
                        "You already is the operative!", ephemeral=True
                    )

                if codename.blue_spymaster == interaction.user:
                    codename.blue_spymaster = None

                codename.blue_operative = interaction.user
                await interaction.response.send_message(
                    "You have joined the blue team as an operative!", ephemeral=True
                )
            case "join_red_spymaster":
                if (codename.blue_spymaster or codename.blue_operative) == interaction.user:
                    await interaction.response.send_message(
                        "You cannot join the red team as the spymaster if you are the blue team!",
                        ephemeral=True,
                    )
                    return

                if codename.red_spymaster == interaction.user:
                    return await interaction.response.send_message(
                        "You already is the spymaster!", ephemeral=True
                    )

                if codename.red_operative == interaction.user:
                    codename.red_operative = None

                codename.red_spymaster = interaction.user
                await interaction.response.send_message(
                    "You have joined the red team as the spymaster!", ephemeral=True
                )
            case "join_red_operative":
                if (codename.blue_spymaster or codename.blue_operative) == interaction.user:
                    await interaction.response.send_message(
                        "You cannot join the red team as the operative if you are the blue team!",
                        ephemeral=True,
                    )
                    return

                if codename.red_operative == interaction.user:
                    return await interaction.response.send_message(
                        "You already is the spymaster!", ephemeral=True
                    )

                if codename.red_spymaster == interaction.user:
                    codename.red_spymaster = None

                codename.red_operative = interaction.user
                await interaction.response.send_message(
                    "You have joined the red team as an operative!", ephemeral=True
                )
            case "randomize_teams":
                if self.check_all_roles(codename):
                    return await interaction.response.send_message(
                        "All roles are already filled!", ephemeral=True
                    )

                codename.randomize_teams()
                await interaction.response.send_message("Teams have been randomize!", ephemeral=True)

            case "start_game":
                if not self.check_all_roles(codename):
                    return await interaction.response.send_message(
                        "All roles must be filled before starting the game!", ephemeral=True
                    )

                await codename.start(interaction)

            case "reset_team":
                codename.reset_teams()
                await interaction.response.send_message("Teams have been reset!", ephemeral=True)

            case _:
                if (codename.blue_spymaster or codename.red_spymaster) == interaction.user:
                    return await interaction.response.send_message(
                        "You cannot give answers as a spymaster!", ephemeral=True
                )

                text = interaction.data.custom_id.split("_")[0]
                match codename.current_turn:
                    case "red":
                        if interaction.user != codename.red_operative:
                            return await interaction.response.send_message(
                                "It is not your turn!", ephemeral=True
                        )

                        if not codename.hint:
                            return await interaction.response.send_message(
                                "You won't be able to give an answer until there's a hint!", ephemeral=True
                        )
                    case "blue":
                        if interaction.user != codename.blue_operative:
                            return await interaction.response.send_message(
                                "It is not your turn!", ephemeral=True
                        )

                        if not codename.hint:
                            return await interaction.response.send_message(
                                "You won't be able to give an answer until there's a hint!", ephemeral=True
                        )
                return await codename.give_answer(interaction, text, interaction.user, codename.current_turn)
        await codename.update_display(message=interaction.message)


def setup(bot):
    bot.add_cog(Events(bot))
