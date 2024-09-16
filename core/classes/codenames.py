import random
from typing import Literal, Optional, List, Any

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
from disnake.ui.action_row import Components, MessageUIComponent

from core.embeds import WarningEmbed, CodenamesEmbed
from core.types.answer import Answer

TEAM = Literal["blue", "red"]


class Codenames:
    def __init__(
        self,
        owner: Member,
    ):
        self.owner = owner
        self.message = None
        self.components = None
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

    def __generate_answer_components(self):
        self.answer_components = [
            Button(
                label=self.board[i][j],
                custom_id=f"{self.board[i][j]}_bleed_{self.owner.id}",
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

    @staticmethod
    def __generate_room_button(team: str, role: str, owner_id: int, disabled: bool):
        style = ButtonStyle.primary if team == "blue" else ButtonStyle.danger
        label = f"加入{team}隊的{'間諜首領' if role == 'spymaster' else '特工'}"
        custom_id = f"join_{team}_{role}_{owner_id}"
        return Button(style=style, label=label, custom_id=custom_id, disabled=disabled)

    def __generate_components(self) -> Components[MessageUIComponent]:
        components = []
        for i in range(len(self.board)):
            for j in range(len(self.board)):
                disabled = (
                    self.board[i][j]
                    not in self.blue_words + self.red_words + self.neutral_words
                    and self.board[i][j] != self.assassin
                )

                button = Button(
                    label=self.board[i][j],
                    style=ButtonStyle.gray,
                    custom_id=f"{self.board[i][j]}_{self.owner.id}",
                    row=0 if i >= 5 else i,
                    disabled=disabled,
                )

                components.append(button)

        return components

    async def __generate_room_embed(self) -> Embed:
        embed = Embed(colour=Colour.random())

        embed.title = f"{self.owner.display_name} 的遊戲"

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

        return embed

    def join(self, member: Member):
        self.players.append(member)

    def _switch_role(self, role: str, user: Member):
        self.blue_spymaster = None
        self.blue_operative = None
        self.red_spymaster = None
        self.red_operative = None
        self.current_spymaster = None

        match role:
            case "blue_spymaster":
                self.blue_spymaster = user
                self.current_spymaster = self.blue_spymaster
            case "blue_operative":
                self.blue_operative = user
            case "red_spymaster":
                self.red_spymaster = user
                self.current_spymaster = self.red_spymaster
            case "red_operative":
                self.red_operative = user

    def __randomize_teams(self):
        self.blue_operative = None
        self.blue_spymaster = None
        self.red_operative = None
        self.red_spymaster = None

        random.shuffle(self.players)

        players = self.players[:4]
        (
            self.blue_spymaster,
            self.red_spymaster,
            self.blue_operative,
            self.red_operative,
        ) = (players + [None] * 4)[:4]

    def __reset_teams(self):
        self.blue_operative = None
        self.blue_spymaster = None
        self.red_operative = None
        self.red_spymaster = None

    def __switch_turn(self):
        self.current_turn = "blue" if self.current_turn == "red" else "red"
        self.current_spymaster = (
            self.blue_spymaster if self.current_turn == "blue" else self.red_spymaster
        )
        self.hint = False

    async def __end_game(self, interaction: ApplicationCommandInteraction):
        self.blue_operative = None
        self.blue_spymaster = None
        self.red_operative = None
        self.red_spymaster = None
        self.blue_words = []
        self.red_words = []
        self.neutral_words = []

        await interaction.response.edit_message(
            embed=Embed(
                title="Game Over!",
                description=f"{self.current_turn} Team win!",
                colour=Colour.red(),
            ),
            components=self.answer_components,
        )

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
                    "你不是藍隊的間諜首腦!", ephemeral=True
                )
        else:
            if self.red_spymaster != interaction.user:
                return await interaction.response.send_message(
                    "你不是紅隊的間諜首腦!", ephemeral=True
                )
        self.word = word
        self.number = number
        self.hint = True

    async def give_answer(
        self,
        interaction: ApplicationCommandInteraction,
        text: str,
        team: TEAM,
    ):
        answer = self.__check_answer_correct(text)

        def update_button():
            for button in self.components:
                if button.label == text:
                    button.disabled = True
                    button.style = (
                        ButtonStyle.blurple
                        if text in self.blue_words
                        else ButtonStyle.red
                    )
                    break

        match team:
            case "blue":
                update_button()
                if answer == Answer.BLUE:
                    self._blue_count += 1
                    print(self._blue_count)
                    if self._blue_count == self.number:
                        self.__switch_turn()
                        await interaction.response.send_message(
                            "選擇正確，由於已經達到作答上限，回合將交給對面。",
                            ephemeral=True,
                        )
                        self._blue_count = 0
                    self.blue_words.remove(text)
                    await interaction.response.send_message(
                        "選擇正確，請繼續作答!", ephemeral=True
                    )
                elif answer == Answer.RED or answer == Answer.NEUTRAL:
                    await interaction.response.send_message(
                        "你答錯了，回合將被交給對面。", ephemeral=True
                    )
                    self.__switch_turn()
                    self._blue_count = 0
                else:
                    self.__switch_turn()
                    return await self.__end_game(interaction)
            case "red":
                update_button()
                if answer == Answer.RED:
                    self._red_count += 1
                    print(self._red_count)
                    print(number)
                    if self._red_count == self.number:
                        self.__switch_turn()
                        await interaction.response.send_message(
                            "選擇正確，由於已經達到作答上限，回合將交給對面。",
                            ephemeral=True,
                        )
                        self._red_count = 0
                    self.red_words.remove(text)
                    await interaction.response.send_message(
                        "選擇正確，請繼續作答!", ephemeral=True
                    )
                elif answer == Answer.BLUE or answer == Answer.NEUTRAL:
                    await interaction.response.send_message(
                        "你答錯了，回合將被交給對面。", ephemeral=True
                    )
                    self.__switch_turn()
                    self._red_count = 0
                else:
                    self.__switch_turn()
                    return await self.__end_game(interaction)
        return await self.update_display(message=interaction.message, mode="game")

    async def update_display(
        self,
        interaction: ApplicationCommandInteraction = None,
        message: Message = None,
        mode: Literal["room", "game"] = "room",
    ):
        owner_id = self.owner.id
        if mode == "room":
            components = [
                ActionRow(
                    self.__generate_room_button(
                        "blue",
                        "spymaster",
                        owner_id,
                        disabled=bool(self.blue_spymaster),
                    ),
                    self.__generate_room_button(
                        "blue",
                        "operative",
                        owner_id,
                        disabled=bool(self.blue_operative),
                    ),
                ),
                ActionRow(
                    self.__generate_room_button(
                        "red", "spymaster", owner_id, disabled=bool(self.red_spymaster)
                    ),
                    self.__generate_room_button(
                        "red", "operative", owner_id, disabled=bool(self.red_operative)
                    ),
                ),
                ActionRow(
                    Button(
                        style=ButtonStyle.gray,
                        label="隨機分隊",
                        custom_id=f"randomize_teams_{owner_id}",
                    ),
                    Button(
                        style=ButtonStyle.green,
                        label="開始遊戲",
                        custom_id=f"start_game_{owner_id}",
                    ),
                    Button(
                        style=ButtonStyle.gray,
                        label="重製隊伍",
                        custom_id=f"reset_team_{owner_id}",
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
                    embed=(await self.__generate_codenames_embed()),
                    components=self.components,
                )
            elif message:
                await message.edit(
                    embed=(await self.__generate_codenames_embed()),
                    components=self.components,
                )
            else:
                await self.message.edit(
                    embed=(await self.__generate_codenames_embed()),
                    components=self.components,
                )

    async def __generate_codenames_embed(self) -> CodenamesEmbed:
        embed = CodenamesEmbed("機密代號")

        embed.colour = Colour.random()

        embed.add_field(
            name="目前回合",
            value="藍隊" if self.current_turn == "blue" else "紅隊",
            inline=True,
        )

        embed.add_field(
            name="線索",
            value=(
                f"`{self.word}`，共有 {self.number} 張卡牌與其關聯。"
                if self.hint
                else "等待間諜首腦提供"
            ),
            inline=True,
        )

        embed.add_field(
            name="藍隊剩餘卡牌", value=f"{len(self.blue_words)}張", inline=False
        )

        embed.add_field(
            name="紅隊剩餘卡牌", value=f"{len(self.red_words)}張", inline=False
        )

        return embed

    async def send_spymaster_message(self, spymaster: Member, color_name):
        components = self.__generate_answer_components()
        embed = WarningEmbed(
            title="請注意！這個訊息只有你可以看到",
            description=f"你是間諜首腦，你必須幫助你的特工想辦法找到所有的{color_name}單詞。\n"
            "但請注意，你必須要避免他們找到刺客。也就是下方提示卡中含有刺客🥷表情符號的詞彙。\n"
            f"你的特工必須在遊戲結束前找到所有的{color_name}單詞。\n"
            "為此，我們給予了你下方的提示卡讓你可以正確的引導你的特工。謹記不要外洩任何訊息。\n"
            "使用 </codenames hint:1285199373231456319> 指令來給予你的特工提示。\n"
            "祝好運。",
            colour=Colour.blue() if color_name == "藍色" else Colour.red(),
        )
        await spymaster.send(embed=embed, components=components)

    async def start(self, interaction: MessageInteraction):
        self.__create_board()
        self.current_spymaster = (
            self.blue_spymaster if self.current_turn == "blue" else self.red_spymaster
        )
        self.components = self.__generate_components()

        await interaction.response.send_message(
            embed=(await self.__generate_codenames_embed()), components=self.components
        )

        self.message = await interaction.original_response()

        await self.send_spymaster_message(self.blue_spymaster, "藍色")
        await self.send_spymaster_message(self.red_spymaster, "紅色")
