"""
    Copyright (c) 2018 Elliott Pardee <me [at] vypr [dot] xyz>
    This file is part of OrthoBot.

    OrthoBot is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OrthoBot is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OrthoBot.  If not, see <http://www.gnu.org/licenses/>.
"""

import asyncio
import configparser
import datetime
import os

import discord

import central
from handlers.command_logic import embed_builders
from handlers.commands import CommandHandler

dir_path = os.path.dirname(os.path.realpath(__file__))

config = configparser.ConfigParser()
config.read(dir_path + "/config.ini")

configVersion = configparser.ConfigParser()
configVersion.read(dir_path + "/config.example.ini")


class OrthoBot(discord.AutoShardedClient):
    def __init__(self, *args, loop=None, **kwargs):
        super().__init__(*args, loop=loop, **kwargs)
        self.bg_task = self.loop.create_task(self.run_dailies())
        self.current_page = None
        self.total_pages = None

    async def on_ready(self):
        if int(config["OrthoBot"]["shards"]) < 2:
            activity = discord.Game(central.version + " | Shard: 1 / 1")
            await self.change_presence(status=discord.Status.online, activity=activity)

            central.log_message("info", 1, "global", "global", "connected")

    async def on_shard_ready(self, shard_id):
        activity = discord.Game(central.version + " | Shard: " + str(shard_id + 1) + " / " +
                                str(config["OrthoBot"]["shards"]))
        await self.change_presence(status=discord.Status.online, activity=activity, shard_id=shard_id)

        central.log_message("info", shard_id + 1, "global", "global", "connected")

    async def run_dailies(self):
        await self.wait_until_ready()

        while not self.is_closed():
            # noinspection PyBroadException
            try:
                # a nice list comprehension for getting all the servers with daily stuff set
                results = [x for x in central.guildDB.all() if "channel" in x and "time" in x]

                for item in results:
                    if "channel" in item and "time" in item:
                        channel = self.get_channel(int(item["channel"]))
                        daily_time = item["time"]

                        current_time = datetime.datetime.utcnow().strftime("%H:%M")

                        if daily_time == current_time:
                            embed = embed_builders.create_daily_embed()
                            await channel.send("Here is today's daily readings and saints/feasts:")
                            await channel.send(embed=embed)
            except Exception:
                pass

            await asyncio.sleep(60)

    async def on_message(self, raw):
        sender = raw.author
        identifier = sender.name + "#" + sender.discriminator
        channel = raw.channel
        message = raw.content
        guild = None

        if config["OrthoBot"]["devMode"] == "True":
            if str(sender.id) != config["OrthoBot"]["owner"]:
                return

        if sender == self.user:
            return

        if hasattr(channel, "guild"):
            guild = channel.guild

            if hasattr(channel.guild, "name"):
                source = channel.guild.name + "#" + channel.name
            else:
                source = "unknown (direct messages?)"

            if "Discord Bot" in channel.guild.name:
                if sender.id != config["OrthoBot"]["owner"]:
                    return
        else:
            source = "unknown (direct messages?)"

        if guild is None:
            shard = 1
        else:
            shard = guild.shard_id + 1

        embed_or_reaction_not_allowed = False

        if guild is not None:
            try:
                perms = channel.permissions_for(guild.me)

                if perms is not None:
                    if not perms.send_messages or not perms.read_messages:
                        return

                    if not perms.embed_links:
                        embed_or_reaction_not_allowed = True

                    if not perms.add_reactions:
                        embed_or_reaction_not_allowed = True

                    if not perms.manage_messages or not perms.read_message_history:
                        embed_or_reaction_not_allowed = True
            except AttributeError:
                pass

        if message.startswith(config["OrthoBot"]["commandPrefix"]):
            command = message[1:].split(" ")[0]
            args = message.split(" ")

            if not isinstance(args.pop(0), str):
                args = None

            cmd_handler = CommandHandler()

            res = cmd_handler.process_command(bot, command, sender, guild, channel, args)

            self.current_page = 1

            if res is None:
                return

            if res is not None:
                if "leave" in res:
                    if res["leave"] == "this":
                        if guild is not None:
                            await guild.leave()
                    else:
                        for item in bot.guilds:
                            if str(item.id) == res["leave"]:
                                await item.leave()
                                await channel.send("Left " + str(item.name))

                    central.log_message("info", shard, identifier, source, "+leave")
                    return

                if "isError" not in res:
                    if guild is not None:
                        is_banned, reason = central.is_banned(str(guild.id))

                        if is_banned:
                            await channel.send("This server has been banned from using OrthoBot. Reason: `" +
                                               reason + "`.")
                            await channel.send("If this is invalid, the server owner may appeal by contacting " +
                                               "vypr#0001.")

                            central.log_message("err", shard, identifier, source, "Server is banned.")
                            return

                    is_banned, reason = central.is_banned(str(sender.id))
                    if is_banned:
                        await channel.send(sender.mention + " You have been banned from using OrthoBot. " +
                                           "Reason: `" + reason + "`.")
                        await channel.send("You may appeal by contacting vypr#0001.")

                        central.log_message("err", shard, identifier, source, "User is banned.")
                        return

                    if embed_or_reaction_not_allowed:
                        await channel.send("I need 'Embed Links', 'Read Message History', "
                                           + "'Manage Messages', and 'Add Reactions' permissions!")
                        return

                    if "twoMessages" in res:
                        await channel.send(res["firstMessage"])
                        await channel.send(res["secondMessage"])
                    elif "paged" in res:
                        self.total_pages = len(res["pages"])

                        msg = await channel.send(embed=res["pages"][0])

                        await msg.add_reaction("⬅")
                        await msg.add_reaction("➡")

                        def check(r, u):
                            if r.message.id == msg.id:
                                if str(r.emoji) == "⬅":
                                    if u.id != bot.user.id:
                                        if self.current_page != 1:
                                            self.current_page -= 1
                                            return True
                                elif str(r.emoji) == "➡":
                                    if u.id != bot.user.id:
                                        if self.current_page != self.total_pages:
                                            self.current_page += 1
                                            return True

                        continue_paging = True

                        try:
                            while continue_paging:
                                reaction, user = await bot.wait_for('reaction_add', timeout=120.0, check=check)
                                await reaction.message.edit(embed=res["pages"][self.current_page - 1])

                                reaction, user = await bot.wait_for('reaction_remove', timeout=120.0, check=check)
                                await reaction.message.edit(embed=res["pages"][self.current_page - 1])

                        except (asyncio.TimeoutError, IndexError):
                            await msg.clear_reactions()
                    else:
                        if "reference" not in res and "text" not in res:
                            await channel.send(embed=res["message"])
                        else:
                            if res["message"] is not None:
                                await channel.send(res["message"])
                            else:
                                await channel.send("Done.")

                    clean_args = str(args).replace(",", " ").replace("[", "").replace("]", "")
                    clean_args = clean_args.replace("\"", "").replace("'", "").replace("  ", " ")
                    clean_args = clean_args.replace("\n", "").strip()

                    ignore_arg_commands = ["puppet", "eval"]

                    if command in ignore_arg_commands:
                        clean_args = ""

                    central.log_message(res["level"], shard, identifier, source, config["OrthoBot"]["commandPrefix"]
                                        + command + " " + clean_args)
                else:
                    # noinspection PyBroadException
                    try:
                        await channel.send(embed=res["return"])
                    except Exception:
                        pass


if int(config["OrthoBot"]["shards"]) > 1:
    bot = OrthoBot(shard_count=int(config["OrthoBot"]["shards"]))
else:
    bot = OrthoBot()

central.log_message("info", 0, "global", "global", central.version + " by Elliott Pardee (vypr)")
bot.run(config["OrthoBot"]["token"])
