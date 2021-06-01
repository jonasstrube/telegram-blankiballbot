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
    Update,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
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

HOME_CHOOSING = range(1)

keyboard_main = [
    ['Spiel eintragen', 'Spielplan anzeigen'],
    ['Organisation', 'Infos', 'FAQ', 'About']
]

# ---------------------------------------------

def admin_status(update: Update, context: CallbackContext) -> None:
    last_restart_date: datetime = context.bot_data.get('last_bot_restart')
    date_string = last_restart_date.strftime("%d.%m.%Y at %H:%M") #12.04.2021 at 16:25
    update.message.reply_text("last restart: " + date_string)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Hi! Schön dass du da bist", reply_markup = ReplyKeyboardMarkup(keyboard_main))
    return HOME_CHOOSING

def spiel_eintragen(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Danke fürs Eintragen!')
    return HOME_CHOOSING

def abbrechen(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Jo, nix passiert", reply_markup = ReplyKeyboardMarkup(keyboard_main))
    return HOME_CHOOSING

# ------------------ run -----------------------

def main():
    pp = PicklePersistence(filename='db/blankiballbot_pp_db')

    updater = Updater(token=os.environ['TELEGRAM_BOTAPI_TOKEN'], persistence=pp, use_context=True)

    dp = updater.dispatcher

    dp.bot_data["last_bot_restart"] = datetime.now()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            HOME_CHOOSING: [
                MessageHandler(Filters.regex('^(' +  keyboard_main[0][0] +')$'), spiel_eintragen)]
        },
        fallbacks=[MessageHandler(Filters.regex('^Abbrechen$'), abbrechen)],
        name="home_conversation",
        persistent=True,
    )

    dp.add_handler(MessageHandler(Filters.regex('^status$'), admin_status))
    dp.add_handler(conv_handler)
    
    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
    