import discord
from discord.ext import commands
import os
import json
import asyncio
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

bots_id = [1149056168178757744, 412347257233604609]
l4_info = {}


def get_guild_priorities(guild_id):
    FILE_PATH = f'priorities/{guild_id}.json'
    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, "w") as file:
            json.dump({}, file, indent=4)

    with open(FILE_PATH, "r") as file:
        data = json.load(file)

    return data


def update_json_priorities(guild_id, data):
    FILE_PATH = f'priorities/{guild_id}.json'
    with open(FILE_PATH, "w") as file:
        json.dump(data, file, indent=4)


class L4_Sort:
    def __init__(self, guild_id, members):
        self.guild_id = guild_id
        self.players_priorities = get_guild_priorities(guild_id)
        self.voice_players = self.get_members_priorities(members)
        self.view = None

    def get_members_priorities(self, members):
        priorities = {}
        for member in members:
            member_id = str(member.id)
            if member_id not in self.players_priorities and member.id not in bots_id:
                self.players_priorities[member_id] = 3
            priorities[member_id] = self.players_priorities[member_id]

        update_json_priorities(self.guild_id, self.players_priorities)
        return priorities

    def distribute_random_balanced(self, players):
        players = list(players.items())
        random.shuffle(players)

        teams = [[], []]
        team_strength = [0, 0]

        for player, strength in players:
            weakest_team = team_strength.index(min(team_strength))
            teams[weakest_team].append(player)
            team_strength[weakest_team] += strength

        return teams, team_strength


def time_stamp(time):
    counted_time = (discord.utils.utcnow() - time).days // 365
    if counted_time == 0:
        return 'меньше года назад'
    elif (counted_time // 10 != 1 and counted_time % 10 == 1) or counted_time == 1:
        return f'{counted_time} год назад'
    elif (counted_time // 10 != 1 and counted_time % 10 in [2, 3, 4]) or counted_time in [2, 3, 4]:
        return f'{counted_time} года назад'
    else:
        return f'{counted_time} лет назад'


class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_l4_info(self, guild_id, members=None):
        if members is None:
            members = []

        if guild_id not in l4_info:
            l4_info[guild_id] = L4_Sort(guild_id, members)
        return l4_info[guild_id]

    @commands.command(help='> Помощь',
                      description='* !help `команда` (без — полный список)')
    async def help(self, ctx, comm=None):
        if comm is None:
            embed = discord.Embed(
                title='Как узнать команду',
                description="`!help <команда>` для подробностей команды."
            )
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.add_field(
                name='Музыкальные команды',
                value='`play`, `playnext`, `choose`, `skip`, `shuffle`, '
                      '`current`, `clear`, `repeat`, `leave`, `loop`, `queue`',
                inline=False
            )
            embed.add_field(
                name='Команды для веселья',
                value='`l4d2_sort`, `set_priority`, `add_player`, `remove_player`',
                inline=False
            )
            embed.add_field(
                name='Остальные команды',
                value='`help`, `user`',
                inline=False
            )
        else:
            command = self.bot.get_command(comm)
            if command is None:
                embed = discord.Embed(description='Нет такой команды')
            else:
                embed = discord.Embed(title=command.name)
                embed.add_field(name='Помощь', value=command.help, inline=False)
                embed.add_field(name='Описание', value=command.description, inline=False)
                if command.aliases:
                    embed.add_field(
                        name='Aliases',
                        value=', '.join(command.aliases),
                        inline=False
                    )

        await ctx.send(embed=embed)

    @commands.command(name='user',
                      help='> Информация о пользователе',
                      description='* !user `UserID/упоминание`')
    async def user(self, ctx, user_id=None):
        if user_id is None:
            user_id = ctx.author.id
        else:
            user_id = user_id.strip("<@!>")

        guild = ctx.guild
        member = guild.get_member(int(user_id))
        guild_member = member is not None

        if not guild_member:
            member = await self.bot.fetch_user(user_id)

        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url

        embed = discord.Embed()
        embed.set_author(name=member.name, icon_url=avatar_url)
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name='', value=member.mention)
        embed.add_field(name='User ID', value=member.id, inline=False)
        embed.add_field(
            name='Создан',
            value=f"{member.created_at:%d %B %Y} ({time_stamp(member.created_at)})",
            inline=False
        )

        if guild_member:
            embed.add_field(
                name='Зашёл на сервер',
                value=f"{member.joined_at:%d %B %Y} ({time_stamp(member.joined_at)})",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name='l4d2_sort', aliases=['l4', 'д4'],
                      help='> Сортировка команд',
                      description='* !l4')
    async def l4d2_sort_teams(self, ctx):
        members = [m for m in ctx.author.voice.channel.members if m.id not in bots_id]
        l4_obj = self.get_l4_info(ctx.guild.id, members)
        l4_obj.view = TeamView(l4_obj, l4_obj.voice_players, ctx.guild)
        await l4_obj.view.send_message(ctx)


class TeamView(discord.ui.View):
    def __init__(self, l4_obj, members, guild):
        super().__init__(timeout=None)
        self.players = members
        self.l4_obj = l4_obj
        self.guild = guild
        self.message = None
        self.teams, self.strength = self.l4_obj.distribute_random_balanced(self.players)

    def get_embed(self):
        embed = discord.Embed(colour=discord.Colour.blue())
        embed.add_field(name="Выжившие", value="\n".join(
            self.guild.get_member(int(p)).mention for p in self.teams[0]
        ))
        embed.add_field(name="Заражённые", value="\n".join(
            self.guild.get_member(int(p)).mention for p in self.teams[1]
        ))
        embed.add_field(name="Сила", value=f"{self.strength[0]} vs {self.strength[1]}", inline=False)
        return embed

    async def send_message(self, ctx):
        self.message = await ctx.send(embed=self.get_embed(), view=self)

    @discord.ui.button(label="🔄 Обновить", style=discord.ButtonStyle.primary)
    async def refresh(self, interaction: discord.Interaction, _):
        self.teams, self.strength = self.l4_obj.distribute_random_balanced(self.players)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)


async def setup(bot):
    await bot.add_cog(FunCommands(bot))
