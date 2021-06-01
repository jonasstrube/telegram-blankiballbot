#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0613, C0116, C0103
# type: ignore[union-attr]

import logging
import os
from datetime import (
    datetime
) 

from telegram import (
    Update
)
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    PicklePersistence,
    Filters
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------- classes -------------------

# --------------------------------------------

# -------------- setting vars ---------------

# ------------------------------------------

# --------------- global vars ----------------

# ---------------------------------------------

def admin_status(update: Update, context: CallbackContext) -> None:
    last_restart_date: datetime = context.bot_data.get('last_bot_restart')
    date_string = last_restart_date.strftime("%d.%m.%Y at %H:%M") #12.04.2021 at 16:25
    update.message.reply_text("last restart: " + date_string)

def start(update: Update, context: CallbackContext) -> None:

    update.message.reply_text("Hallo " + update.message.from_user.first_name + ", komm rein! Leg schon mal deine Jacke ab, Setz dich und nimm dir nen Cookie. Fühl dich wie zuhause!")
    update.message.reply_text("Bald wird hier ordentlich Funktionalität reingepumpt, Jonas und Richard sind aber grad noch an anderen Sachen dran")
    update.message.reply_text("Machs dir schon mal bequem, schau dich um und präg dir alles gut ein. In ein paar Tagen wird hier nichts mehr aussehen wie davor. Jonas hat gesagt \"Alles wird sich verändern! Kein Softwarebaustein bleibt auf dem anderen!\"")
    update.message.reply_text("Das wird sicher super. Ich bin mindestens genauso gehyped wie du!")
    update.message.reply_text("Liebe Grüße, dein Hermann Blankenstein")

# ------------------ run -----------------------

def main():
    pp = PicklePersistence(filename='db/blankiballbot_pp_db')

    updater = Updater(token=os.environ['TELEGRAM_BOTAPI_TOKEN'], persistence=pp, use_context=True)

    dp = updater.dispatcher

    dp.bot_data["last_bot_restart"] = datetime.now()

    dp.add_handler(MessageHandler(Filters.regex('^status$'), admin_status))
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text, start))

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

# ------------------ run -----------------------