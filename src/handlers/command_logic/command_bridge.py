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

import json
import math
import os
import sys

import discord

from handlers.command_logic.settings import misc
from . import embed_builders

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + "/../..")

lang = open(dir_path + "/strings.json")
lang = json.loads(lang.read())

import central  # noqa: E402


def run_command(command, args, user, guild, channel):
    embed = discord.Embed()

    if command == "orthobot":
        embed.title = lang["orthobot"].replace("<orthobotversion>", central.version.split("v")[1])
        embed.description = lang["code"].replace("repositoryLink", "https://github.com/Oikonomia/OrthoBot")

        embed.color = 303102
        embed.set_thumbnail(url=central.icon)
        embed.set_footer(text=central.version, icon_url=central.icon)

        response = lang["commandlist"]
        #response2 = lang["commandlist2"]
        response3 = lang["guildcommandlist"]

        response = response.replace("<orthobotversion>", central.version)
        response = response.replace("* ", "")
        response = response.replace("+", central.config["OrthoBot"]["commandPrefix"])

        #response2 = response2.replace("* ", "")
        #response2 = response2.replace("+", central.config["OrthoBot"]["commandPrefix"])

        response3 = response3.replace("* ", "")
        response3 = response3.replace("+", central.config["OrthoBot"]["commandPrefix"])

        embed.add_field(name=lang["commandlistName"], value=response, inline=False)
        #embed.add_field(name=lang["councillistName"], value=response2, inline=False)
        embed.add_field(name=lang["guildcommandlistName"], value=response3, inline=False)

        return {
            "level": "info",
            "message": embed
        }
    elif command == "search":
        query = ""

        for arg in args:
            query += arg + " "

        results = search(query[0:-1])

        query.replace("\"", "")

        pages = []
        max_results_per_page = 6
        total_pages = int(math.ceil(len(results.keys()) / max_results_per_page))

        if total_pages == 0:
            total_pages += 1
        elif total_pages > 100:
            total_pages = 100

        for i in range(total_pages):
            embed = discord.Embed()

            embed.title = lang["searchResults"] + " \"" + query[0:-1] + "\""

            page_counter = lang["pageOf"].replace("<num>", str(i + 1)).replace("<total>", str(total_pages))
            embed.description = page_counter

            embed.color = 303102
            embed.set_footer(text=central.version, icon_url=central.icon)

            if len(results.keys()) > 0:
                count = 0

                for key in list(results.keys()):
                    if len(results[key]["text"]) < 700:
                        if count < max_results_per_page:
                            title = results[key]["title"]
                            text = results[key]["text"]

                            embed.add_field(name=title, value=text, inline=False)

                            del results[key]
                            count += 1
            else:
                embed.title = lang["nothingFound"].replace("<query>", query[0:-1])
                embed.description = ""

            pages.append(embed)

            if len(pages) > 1:
                return {
                    "level": "info",
                    "paged": True,
                    "pages": pages
                }
            else:
                return {
                    "level": "info",
                    "message": pages[0]
                }
    elif command == "daily":
        return_embed = embed_builders.create_daily_embed(args[0] if args else None)

        return {
            "level": "info",
            "message": return_embed
        }
    elif command == "saint" or command == "feast":
        return_embed = embed_builders.create_saint_embed(args[0])

        return {
            "level": "info",
            "message": return_embed
        }
    elif command == "lectionary" or command == "reading":
        if len(args) == 4:
            return_embed = embed_builders.create_lectionary_embed(args[0], args[1], args[2], _date=args[3])
        else:
            return_embed = embed_builders.create_lectionary_embed(args[0], args[1], args[2])

        return {
            "level": "info",
            "message": return_embed
        }
    elif command == "setdailytime":
        perms = user.guild_permissions

        if str(user.id) != central.config["OrthoBot"]["owner"]:
            if not perms.manage_guild:
                embed.color = 16723502
                embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + "setdailytime",
                                value=lang["setdailytimenoperm"])

                return {
                    "level": "err",
                    "message": embed
                }

        if misc.set_guild_daily_time(guild, channel, args[0]):
            embed.color = 303102
            embed.set_footer(text=central.version, icon_url=central.icon)

            embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + "setdailytime",
                            value=lang["setdailytimesuccess"])

            return {
                "level": "info",
                "message": embed
            }
        else:
            embed.color = 16723502
            embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + "setdailytime",
                            value=lang["setdailytimefail"])

            return {
                "level": "err",
                "message": embed
            }
    elif command == "cleardailytime":
        perms = user.guild_permissions

        if str(user.id) != central.config["OrthoBot"]["owner"]:
            if not perms.manage_guild:
                embed.color = 16723502
                embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + "cleardailytime",
                                value=lang["cleardailytimenoperm"])

                return {
                    "level": "err",
                    "message": embed
                }

        if misc.set_guild_daily_time(guild, channel, "clear"):
            embed.color = 303102
            embed.set_footer(text=central.version, icon_url=central.icon)

            embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + "cleardailytime",
                            value=lang["cleardailytimesuccess"])

            return {
                "level": "info",
                "message": embed
            }
    elif command == "dailytime":
        time_tuple = misc.get_guild_daily_time(guild)

        if time_tuple is not None:
            channel, time = time_tuple

            embed.color = 303102
            embed.set_footer(text=central.version, icon_url=central.icon)

            response = lang["dailytimeused"]

            response = response.replace("<time>", time + " UTC")
            response = response.replace("<channel>", channel)

            embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + "dailytime",
                            value=response)

            return {
                "level": "info",
                "message": embed
            }
        else:
            response = lang["nodailytimeused"]

            embed.color = 16723502
            embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + "dailytime",
                            value=response)

            return {
                "level": "err",
                "message": embed
            }
    elif command == "users":
        embed.color = 303102
        embed.set_footer(text=central.version, icon_url=central.icon)

        processed = len(args[0].users)

        embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + "users",
                        value=lang["users"] + ": " + str(processed))

        return {
            "level": "info",
            "message": embed
        }
    elif command == "servers":
        embed.color = 303102
        embed.set_footer(text=central.version, icon_url=central.icon)

        processed = len(args[0].guilds)

        embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + "servers",
                        value=lang["servers"].replace("<count>", str(processed)))

        return {
            "level": "info",
            "message": embed
        }


def run_owner_command(bot, command, args):
    if command == "puppet":
        message = ""

        for item in args:
            message += item + " "

        if message == " " or message == "":
            return

        return {
            "level": "info",
            "text": True,
            "message": message[0:-1]
        }
    elif command == "eval":
        message = ""

        for item in args:
            message += item + " "

        try:
            return {
                "level": "info",
                "text": True,
                "message": exec(message[0:-1])
            }
        except Exception as e:
            return {
                "level": "err",
                "text": True,
                "message": "[err] " + str(e)
            }
    elif command == "userid":
        arg = ""

        for item in args:
            arg += item + " "

        split = arg[0:-1].split("#")
        results = "IDs matching: "

        if len(split) == 2:
            users = [x for x in bot.users if x.name == split[0] and x.discriminator == split[1]]

            for item in users:
                results += str(item.id) + ", "

            results = results[0:-2]
        else:
            results += "None"

        return {
            "level": "info",
            "text": True,
            "message": results
        }
    elif command == "ban":
        ban_reason = ""

        for index, value in enumerate(args):
            if index != 0:
                ban_reason += value + " "

        if central.is_snowflake(args[0]):
            if central.add_ban(args[0], ban_reason[0:-1]):
                return {
                    "level": "info",
                    "text": True,
                    "message": "Banned " + args[0] + " for " + ban_reason[0:-1] + "."
                }
            else:
                return {
                    "level": "err",
                    "text": True,
                    "message": args[0] + " is already banned."
                }
        else:
            return {
                "level": "err",
                "text": True,
                "message": "This is not an ID."
            }
    elif command == "unban":
        if central.is_snowflake(args[0]):
            if central.remove_ban(args[0]):
                return {
                    "level": "info",
                    "text": True,
                    "message": "Unbanned " + args[0] + "."
                }
            else:
                return {
                    "level": "err",
                    "text": True,
                    "message": args[0] + " is not banned."
                }
        else:
            return {
                "level": "err",
                "text": True,
                "message": "This is not an ID."
            }
    elif command == "reason":
        if central.is_snowflake(args[0]):
            is_banned, reason = central.is_banned(args[0])
            if is_banned:
                if reason is not None:
                    return {
                        "level": "info",
                        "text": True,
                        "message": args[0] + " is banned for `" + reason + "`."
                    }
                else:
                    return {
                        "level": "info",
                        "text": True,
                        "message": args[0] + " is banned for an unknown reason."
                    }
            else:
                return {
                    "level": "err",
                    "text": True,
                    "message": args[0] + " is not banned."
                }
        else:
            return {
                "level": "err",
                "text": True,
                "message": "This is not an ID."
            }
    elif command == "leave":
        if len(args) > 0:
            exists = False
            server_id = None
            server_name = ""

            for arg in args:
                server_name += arg + " "

            for item in bot.guilds:
                if item.name == server_name[0:-1]:
                    exists = True
                    server_id = item.id

            if exists:
                return {
                    "level": "info",
                    "leave": str(server_id)
                }
            else:
                return {
                    "level": "err",
                    "text": True,
                    "message": "Server does not exist!"
                }
        else:
            return {
                "level": "info",
                "leave": "this"
            }


def search(query):
    if len(query) > 0:
        return {}
    else:
        return None
