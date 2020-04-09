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

import os
import sys

import discord

from handlers.command_logic import command_bridge

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + "/..")

import central  # noqa: E402

command_map = {
    "orthobot": 0,
    # "search": 1,
    "daily": 1,
    "saint": 1,
    "feast": 1,
    "lectionary": 3,
    "reading": 3,
    "random": 0,
    "setdailytime": 1,
    "cleardailytime": 0,
    "dailytime": 0,
    "users": 0,
    "servers": 0,
    "invite": 0,
}


def is_command(command):
    result = {
        "ok": False
    }

    for original_command_name in command_map.keys():
        if original_command_name == command:
            result = {
                "ok": True,
                "orig": original_command_name
            }

    return result


def is_owner_command(command):
    owner_commands = ["leave", "puppet", "userid", "ban", "unban",
                      "reason", "optout", "unoptout", "eval"]

    if command in owner_commands:
        return True
    else:
        return False


class CommandHandler:
    @classmethod
    def process_command(cls, bot, command, sender, guild, channel, args=None):
        proper_command = is_command(command)

        if proper_command["ok"]:
            orig_cmd = proper_command["orig"]
            if not is_owner_command(orig_cmd):
                if orig_cmd != "search":
                    if orig_cmd != "lectionary" and orig_cmd != "reading":
                        if orig_cmd != "servers" and orig_cmd != "users":
                            required_arguments = command_map[orig_cmd]

                            if args is None:
                                args = []

                            if True:
                                embed = discord.Embed()

                                embed.color = 16723502
                                embed.set_footer(text=central.version, icon_url=central.icon)

                                response = "+<command> requires <count> arguments."

                                response = response.replace("<command>", command)
                                response = response.replace("<count>", str(required_arguments))

                                embed.add_field(name="Error", value=response)

                                return {
                                    "isError": True,
                                    "return": embed
                                }

                            return command_bridge.run_command(orig_cmd, args, sender, guild, channel)
                        else:
                            required_arguments = command_map[orig_cmd]

                            if args is None:
                                args = []

                            if len(args) != required_arguments:
                                embed = discord.Embed()

                                embed.color = 16723502
                                embed.set_footer(text=central.version, icon_url=central.icon)

                                response = "+<command> requires <count> arguments."
                                response = response.replace("<command>", command)
                                response = response.replace("<count>", str(required_arguments))

                                embed.add_field(name="Error", value=response)

                                return {
                                    "isError": True,
                                    "return": embed
                                }

                            return command_bridge.run_command(orig_cmd, [bot], sender, guild, channel)
                    else:
                        if args is None:
                            args = []

                        if len(args) != 3 and len(args) != 4:
                            embed = discord.Embed()

                            embed.color = 16723502
                            embed.set_footer(text=central.version, icon_url=central.icon)

                            embed.add_field(name="Error", value=f"Usage: `~{orig_cmd} type id event` " +
                                                                f"or `~{orig_cmd} type id event date`.")

                            return {
                                "isError": True,
                                "return": embed
                            }
                        else:
                            if args[0] == "epistle":
                                if len(args) != 4:
                                    embed = discord.Embed()

                                    embed.color = 16723502
                                    embed.set_footer(text=central.version, icon_url=central.icon)

                                    embed.add_field(name="Error", value="Epistles must have a date argument. " +
                                                                        f"Usage: `~{orig_cmd} type id event date`.")

                                    return {
                                        "isError": True,
                                        "return": embed
                                    }
                            return command_bridge.run_command(orig_cmd, args, sender, guild, channel)
                else:
                    if args is None:
                        args = []

                    if len(args) == 1 and len(args[0]) < 4:
                        embed = discord.Embed()

                        embed.color = 16723502
                        embed.set_footer(text=central.version, icon_url=central.icon)

                        embed.add_field(name="Error", value="Your search query must be longer than 3 characters.")

                        return {
                            "isError": True,
                            "return": embed
                        }

                    if len(args) == 0:
                        embed = discord.Embed()

                        embed.color = 16723502
                        embed.set_footer(text=central.version, icon_url=central.icon)

                        response = "+<command> requires at least <count> arguments."

                        response = response.replace("<command>", command)
                        response = response.replace("<count>", "1")

                        embed.add_field(name="Error", value=response)

                        return {
                            "isError": True,
                            "return": embed
                        }
                    else:
                        return command_bridge.run_command(orig_cmd, args, sender, guild, channel)
            else:
                # noinspection PyBroadException
                try:
                    if str(sender.id) == central.config["OrthoBot"]["owner"]:
                        return command_bridge.run_owner_command(bot, command, args)
                except Exception:
                    pass
