#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0613, C0116, C0103
# type: ignore[union-attr]

# dependencies
# pip install python-telegram-bot --upgrade
# pip install requests

import logging
import os
from datetime import (
    datetime
)
import requests
import json
import math

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

HOME_WAEHLEN, SPIEL_EINTRAGEN_TEAMAUSWAEHLEN, EINSTELLUNGEN_WAEHLEN, EINSTELLUNGEN_TEAM_SPEICHERN = range(4)

keyboard_main = [
    ['Spiel eintragen', 'Spielplan anzeigen'],
    ['Organisation', 'Infos'],
    ['FAQ', 'About', 'Settings']
]

# ---------------------------------------------

def admin_status(update: Update, context: CallbackContext) -> None:
    last_restart_date: datetime = context.bot_data.get('last_bot_restart')
    date_string = last_restart_date.strftime("%d.%m.%Y at %H:%M") #12.04.2021 at 16:25
    update.message.reply_text("last restart: " + date_string)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Hi! Schön dass du da bist", reply_markup = ReplyKeyboardMarkup(keyboard_main))
    return HOME_WAEHLEN

def spiel_eintragen(update: Update, context: CallbackContext) -> int:
    team_id = context.user_data.get('team_id')

    if team_id:
        answer_api = requests.get('https://blankiball.de/api/team/read_opponents.php?id=' + str(team_id)) # get all possible opponents of the team of the user
        possible_opponent_teams = json.loads(answer_api.text)['records']

        # iterate through all possible opponent teams and distribute them through the keyboard (1: [1], 2: [1, 2], 3: [1, 2][3], 4: [1, 2][3, 4], 5: [1, 2, 3][4, 5], 6: [1, 2, 3][4, 5, 6], etc)
        keyboard_answer = []
        teams_count = len(possible_opponent_teams)
        teams_index = 0
        row_count = round(math.sqrt(teams_count))
        average_column_count = teams_count / row_count
        average_column_count_modulo = average_column_count % 1
        for current_row in range(row_count):
            if average_column_count_modulo == 0 or (current_row + 1) / row_count <= average_column_count_modulo + 0.0001:
                column_count: int = math.ceil(average_column_count)
            else:
                column_count: int = math.ceil(average_column_count - 1)
            single_row_content = []
            for current_column in range(column_count):
                current_team = possible_opponent_teams[teams_index]
                teams_index += 1
                single_row_content.append(current_team['name'] + " (" + current_team['kuerzel'] + ")")
            keyboard_answer.append(single_row_content)

        update.message.reply_text('Gegen welches Team habt ihr gespielt?', reply_markup=ReplyKeyboardMarkup(keyboard_answer))
        return SPIEL_EINTRAGEN_TEAMAUSWAEHLEN
    else:
        # TODO update.message.reply_text('Ich weiß noch nicht in welchem Team du spielst, aber deiner Telefonnummer nach könntest du "Max" aus Team "Beispielteam" sein. Stimmt das?', reply_markup=ReplyKeyboardMarkup(keyboard_answer))
        update.message.reply_text('Ich weiß noch nicht in welchem Team du spielst, da kann ich dir grad nicht helfen beim Eintragen :/', reply_markup=ReplyKeyboardMarkup(keyboard_main))
        return HOME_WAEHLEN

def spiel_eintragen_ergebnisteam1(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('-- Dialog beendet --', reply_markup=ReplyKeyboardMarkup(keyboard_main))
    return HOME_WAEHLEN

def einstellungen_waehlen(update: Update, context: CallbackContext) -> int: #from state HOME_WAEHLEN
    keyboard_answer =[['Team einstellen']]
    update.message.reply_text('Aye Aye! Was willst du einstellen?', reply_markup=ReplyKeyboardMarkup(keyboard_answer))
    return EINSTELLUNGEN_WAEHLEN

def einstellungen_team_aendern(update: Update, context: CallbackContext) -> int: #from state EINSTELLUNGEN_WAEHLEN
    answer_api = requests.get('https://blankiball.de/api/team/read.php') # get all possible teams the user could be in
    possible_teams = json.loads(answer_api.text)['records']
    
    #  TODO refactor for more efficiency
    keyboard_answer = []
    teams_per_row = 3
    for row in range(math.ceil(len(possible_teams) / teams_per_row)):
        row_content = []
        for column in range(teams_per_row):
            if not row*3 + column >= len(possible_teams):
                row_content.append(possible_teams[row*3 + column]['name'] + " (" + possible_teams[row*3 + column]['kuerzel'] + ")")
        keyboard_answer.append(row_content)
    
    update.message.reply_text('Okay. Zu welchem Team gehörst du denn? (Du kannst durch die Liste scrollen)', reply_markup=ReplyKeyboardMarkup(keyboard_answer))
    return EINSTELLUNGEN_TEAM_SPEICHERN

def einstellungen_team_speichern(update: Update, context: CallbackContext) -> int: #from state EINSTELLUNGEN_TEAM_SPEICHERN
    keyboard_answer =[['Team einstellen']]
    update.message.reply_text('nice! You got here', reply_markup=ReplyKeyboardMarkup(keyboard_main))
    return HOME_WAEHLEN

def abbrechen(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Jo, nix passiert", reply_markup = ReplyKeyboardMarkup(keyboard_main))
    return HOME_WAEHLEN

# ------------------ run -----------------------

def main():
    pp = PicklePersistence(filename='db/blankiballbot_pp_db')

    updater = Updater(token=os.environ['TELEGRAM_BOTAPI_TOKEN'], persistence=pp, use_context=True)

    dp = updater.dispatcher

    dp.bot_data["last_bot_restart"] = datetime.now()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            HOME_WAEHLEN: [
                # TODO refactor main keyboard so that it also receives the values from variables. Then, the filters here can get the menu points from the unique variables rather than from the changeable keyboard array
                MessageHandler(Filters.regex('^(' +  keyboard_main[0][0] +')$'), spiel_eintragen),
                MessageHandler(Filters.regex('^(' +  keyboard_main[2][2] +')$'), einstellungen_waehlen)
                ],
            SPIEL_EINTRAGEN_TEAMAUSWAEHLEN: [
                MessageHandler(Filters.text, spiel_eintragen_ergebnisteam1)],
            EINSTELLUNGEN_WAEHLEN: [
                MessageHandler(Filters.regex('^(Team einstellen)$'), einstellungen_team_aendern)], # TODO refactor 'Team einstellen' into variable
            EINSTELLUNGEN_TEAM_SPEICHERN: [
                MessageHandler(Filters.text, einstellungen_team_speichern)] # TODO refactor 'Team einstellen' into variable
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
    