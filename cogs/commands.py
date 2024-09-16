from disnake.ext import commands

from disnake import (
    ApplicationCommandInteraction,
    Option,
    OptionType,
)

from core.bot import Bot


class Commands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.slash_command(name="codenames")
    async def codenames(self, inter):
        pass

    @codenames.sub_command(name="create", description="建立一個新的機密檔案遊戲")
    async def codenames_create(self, interaction: ApplicationCommandInteraction):
        await interaction.response.defer()

        codenames = self.bot.codenames_manager.get(interaction.user)

        if codenames:
            await interaction.response.send_message("Game already exists in this room!")
            return

        codenames = self.bot.codenames_manager.new(interaction.user)

        codenames.join(interaction.user)

        await codenames.update_display(message=await interaction.original_response())

    @codenames.sub_command(name="view_hint_card", description="查看提示卡 (僅供間諜首腦)")
    async def view_hint_card(self, interaction: ApplicationCommandInteraction):
        codename = self.bot.codenames_manager.find_all(interaction.user)

        if interaction.user not in (codename.blue_spymaster, codename.red_spymaster):
            return await interaction.response.send_message(
                "你並非間諜首腦", ephemeral=True
            )

        await interaction.response.send_message(components=codename.answer_components, ephemeral=True)

    @codenames.sub_command(
        name="test",
        description="test command",
    )
    async def test(self, interaction: ApplicationCommandInteraction):
        if interaction.user.id != self.bot.owner_id:
            return await interaction.response.send_message("你不是這個機器人的作者!")
        codename = self.bot.codenames_manager.new(interaction.user)
        codename.blue_spymaster = interaction.user
        codename.join(interaction.user)
        await codename.start(interaction)

    @codenames.sub_command(
        name="switchrole",
        description="admin command",
        options=[
            Option(
                name="role",
                choices=[
                    "blue_spymaster",
                    "blue_operative",
                    "red_spymaster",
                    "red_operative",
                ],
                required=True,
            )
        ],
    )
    async def switchrole(self, interaction: ApplicationCommandInteraction, role: str):
        if interaction.user.id != self.bot.owner_id:
            return await interaction.response.send_message("你不是這個機器人的作者!")
        codename = self.bot.codenames_manager.get(interaction.user.id)
        codename._switch_role(role, interaction.user)
        await codename.update_display(mode="game")
        await interaction.response.send_message("Switched role!", ephemeral=True)

    @codenames.sub_command(
        name="hint",
        description="給予你的隊伍提示",
        options=[
            Option(
                name="word",
                description="提示字詞，請不要直接輸入答案",
                type=OptionType.string,
                required=True,
            ),
            Option(
                name="number",
                description="輸入和幾個詞彙相關的數量",
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
                "你不是當前行動隊伍的間諜首腦", ephemeral=True
            )

        await codename.give_hint(word, number, interaction)
        await interaction.response.send_message("提示給予成功!", ephemeral=True)
        await codename.update_display(mode="game")


def setup(bot):
    bot.add_cog(Commands(bot))
