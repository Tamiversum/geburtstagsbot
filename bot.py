import json
import os
import random
from datetime import datetime
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands, tasks


# ============================================================
# KONFIGURATION
# ============================================================

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
BIRTHDAY_CHANNEL_ID = int(os.getenv("BIRTHDAY_CHANNEL_ID", "0"))

DATA_FILE = Path("birthdays.json")


# ============================================================
# INTENTS
# ============================================================

intents = discord.Intents.default()


# ============================================================
# GEBURTSTAGSTEXTE
# ============================================================

BIRTHDAY_MESSAGES = [
    (
        "🎂 Heute ist dein Tag!",
        "Wir wünschen dir von Herzen alles Gute zum Geburtstag! "
        "Lass dich feiern, genieß deinen Tag und mach genau das, "
        "worauf du Lust hast."
    ),
    (
        "🎉 Ein ganz besonderer Tag!",
        "Heute dreht sich alles um dich. Wir wünschen dir "
        "einen wunderschönen Geburtstag, viele schöne Momente "
        "und natürlich ganz viel Grund zum Lächeln."
    ),
    (
        "🥳 Geburtstagsalarm!",
        "Heute gibt es etwas zu feiern: Du hast Geburtstag! "
        "Wir wünschen dir alles Gute, einen tollen Tag und "
        "ein neues Lebensjahr voller schöner Erlebnisse."
    ),
    (
        "✨ Heute darf gefeiert werden!",
        "Alles Gute zum Geburtstag! Wir hoffen, dass dein Tag "
        "genauso besonders wird, wie du es verdient hast."
    ),
    (
        "🎈 Heute bist du dran!",
        "Ein weiteres Jahr voller Geschichten, Erlebnisse "
        "und Erinnerungen beginnt. Wir wünschen dir dafür "
        "nur das Beste und einen richtig schönen Geburtstag."
    ),
    (
        "🌟 Happy Birthday!",
        "Heute ist dein persönlicher Ehrentag. Wir wünschen dir "
        "Glück, Gesundheit, schöne Überraschungen und natürlich "
        "jede Menge gute Laune."
    ),
    (
        "🎁 Eine kleine Geburtstagsmeldung!",
        "So etwas darf natürlich nicht unbemerkt bleiben: "
        "Heute hast du Geburtstag! Alles Gute und einen "
        "wunderschönen Tag wünschen wir dir."
    ),
    (
        "🎊 Zeit für Konfetti!",
        "Wir wünschen dir alles Liebe und Gute zum Geburtstag! "
        "Genieß deinen Tag, lass dich ordentlich feiern und "
        "sammle viele schöne Erinnerungen."
    ),
]


CLOSINGS = [
    "🥳 Lass dich ordentlich feiern!",
    "🎉 Hab einen großartigen Tag!",
    "🎂 Genieß deinen Ehrentag!",
    "✨ Auf ein tolles neues Lebensjahr!",
    "🎈 Heute darfst du dich feiern lassen!",
    "💫 Alles Gute für dein neues Lebensjahr!",
    "🥂 Mach dir einen richtig schönen Tag!",
    "🎁 Wir wünschen dir einen Tag voller schöner Momente!",
]


# ============================================================
# DATEN LADEN / SPEICHERN
# ============================================================

def load_data():
    if not DATA_FILE.exists():
        return {
            "birthdays": {},
            "last_greetings": {}
        }

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if "birthdays" not in data:
            data["birthdays"] = {}

        if "last_greetings" not in data:
            data["last_greetings"] = {}

        return data

    except (json.JSONDecodeError, OSError):
        return {
            "birthdays": {},
            "last_greetings": {}
        }


def save_data(data):
    temp_file = DATA_FILE.with_suffix(".tmp")

    with temp_file.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    temp_file.replace(DATA_FILE)


# ============================================================
# DATUM VERARBEITEN
# ============================================================

def parse_birthday(value):
    try:
        birthday = datetime.strptime(
            value,
            "%d.%m.%Y"
        )

    except ValueError:
        return None, "Bitte verwende das Format `TT.MM.JJJJ`."

    today = datetime.now()

    if birthday > today:
        return None, "Das Geburtsdatum darf nicht in der Zukunft liegen."

    if birthday.year < 1900:
        return None, "Bitte gib ein gültiges Geburtsdatum ein."

    return birthday, None


# ============================================================
# BOT
# ============================================================

class BirthdayBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        await self.tree.sync()

        if not birthday_check.is_running():
            birthday_check.start()


bot = BirthdayBot()


# ============================================================
# SLASH COMMAND
# ============================================================

@bot.tree.command(
    name="geburtstag",
    description="Deinen Geburtstag verwalten"
)
@app_commands.describe(
    aktion="Was möchtest du tun?",
    datum="Dein Geburtsdatum im Format TT.MM.JJJJ"
)
@app_commands.choices(
    aktion=[
        app_commands.Choice(
            name="Geburtstag eintragen",
            value="setzen"
        ),
        app_commands.Choice(
            name="Geburtstag anzeigen",
            value="anzeigen"
        ),
        app_commands.Choice(
            name="Geburtstag löschen",
            value="loeschen"
        )
    ]
)
async def geburtstag(
    interaction: discord.Interaction,
    aktion: app_commands.Choice[str],
    datum: str | None = None
):

    data = load_data()
    user_id = str(interaction.user.id)

    # --------------------------------------------------------
    # GEBURTSTAG EINTRAGEN
    # --------------------------------------------------------

    if aktion.value == "setzen":

        if not datum:
            await interaction.response.send_message(
                "Bitte gib dein Geburtsdatum an.\n\n"
                "Beispiel:\n"
                "`/geburtstag` → Geburtstag eintragen → `15.04.1995`",
                ephemeral=True
            )
            return

        birthday, error = parse_birthday(datum)

        if error:
            await interaction.response.send_message(
                error,
                ephemeral=True
            )
            return

        data["birthdays"][user_id] = {
            "day": birthday.day,
            "month": birthday.month,
            "year": birthday.year
        }

        save_data(data)

        await interaction.response.send_message(
            f"🎂 Dein Geburtstag wurde gespeichert: "
            f"**{birthday.strftime('%d.%m.%Y')}**",
            ephemeral=True
        )

        return

    # --------------------------------------------------------
    # GEBURTSTAG ANZEIGEN
    # --------------------------------------------------------

    if aktion.value == "anzeigen":

        birthday = data["birthdays"].get(user_id)

        if not birthday:
            await interaction.response.send_message(
                "Für dich ist noch kein Geburtstag gespeichert.",
                ephemeral=True
            )
            return

        formatted = (
            f"{birthday['day']:02d}."
            f"{birthday['month']:02d}."
            f"{birthday['year']:04d}"
        )

        await interaction.response.send_message(
            f"🎂 Dein gespeicherter Geburtstag ist "
            f"**{formatted}**.",
            ephemeral=True
        )

        return

    # --------------------------------------------------------
    # GEBURTSTAG LÖSCHEN
    # --------------------------------------------------------

    if aktion.value == "loeschen":

        if user_id not in data["birthdays"]:
            await interaction.response.send_message(
                "Für dich ist kein Geburtstag gespeichert.",
                ephemeral=True
            )
            return

        del data["birthdays"][user_id]
        data["last_greetings"].pop(user_id, None)

        save_data(data)

        await interaction.response.send_message(
            "🗑️ Dein Geburtstag wurde gelöscht.",
            ephemeral=True
        )

        return


# ============================================================
# GEBURTSTAGSPRÜFUNG
# ============================================================

@tasks.loop(hours=1)
async def birthday_check():

    if BIRTHDAY_CHANNEL_ID == 0:
        return

    now = datetime.now()

    data = load_data()

    channel = bot.get_channel(BIRTHDAY_CHANNEL_ID)

    if channel is None:
        try:
            channel = await bot.fetch_channel(
                BIRTHDAY_CHANNEL_ID
            )
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return

    today_key = now.strftime("%d.%m.%Y")

    changed = False

    for user_id, birthday in data["birthdays"].items():

        if birthday["day"] != now.day:
            continue

        if birthday["month"] != now.month:
            continue

        # ----------------------------------------------------
        # DUPLIKAT-SCHUTZ
        # ----------------------------------------------------

        if data["last_greetings"].get(user_id) == today_key:
            continue

        try:
            user = await bot.fetch_user(int(user_id))
        except (discord.NotFound, discord.HTTPException):
            continue

        title, message = random.choice(BIRTHDAY_MESSAGES)
        closing = random.choice(CLOSINGS)

        # ----------------------------------------------------
        # EMBED
        # ----------------------------------------------------

        embed = discord.Embed(
            title=title,
            description=(
                f"🎉 Heute feiern wir **{user.display_name}**!\n\n"
                f"{message}\n\n"
                f"{closing}"
            ),
            timestamp=datetime.now()
        )

        avatar = user.display_avatar.url

        embed.set_thumbnail(url=avatar)

        embed.set_footer(
            text="🎂 Alles Gute zum Geburtstag!"
        )

        try:
            await channel.send(
                content=user.mention,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(
                    users=True
                )
            )

            data["last_greetings"][user_id] = today_key
            changed = True

        except discord.HTTPException:
            continue

    if changed:
        save_data(data)


# ============================================================
# EVENTS
# ============================================================

@bot.event
async def on_ready():

    print("=" * 60)
    print("GEBURTSTAGSBOT")
    print("=" * 60)
    print(f"Bot: {bot.user}")
    print(f"Server: {len(bot.guilds)}")
    print(f"Geburtstagskanal: {BIRTHDAY_CHANNEL_ID}")
    print("Slash Commands: synchronisiert")
    print("Status: ONLINE")
    print("=" * 60)


# ============================================================
# START
# ============================================================

if not TOKEN:
    raise RuntimeError(
        "DISCORD_BOT_TOKEN wurde nicht gesetzt."
    )

bot.run(TOKEN)
