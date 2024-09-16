from disnake.ext import commands

from disnake import MessageInteraction

from core.bot import Bot
from core.classes.codenames import Codenames


def check_all_roles(codename: "Codenames"):
    return all(
        [
            codename.blue_operative,
            codename.blue_spymaster,
            codename.red_operative,
            codename.red_spymaster,
        ]
    )


class Events(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    async def join_team(codename: Codenames, team: str, role: str, interaction):
        opposite_team = "red" if team == "blue" else "blue"
        spymaster_attr = f"{team}_spymaster"
        operative_attr = f"{team}_operative"
        opposite_spymaster_attr = f"{opposite_team}_spymaster"
        opposite_operative_attr = f"{opposite_team}_operative"

        if (
            getattr(codename, opposite_spymaster_attr) == interaction.user
            or getattr(codename, opposite_operative_attr) == interaction.user
        ):
            return await interaction.response.send_message(
                f"由於你是{opposite_team}隊成員，因此你無法加入{team}隊!",
                ephemeral=True,
            )

        current_role = getattr(
            codename, spymaster_attr if role == "spymaster" else operative_attr
        )
        if current_role == interaction.user:
            return await interaction.response.send_message(
                f"你已經是{team}隊的{role}了!", ephemeral=True
            )

        if (
            role == "spymaster"
            and getattr(codename, operative_attr) == interaction.user
        ):
            setattr(codename, operative_attr, None)
        elif (
            role == "operative"
            and getattr(codename, spymaster_attr) == interaction.user
        ):
            setattr(codename, spymaster_attr, None)

        setattr(
            codename,
            spymaster_attr if role == "spymaster" else operative_attr,
            interaction.user,
        )

        await interaction.response.send_message(
            f"你作為{role}加入了{team}隊!", ephemeral=True
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
                await self.join_team(codename, "blue", "spymaster", interaction)

            case "join_blue_operative":
                await self.join_team(codename, "blue", "operative", interaction)

            case "join_red_spymaster":
                await self.join_team(codename, "red", "spymaster", interaction)

            case "join_red_operative":
                await self.join_team(codename, "red", "operative", interaction)

            case "randomize_teams":
                codename.randomize_teams()
                await interaction.response.send_message(
                    "隊伍已隨機分配!", ephemeral=True
                )

            case "start_game":
                if not check_all_roles(codename):
                    return await interaction.response.send_message(
                        "所有身分都要有人選，否則無法開始!", ephemeral=True
                    )

                await codename.start(interaction)

            case "reset_team":
                codename.reset_teams()
                await interaction.response.send_message("隊伍已重製", ephemeral=True)

            case _:
                if interaction.user in (codename.blue_spymaster, codename.red_spymaster):
                    return await interaction.response.send_message(
                        "間諜首腦無法給予答案!", ephemeral=True
                    )

                text = interaction.data.custom_id.split("_")[0]
                operative = (
                    codename.red_operative
                    if codename.current_turn == "red"
                    else codename.blue_operative
                )

                if interaction.user != operative:
                    return await interaction.response.send_message(
                        "還不是你的回合!", ephemeral=True
                    )

                if not codename.hint:
                    return await interaction.response.send_message(
                        "在得到線索前，你無法作答！", ephemeral=True
                    )
                return await codename.give_answer(
                    interaction, text, codename.current_turn
                )
        await codename.update_display(message=interaction.message)


def setup(bot):
    bot.add_cog(Events(bot))
