import random
from typing import Literal, Optional

from disnake import (
    Member,
    ApplicationCommandInteraction,
    MessageInteraction,
    ButtonStyle,
    Embed,
    Message,
    Colour,
)
from disnake.ui import Button, ActionRow

from core.classes.codenames_view import CodenamesView
from core.embeds import WarningEmbed, CodenamesEmbed
from core.types.answer import Answer

TEAM = Literal["blue", "red"]


class Codenames:
    def __init__(
        self,
        room_id: int,
    ):
        self.room_id = room_id
        self.message = None
        self.view: CodenamesView = None
        self.blue_operative = None
        self.blue_spymaster = None
        self.red_operative = None
        self.red_spymaster = None
        self.players = []

        self.current_turn: TEAM = random.choice(["blue", "red"])
        self.current_spymaster = None

        self.words = []
        self.blue_words = []
        self.red_words = []
        self.neutral_words = []
        self.assassin = None

        self.board = []
        self._red_count = 0
        self._blue_count = 0

        # hint
        self.word = None
        self.number = 0
        self.hint = False

        # answer components
        self.answer_components = None

    def __set_words(self):
        with open("words.txt", "r", encoding="utf-8") as f:
            self.words = random.sample(f.read().splitlines(), 25)

        self.blue_words = random.sample(
            self.words, 9 if self.current_turn == "blue" else 8
        )

        remaining_items = list(set(self.words) - set(self.blue_words))
        self.red_words = random.sample(
            remaining_items, 9 if self.current_turn == "red" else 8
        )

        remaining_items = list(set(remaining_items) - set(self.red_words))
        self.neutral_words = random.sample(remaining_items, 7)

        remaining_items = list(set(remaining_items) - set(self.neutral_words))
        self.assassin = random.choice(remaining_items)

    def __create_board(self):
        self.__set_words()

        self.board = [[self.words[i * 5 + j] for j in range(5)] for i in range(5)]

    def bleed_board(self):
        self.answer_components = [
            Button(
                label=self.board[i][j],
                custom_id=f"{self.board[i][j]}_bleed_{self.room_id}",
                style=(
                    ButtonStyle.blurple
                    if self.board[i][j] in self.blue_words
                    else (
                        ButtonStyle.red
                        if self.board[i][j] in self.red_words
                        else ButtonStyle.gray
                    )
                ),
                emoji="🥷" if self.board[i][j] == self.assassin else None,
                disabled=True,
            )
            for i in range(len(self.board))
            for j in range(len(self.board))
        ]
        return self.answer_components

    def __generate_view(self) -> CodenamesView:
        view = CodenamesView()
        for i in range(len(self.board)):
            for j in range(len(self.board)):
                disabled = (
                    self.board[i][j] not in self.blue_words +
                    self.red_words +
                    self.neutral_words and
                    self.board[i][j] != self.assassin
                )

                button = Button(
                    label=self.board[i][j],
                    style=ButtonStyle.gray,
                    custom_id=f"{self.board[i][j]}_{self.room_id}",
                    row=0 if i >= 5 else i,
                    disabled=disabled
                )

                view.add_item(button)

        return view

    async def __generate_room_embed(self) -> Embed:
        embed = Embed()

        embed.title = "房號： " + str(self.room_id)

        embed.description = f"請選擇角色，玩家人數: {len(self.players)} / 4"

        embed.add_field(
            name="藍隊",
            value=f"特工: {self.blue_operative.mention if self.blue_operative else '無'}\n"
            f"間諜首領: {self.blue_spymaster.mention if self.blue_spymaster else '無'}",
            inline=False,
        )
        embed.add_field(
            name="紅隊",
            value=f"特工: {self.red_operative.mention if self.red_operative else '無'}\n"
            f"間諜首領: {self.red_spymaster.mention if self.red_spymaster else '無'}",
            inline=False,
        )

        embed.color = Colour.random()

        return embed

    def join(self, member: Member):
        self.players.append(member)

    def _switch_role(self, role: str, user: Member):
        match role:
            case "blue_spymaster":
                self.blue_spymaster = user
                self.current_spymaster = self.blue_spymaster
                self.blue_operative = None
                self.red_operative = None
                self.red_spymaster = None
            case "blue_operative":
                self.blue_operative = user
                self.blue_spymaster = None
                self.red_operative = None
                self.red_spymaster = None
            case "red_spymaster":
                self.red_spymaster = user
                self.current_spymaster = self.red_spymaster
                self.red_operative = None
                self.blue_spymaster = None
                self.blue_operative = None
            case "red_operative":
                self.red_operative = user
                self.red_spymaster = None
                self.blue_spymaster = None
                self.blue_operative = None

    def randomize_teams(self):
        self.blue_operative = None
        self.blue_spymaster = None
        self.red_operative = None
        self.red_spymaster = None

        players = self.players
        random.shuffle(players)

        self.blue_spymaster = players[0]
        self.red_spymaster = players[1] if len(players) > 1 else None
        self.blue_operative = players[2] if len(players) > 2 else None
        self.red_operative = players[3] if len(players) > 3 else None

    def reset_teams(self):
        self.blue_operative = None
        self.blue_spymaster = None
        self.red_operative = None
        self.red_spymaster = None

    def __switch_turn(self):
        self.current_turn = "blue" if self.current_turn == "red" else "red"
        self.current_spymaster = self.blue_spymaster if self.current_turn == "red" else self.red_spymaster
        self.hint = False

    async def __end_game(self, interaction: ApplicationCommandInteraction):
        self.blue_operative = None
        self.blue_spymaster = None
        self.red_operative = None
        self.red_spymaster = None
        self.blue_words = []
        self.red_words = []
        self.neutral_words = []

        await interaction.response.edit_message(embed=Embed(title="Game Over!", description=f"{self.current_turn} Team win!", colour=Colour.red()), components=self.answer_components)

    def __check_answer_correct(self, answer: str) -> Answer:
        if answer in self.blue_words:
            return Answer.BLUE
        elif answer in self.red_words:
            return Answer.RED
        elif answer == self.assassin:
            return Answer.ASSASSIN
        else:
            return Answer.NEUTRAL

    async def give_hint(
        self, word: str, number: int, interaction: ApplicationCommandInteraction
    ):
        if self.current_turn == "blue":
            if self.blue_spymaster != interaction.user:
                return await interaction.response.send_message(
                    "You are not the spymaster!", ephemeral=True
                )
        else:
            if self.red_spymaster != interaction.user:
                return await interaction.response.send_message(
                    "You are not the spymaster!", ephemeral=True
                )
        self.word = word
        self.number = number
        self.hint = True

    async def give_answer(self, interaction: ApplicationCommandInteraction, text: str, number: int, team: TEAM):
        answer = self.__check_answer_correct(text)
        match team:
            case "blue":
                for button in self.view.children:
                    if button.label == text:
                        button.disabled = True
                        button.style = ButtonStyle.blurple if text in self.blue_words else ButtonStyle.red
                        break
                if answer == Answer.BLUE:
                    if self._blue_count == number:
                        self.__switch_turn()
                        await interaction.response.send_message("You have reached the maximum answer limit.", ephemeral=True)
                        self.blue_count = 0
                    self.blue_words.remove(text)
                    await interaction.response.send_message("Correct!", ephemeral=True)
                    self._blue_count += 1
                elif answer == Answer.RED or answer == Answer.NEUTRAL:
                    await interaction.response.send_message("Incorrect!", ephemeral=True)
                    self.__switch_turn()
                    self._blue_count = 0
                else:
                    self.__switch_turn()
                    return await self.__end_game(interaction)
            case "red":
                for button in self.view.children:
                    if button.label == text:
                        button.disabled = True
                        button.style = ButtonStyle.blurple if text in self.blue_words else ButtonStyle.red
                        break
                if answer == Answer.RED:
                    if self._red_count == number:
                        self.__switch_turn()
                        await interaction.response.send_message("You have reached the maximum answer limit.", ephemeral=True)
                        self.red_count = 0
                    self.red_words.remove(text)
                    await interaction.response.send_message("Correct!", ephemeral=True)
                    self._red_count += 1
                elif answer == Answer.BLUE or answer == Answer.NEUTRAL:
                    await interaction.response.send_message("Incorrect!", ephemeral=True)
                    self.__switch_turn()
                    self._red_count = 0
                else:
                    self.__switch_turn()
                    return await self.__end_game(interaction)
        return await self.update_display(message=interaction.message, mode="game")

    async def update_display(
        self, interaction: ApplicationCommandInteraction = None, message: Message = None, mode: Literal["room", "game"] = "room"
    ):
        if mode == "room":
            components = [
                ActionRow(
                    Button(
                        style=ButtonStyle.primary,
                        label="加入藍隊間諜首領",
                        custom_id=f"join_blue_spymaster_{self.room_id}",
                        disabled=False if not self.blue_spymaster else True,
                    ),
                    Button(
                        style=ButtonStyle.primary,
                        label="加入藍隊的特工",
                        custom_id=f"join_blue_operative_{self.room_id}",
                        disabled=False if not self.blue_operative else True,
                    ),
                ),
                ActionRow(
                    Button(
                        style=ButtonStyle.danger,
                        label="加入紅隊間諜首領",
                        custom_id=f"join_red_spymaster_{self.room_id}",
                        disabled=False if not self.red_spymaster else True,
                    ),
                    Button(
                        style=ButtonStyle.danger,
                        label="加入紅隊的特工",
                        custom_id=f"join_red_operative_{self.room_id}",
                        disabled=False if not self.red_operative else True,
                    ),
                ),
                ActionRow(
                    Button(
                        style=ButtonStyle.gray,
                        label="隨機分隊",
                        custom_id=f"randomize_teams_{self.room_id}",
                    ),
                    Button(
                        style=ButtonStyle.green,
                        label="開始遊戲",
                        custom_id=f"start_game_{self.room_id}",
                    ),
                    Button(
                        style=ButtonStyle.gray,
                        label="重製隊伍",
                        custom_id=f"reset_team_{self.room_id}",
                    ),
                ),
            ]
            if interaction:
                await interaction.response.edit_message(
                    embed=(await self.__generate_room_embed()), components=components
                )
            else:
                await message.edit(
                    embed=(await self.__generate_room_embed()), components=components
                )
        else:
            if interaction:
                await interaction.response.edit_message(
                    embed=(await self.__generate_codenames_embed()), view=self.view
                )
            elif message:
                await message.edit(
                    embed=(await self.__generate_codenames_embed()), view=self.view
                )
            else:
                await self.message.edit(
                    embed=(await self.__generate_codenames_embed()), view=self.view
                )

    async def __generate_codenames_embed(self) -> CodenamesEmbed:
        embed = CodenamesEmbed("機密代號")

        embed.colour = Colour.random()

        embed.add_field(name="目前回合", value="藍隊" if self.current_turn == "blue" else "紅隊", inline=True)

        embed.add_field(name="線索", value=f"{self.word}，共有 {self.number} 張卡牌與其關聯。" if self.hint else "等待間諜首腦提供", inline=True)

        embed.add_field(name="藍隊剩餘卡牌", value=f"{len(self.blue_words)}張", inline=False)

        embed.add_field(name="紅隊剩餘卡牌", value=f"{len(self.red_words)}張", inline=False)

        return embed

    async def start(self, interaction: MessageInteraction):
        self.__create_board()
        self.current_spymaster = self.blue_spymaster if self.current_turn == "blue" else self.red_spymaster
        self.view = self.__generate_view()

        await interaction.response.send_message(
            embed=(await self.__generate_codenames_embed()), view=self.view
        )

        self.message = await interaction.original_response()

        components = self.bleed_board()
        embed = WarningEmbed(
            title="請注意！這個訊息只有你可以看到",
            description=f"你是間諜首腦，你必須幫助你的特工想辦法找到所有的藍色單詞。\n"
            "但請注意，你必須要避免他們找到刺客。也就是下方提示卡中含有刺客🥷表情符號的詞彙。\n"
            "你的特工必須在遊戲結束前找到所有的藍色單詞。\n"
            "為此，我們給予了你一張提示卡讓你可以正確的引導你的特工。謹記不要外洩任何資料。\n"
            "祝好運。",
            colour=Colour.blue(),
        )
        await self.blue_spymaster.send(embed=embed, components=components)

        embed = WarningEmbed(
            title="請注意！這個訊息只有你可以看到",
            description=f"你是間諜首腦，你必須幫助你的特工想辦法找到所有的紅色單詞。\n"
            "但請注意，你必須要避免他們找到刺客。也就是下方提示卡中含有刺客🥷表情符號的詞彙。\n"
            "你的特工必須在遊戲結束前找到所有的紅色單詞。\n"
            "為此，我們給予了你一張提示卡讓你可以正確的引導你的特工。謹記不要外洩任何資料。\n"
            "祝好運。",
            colour=Colour.red(),
        )

        await self.red_spymaster.send(embed=embed, components=components)
