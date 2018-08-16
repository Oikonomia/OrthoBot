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
from datetime import date, timedelta
from http.client import HTTPConnection
import logging
import html

import discord
import requests
from bs4 import BeautifulSoup

HTTPConnection.debuglevel = 0

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

from handlers.commandlogic.settings import misc

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + "/../..")

lang = open(dir_path + "/strings.json")
lang = json.loads(lang.read())

import central  # noqa: E402


def run_command(command, args, user, guild, channel):
    embed = discord.Embed()

    if command == "orthobot":
        embed.title = lang["orthobot"].replace("<orthobotversion>", central.version.split("v")[1])
        embed.description = lang["code"].replace("repositoryLink", "https://github.com/vypr/OrthoBot")

        embed.color = 303102
        embed.set_footer(text=central.version, icon_url=central.icon)

        response = lang["commandlist"]
        response2 = lang["commandlist2"]
        response3 = lang["guildcommandlist"]

        response = response.replace("<orthobotversion>", central.version)
        response = response.replace("* ", "")
        response = response.replace("+", central.config["OrthoBot"]["commandPrefix"])

        response2 = response2.replace("* ", "")
        response2 = response2.replace("+", central.config["OrthoBot"]["commandPrefix"])

        response3 = response3.replace("* ", "")
        response3 = response3.replace("+", central.config["OrthoBot"]["commandPrefix"])

        embed.add_field(name=lang["commandlistName"], value=response, inline=False)
        embed.add_field(name=lang["councillistName"], value=response2, inline=False)
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
    elif command == "today":
        return_embed = create_embed()

        return {
            "level": "info",
            "message": return_embed
        }
    elif command == "setdailytime":
        perms = user.guild_permissions

        if str(user.id) != central.config["OrthoBot"]["owner"]:
            if not perms.manage_guild:
                embed.color = 16723502
                embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + lang["commands"]["setdailytime"],
                                value=lang["setdailytimenoperm"])

                return {
                    "level": "err",
                    "message": embed
                }

        if misc.set_guild_daily_time(guild, channel, args[0]):
            embed.color = 303102
            embed.set_footer(text=central.version, icon_url=central.icon)

            embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + lang["commands"]["setdailytime"],
                            value=lang["setdailytimesuccess"])

            return {
                "level": "info",
                "message": embed
            }
        else:
            embed.color = 16723502
            embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + lang["commands"]["setdailytime"],
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
                embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + lang["commands"]["cleardailytime"],
                                value=lang["cleardailytimenoperm"])

                return {
                    "level": "err",
                    "message": embed
                }

        if misc.set_guild_daily_time(guild, channel, "clear"):
            embed.color = 303102
            embed.set_footer(text=central.version, icon_url=central.icon)

            embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + lang["commands"]["cleardailytime"],
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
            response = response.replace("<setdailytime>", lang["commands"]["setdailytime"])
            response = response.replace("<cleardailytime>", lang["commands"]["cleardailytime"])

            embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + lang["commands"]["dailytime"],
                            value=response)

            return {
                "level": "info",
                "message": embed
            }
        else:
            response = lang["nodailytimeused"]

            response = response.replace("<setdailytime>", lang["commands"]["setdailytime"])

            embed.color = 16723502
            embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + lang["commands"]["dailytime"],
                            value=response)

            return {
                "level": "err",
                "message": embed
            }
    elif command == "random":
        pass
    elif command == "users":
        embed.color = 303102
        embed.set_footer(text=central.version, icon_url=central.icon)

        processed = len(args[0].users)

        embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + lang["commands"]["users"],
                        value=lang["users"] + ": " + str(processed))

        return {
            "level": "info",
            "message": embed
        }
    elif command == "servers":
        embed.color = 303102
        embed.set_footer(text=central.version, icon_url=central.icon)

        processed = len(args[0].guilds)

        embed.add_field(name=central.config["OrthoBot"]["commandPrefix"] + lang["commands"]["servers"],
                        value=lang["servers"].replace("<count>", str(processed)))

        return {
            "level": "info",
            "message": embed
        }
    elif command == "creeds":
        embed.color = 303102
        embed.set_footer(text=central.version, icon_url=central.icon)

        response = lang["creedstext"]

        response = response.replace("<apostles>", lang["commands"]["apostles"])
        response = response.replace("<nicene>", lang["commands"]["nicene"])
        response = response.replace("<chalcedonian>", lang["commands"]["chalcedonian"])
        response = response.replace("<athanasian>", lang["commands"]["athanasian"])

        embed.add_field(name=lang["creeds"], value=response)

        return {
            "level": "info",
            "message": embed
        }
    elif command == "apostles":
        embed.color = 303102
        embed.set_footer(text=central.version, icon_url=central.icon)

        embed.add_field(name=lang["apostlescreed"], value=lang["apostlestext1"])

        return {
            "level": "info",
            "message": embed
        }
    elif command == "nicene":
        embed.color = 303102
        embed.set_footer(text=central.version, icon_url=central.icon)

        embed.add_field(name=lang["nicenecreed"], value=lang["nicenetext1"])
        embed.add_field(name=u"\u200B", value=lang["nicenetext2"])
        embed.add_field(name=u"\u200B", value=lang["nicenetext3"])
        embed.add_field(name=u"\u200B", value=lang["nicenetext4"])

        return {
            "level": "info",
            "message": embed
        }
    elif command == "chalcedonian":
        embed.color = 303102
        embed.set_footer(text=central.version, icon_url=central.icon)

        embed.add_field(name=lang["chalcedoniancreed"], value=lang["chalcedoniantext1"])
        embed.add_field(name=u"\u200B", value=lang["chalcedoniantext2"])

        return {
            "level": "info",
            "message": embed
        }
    elif command == "athanasian":
        embed.color = 303102
        embed.set_footer(text=central.version, icon_url=central.icon)

        embed.add_field(name=lang["pseudoathanasiancreed"],
                        value=lang["pseudoathanasiantext1"] + "https://www.ccel.org/creeds/athanasian.creed.html")

        return {
            "level": "info",
            "message": embed
        }
    elif command == "invite":
        return {
            "level": "info",
            "text": True,
            "message": "<https://discordapp.com/oauth2/authorize?" +
                       "client_id=361033318273384449&scope=bot&permissions=93248>"
        }


def run_owner_command(bot, command, args, lang):
    embed = discord.Embed()

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


def create_embed():
    url = "https://oca.org/saints/lives"

    saints_to_display = 3
    resp = requests.get(url)

    embed = discord.Embed()

    embed.color = 303102
    embed.set_footer(text=central.version + " | Saints from OCA, Readings from GOArch",
                     icon_url=central.icon)

    if resp is not None:
        soup = BeautifulSoup(resp.text, "lxml")
        section = soup.find("section", {"class": "saints"})
        saints = section.find_all("article", {"class": "saint"})

        for index, saint in enumerate(saints):
            if index < saints_to_display:
                if index == 0:
                    embed.set_thumbnail(url = saint.find("img")["src"])

                embed.add_field(name=saint.find("h2", {"class": "name"}).get_text(),
                                value=saint.find("p", {"class": "description"}).get_text(), inline=False)

        embed.add_field(name="For more about today's saints (including the remaining " +
                             str(len(saints) - saints_to_display) + "):", value=url, inline=False)

        goarch = requests.get("https://www.goarch.org/chapel")
        goarch_soup = BeautifulSoup(goarch.text, "lxml")

        readings = goarch_soup.find("ul", {"class": "oc-readings"}).find_all("li")

        for reading in readings:
            reading_link = reading.find("a")

            if "type=epistle" in reading_link["href"]:
                strong = reading_link.find("strong")
                strong.decompose()

                icon = reading_link.find("i")
                icon.decompose()

                embed.add_field(name="Epistle Reading", value=reading_link.get_text(), inline=True)
            elif "type=gospel" in reading_link["href"]:
                strong = reading_link.find("strong")
                strong.decompose()

                icon = reading_link.find("i")
                icon.decompose()

                embed.add_field(name="Gospel Reading", value=reading_link.get_text(), inline=True)

        return embed
    return None


if __name__ == "__main__":
    create_embed()