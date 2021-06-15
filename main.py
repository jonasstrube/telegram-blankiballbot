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
    Sticker,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
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

HOME, SPIEL_EINTRAGEN__GEGNERAUSWAEHLEN, EINSTELLUNGEN, EINSTELLUNGEN__TEAM_AENDERN__TEAM_AUSSUCHEN, EINSTELLUNGEN__TEAM_AENDERN__PASSWORT_EINGEBEN = range(5)

keyboard_main_spiel_eintragen = 'Spiel eintragen'
keyboard_main_spielplan_anzeigen = 'Spielplan anzeigen'
keyboard_main_organisation = 'Organisation'
keyboard_main_infos = 'Infos'
keyboard_main_faq = 'FAQ'
keyboard_main_about = 'About'
keyboard_main_settings = 'Settings'
keyboard_main = [
    [keyboard_main_spiel_eintragen, keyboard_main_spielplan_anzeigen],
    [keyboard_main_organisation, keyboard_main_infos],
    [keyboard_main_faq, keyboard_main_about, keyboard_main_settings]
]

keyboard_einstellungen_team_einstellen = "Team einstellen"
keyboard_einstellungen = [
    [keyboard_einstellungen_team_einstellen]
]

# ---------------------------------------------

def admin_status(update: Update, context: CallbackContext) -> None:
    last_restart_date: datetime = context.bot_data.get('last_bot_restart')
    date_string = last_restart_date.strftime("%d.%m.%Y at %H:%M") #12.04.2021 at 16:25
    update.message.reply_text("last restart: " + date_string)

def start(update: Update, context: CallbackContext) -> int: # after state HOME
    update.message.reply_text("Hi! Schön dass du da bist", reply_markup = ReplyKeyboardMarkup(keyboard_main))
    return HOME

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

        # TODO ihr seid grad in der Gruppenphase, gegen welches dieser Teams habt ihr gespielt?
        update.message.reply_text('Gegen welches Team habt ihr gespielt?', reply_markup=ReplyKeyboardMarkup(keyboard_answer))
        return SPIEL_EINTRAGEN__GEGNERAUSWAEHLEN
    else:
        # TODO update.message.reply_text('Ich weiß noch nicht in welchem Team du spielst, aber deiner Telefonnummer nach könntest du "Max" aus Team "Beispielteam" sein. Stimmt das?', reply_markup=ReplyKeyboardMarkup(keyboard_answer))
        update.message.reply_text('Ich weiß noch nicht in welchem Team du spielst! Geh mal in die Einstellugen, da kannst du mir das schreiben', reply_markup=ReplyKeyboardMarkup(keyboard_main))
        return HOME

def spiel_eintragen__ergebnis_erfragen_team1(update: Update, context: CallbackContext) -> int: # after state SPIEL_EINTRAGEN__GEGNERAUSWAEHLEN
    # TODO get bottles that the first team managed to drink
    update.message.reply_text('-- Dialog beendet --', reply_markup=ReplyKeyboardMarkup(keyboard_main))
    return HOME

def einstellungen_zeigen(update: Update, context: CallbackContext) -> int: # after state HOME_WAEHLEN
    keyboard_answer =[['Team einstellen']]
    update.message.reply_text('Aye Aye! Was willst du einstellen?', reply_markup=ReplyKeyboardMarkup(keyboard_answer))
    return EINSTELLUNGEN

def einstellungen__team_aendern__moegliche_teams_zeigen(update: Update, context: CallbackContext) -> int: # after state EINSTELLUNGEN
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
    
    context.chat_data['einstellungen_possible_teams'] = possible_teams
    mymessage = update.message.reply_text('Okay. Zu welchem Team gehörst du denn? (Du kannst durch die Liste scrollen)', reply_markup=ReplyKeyboardMarkup(keyboard_answer))
    return EINSTELLUNGEN__TEAM_AENDERN__TEAM_AUSSUCHEN

def einstellungen__team_aendern__team_verifizieren(update: Update, context: CallbackContext) -> int: # after state EINSTELLUNGEN__TEAM_AENDERN__TEAM_AUSSUCHEN
      
    # retrieve the team name and kuerzel from the user message
    answer_string = update.message.text

    answer_string_split = answer_string.split()
    team_kuerzel_with_brackets = answer_string_split[-1]
    team_name_split = answer_string_split[:-1]  
    team_kuerzel = team_kuerzel_with_brackets[1:-1]
    team_name = " ".join(team_name_split)

    # get the team with the fitting kuerzel and name
    chosen_team = None
    possible_teams = context.chat_data['einstellungen_possible_teams']
    for team in possible_teams:
        if team['kuerzel'] == team_kuerzel and team['name'] == team_name:
            chosen_team = team
            break

    if chosen_team:
        context.chat_data['temp_einstellungen_team_aendern_chosen_team'] = chosen_team
        update.message.reply_text('Wie ist das Passwort eures Teams?)', reply_markup=ReplyKeyboardRemove())
        update.message.reply_text('(hab ich deinem Teamkapitän bei eurer Anmeldung zugeschickt)')
        return EINSTELLUNGEN__TEAM_AENDERN__PASSWORT_EINGEBEN
    else:
        update.message.reply_text('Gibt kein Team das so heißt wie das was du da eingegeben hast')
        update.message.reply_sticker(sticker="CAACAgIAAxUAAWDHVbrUtdyHyl-SyKqCsVkmOuNPAALJAAMfAUwVjsN8pui5_AwfBA", reply_markup=ReplyKeyboardMarkup(keyboard_main)) # annoyed macron sticker
        return HOME
        
def einstellungen__team_aendern__team_verifizieren_und_speichern(update: Update, context: CallbackContext) -> int: # after state EINSTELLUNGEN__TEAM_AENDERN__PASSWORT_EINGEBEN

    chosen_team = context.chat_data['temp_einstellungen_team_aendern_chosen_team']
    password = update.message.text
    update.message.delete()
    
    request_string = 'https://blankiball.de/api/team/check_password.php?id=' + str(chosen_team['id']) + '&pw=' + password
    answer_api = requests.get(request_string) # ask if password is right for this team
    password_is_right = json.loads(answer_api.text)['is_valid']

    if password_is_right:
        context.user_data['team_id'] = chosen_team['id']
        update.message.reply_text('Passwort stimmt ✅')
        update.message.reply_text('Nice! Du gehörst also zum Team "' + chosen_team['name'] + '" 👌')
        update.message.reply_text('Jetzt kann ich auch deine Spielergebnisse eintragen oder dir deinen Spielplan zeigen', reply_markup=ReplyKeyboardMarkup(keyboard_main))
    else:
        update.message.reply_text('Das Passwort ist nicht richtig 🙁')
        update.message.reply_text('Hast du dich vertippt? Oder hat dein Teamkapitän dich hops genommen?')
        update.message.reply_sticker(sticker="CAACAgIAAxUAAWDHVbqxrxn5P7Y7oUyyaLMoJhK8AALGAAMfAUwVj1Fqci01g7gfBA", reply_markup=ReplyKeyboardMarkup(keyboard_main)) # sad macron sticker
        
    del(context.chat_data['temp_einstellungen_team_aendern_chosen_team'])

    return HOME

def abbrechen(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Jo, nix passiert", reply_markup = ReplyKeyboardMarkup(keyboard_main))
    return HOME

# ------------------ run -----------------------

def main():
    pp = PicklePersistence(filename='db/blankiballbot_pp_db')

    updater = Updater(token=os.environ['TELEGRAM_BOTAPI_TOKEN'], persistence=pp, use_context=True)

    dp = updater.dispatcher

    dp.bot_data["last_bot_restart"] = datetime.now()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            HOME: [
                MessageHandler(Filters.regex('^(' +  keyboard_main_spiel_eintragen +')$'), spiel_eintragen),
                MessageHandler(Filters.regex('^(' +  keyboard_main_settings +')$'), einstellungen_zeigen)
                ],
            SPIEL_EINTRAGEN__GEGNERAUSWAEHLEN: [
                MessageHandler(Filters.text, spiel_eintragen__ergebnis_erfragen_team1)],
            EINSTELLUNGEN: [
                MessageHandler(Filters.regex('^(' + keyboard_einstellungen_team_einstellen + ')$'), einstellungen__team_aendern__moegliche_teams_zeigen)],
            EINSTELLUNGEN__TEAM_AENDERN__TEAM_AUSSUCHEN: [
                MessageHandler(Filters.text, einstellungen__team_aendern__team_verifizieren)],
            EINSTELLUNGEN__TEAM_AENDERN__PASSWORT_EINGEBEN: [
                MessageHandler(Filters.text, einstellungen__team_aendern__team_verifizieren_und_speichern)]
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
    