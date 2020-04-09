from datetime import date, timedelta
import random
import textwrap
import os
import re
import sys

from goarch_api.daily import Daily
from goarch_api.lectionary import Lectionary
from goarch_api.saint import Saint

import discord

from http.client import HTTPConnection
import logging

HTTPConnection.debuglevel = 0

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + "/../..")

import central  # noqa: E402


def random_date():
    start = date.fromtimestamp(0)
    end = start + timedelta(days=(365.5 * 50))
    return start + (end - start) * random.random()


def create_daily_embed(day="today"):
    dates = {
        "yesterday": (date.today() - timedelta(1)),
        "tomorrow": (date.today() + timedelta(1)),
        "random": random_date()
    }

    saints_to_display = 3

    if day == "today":
        daily = Daily()
    elif day in dates:
        date_formatted = f"{dates[day].month}/{dates[day].day}/{dates[day].year}"
        daily = Daily(date_formatted)
    elif day is not None:
        date_format = re.compile("[0-9]*\/[0-9]*\/[0-9]*")

        if date_format.match(day):
            day = day[1:] if day.startswith("0") else day
            daily = Daily(day)
    else:
        daily = Daily()

    daily.get_data()

    embed = discord.Embed()
    embed.color = 303102

    embed.title = daily.formatted_date
    embed.url = daily.public_url

    embed.set_thumbnail(url=daily.icon)

    for index, saint in enumerate(daily.saints):
        saint.get_data()

        if index == 0:
            if daily.lectionary_title == saint.title:
                embed.description = daily.fasting if daily.fasting else "No Fasting"

                if daily.tone:
                    embed.description += f" / {daily.tone}"
            else:
                if daily.fasting:
                    embed.title += f" / {daily.fasting}"
                else:
                    embed.title += " / No Fasting"

                if daily.tone:
                    embed.title += f" / {daily.tone}"

                embed.description = daily.lectionary_title

        if index < saints_to_display:
            if len(saint.readings) > 0:
                biography_excerpt = textwrap.shorten(saint.readings[0].body, width=250, placeholder="...")
                embed.add_field(name=f"{saint.title} ({saint.id})",
                                value=f"© {saint.readings[0].copyright} // " + biography_excerpt, inline=False)
            else:
                embed.add_field(name=f"{saint.title} ({saint.id})", value="No information provided.", inline=False)

    for reading in daily.readings:
        title = f"{reading.type_bb.title()} Reading ({reading.id}, {reading.event})"
        title = title.replace("Mg ", "MG ")
        title = title.replace("Ot ", "OT ")

        embed.add_field(name=title, value=reading.translation.short_title, inline=True)

    embed.set_footer(icon_url=central.icon, text=f"{central.version} | Greek Orthodox Archdiocese of America")

    return embed


def create_saint_embed(_id):
    saint = Saint(_id)
    saint.get_data()

    embed = discord.Embed()
    embed.color = 303102

    embed.title = f"{saint.title} ({saint.id})"
    embed.url = saint.public_url

    if len(saint.icons) > 0:
        embed.set_thumbnail(url=saint.icons[0].url)

    if len(saint.readings) > 0:
        biography_excerpt = textwrap.shorten(saint.readings[0].body, width=600, placeholder="...")
        embed.add_field(name="Biography",
                        value=f"© {saint.readings[0].copyright} // " + biography_excerpt, inline=False)
    else:
        embed.add_field(name=saint.title, value="No information provided.", inline=False)

    for reading in saint.lectionary:
        # this is not a Reading object, it is a LectionaryReading object
        type_strings = {
            "E": "Epistle Reading",
            "G": "Gospel Reading",
            "MG": "Matins Gospel Reading",
            "OT": "Old Testament Reading"
        }

        if reading.type in type_strings:
            _type = type_strings[reading.type]
        else:
            _type = reading.type

        _type += f" ({reading.id}, {saint.id})"

        embed.add_field(name=_type, value=reading.short_title, inline=False)

    for hymn in saint.hymns:
        embed.add_field(name=f"{hymn.short_title} ({hymn.tone})",
                        value=f"© {hymn.translation.copyright} // {hymn.translation.body}", inline=False)

    embed.set_footer(icon_url=central.icon, text=f"{central.version} | Greek Orthodox Archdiocese of America")

    return embed


def create_lectionary_embed(_type, _id, event, _date=None):
    lectionary = Lectionary(_type.upper(), _id, event, date=_date)
    lectionary.get_data()

    embed = discord.Embed()
    embed.color = 303102

    embed.title = f"{lectionary.display_title} ({_id}, {event})"
    embed.description = lectionary.event
    embed.url = lectionary.public_url

    embed.set_thumbnail(url=lectionary.icon.url)

    for translation in lectionary.translations:
        reading_excerpt = textwrap.shorten(translation.body, width=600, placeholder="...")
        embed.add_field(name=translation.short_title, value=reading_excerpt, inline=False)

    embed.set_footer(icon_url=central.icon, text=f"{central.version} | Greek Orthodox Archdiocese of America")

    return embed
