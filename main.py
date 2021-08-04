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
    date,
    datetime,
    timedelta
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

class Spiel:

    def __init__(self, id: int = 0, timestamp: str = None, fk_begegnung: int = None, biereheimteam: int = None, biereauswaertsteam: int = None, austragungsdatum: date = None, who_inserted_or_updated_last: str = None) -> None:
        self.id = id
        self.timestamp = timestamp
        self.fk_begegnung = fk_begegnung
        self.biereheimteam = biereheimteam
        self.biereauswaertsteam = biereauswaertsteam
        self.austragungsdatum = austragungsdatum
        self.who_inserted_or_updated_last = who_inserted_or_updated_last

# --------------------------------------------

# -------------- setting vars ---------------

# ------------------------------------------

# --------------- global vars ----------------

HOME, SPIEL_EINTRAGEN__GEGNERAUSWAEHLEN, SPIEL_EINTRAGEN__ERGEBNIS_EINTRAGEN_TEAM1, SPIEL_EINTRAGEN__ERGEBNIS_EINTRAGEN_TEAM2, SPIEL_EINTRAGEN__ERGEBNIS_BESTAETIGEN, EINSTELLUNGEN, EINSTELLUNGEN__TEAM_AENDERN__TEAM_AUSSUCHEN, EINSTELLUNGEN__TEAM_AENDERN__PASSWORT_EINGEBEN = range(8)

keyboard_main_teaser_how_long = 'Wann geht das Turnier endlich los? 😍'
keyboard_main_teaser_HOW_LONG = 'WIE LANGE NOCH? 😡'
keyboard_main_teaser_features = 'Kannst du eigentlich auch mehr? 🤔'
keyboard_main_teaser = [
    [keyboard_main_teaser_how_long, keyboard_main_teaser_HOW_LONG], 
    [keyboard_main_teaser_features]
]

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

# TODO delete for go live of bot
keyboard_main = keyboard_main_teaser


keyboard_einstellungen_team_einstellen = "Team einstellen"
keyboard_einstellungen = [
    [keyboard_einstellungen_team_einstellen]
]

keyboard_biere_ergebnis = [
    [0, 1],
    [2, 3]
]

keyboard_everything_correct = [
    ["Ja richtig", "Upsi lol, ne da hab ich wohl nen Fehler gemacht"]
]

# ---------------------------------------------

def admin_status(update: Update, context: CallbackContext) -> None:
    last_restart_date: datetime = context.bot_data.get('last_bot_restart')
    date_string = last_restart_date.strftime("%d.%m.%Y at %H:%M") #12.04.2021 at 16:25
    update.message.reply_text("last restart: " + date_string)

def start(update: Update, context: CallbackContext) -> int: # after state HOME
    update.message.reply_text("Hi! Schön dass du da bist", reply_markup = ReplyKeyboardMarkup(keyboard_main))
    return HOME

def spiel_eintragen(update: Update, context: CallbackContext) -> int: # after state HOME
    team_id = context.user_data.get('team_id')
    team_kuerzel = context.user_data.get('team_kuerzel')

    if team_id and team_kuerzel:
        answer_api = requests.get('https://blankiball.de/api/begegnung/read.php?team_id=' + str(team_id)) # get all Begegnungen of the Team of the User

        begegnungen_all = json.loads(answer_api.text)['records']
        
        # remove begegnungen that are not aktiv anymore (abgeschlossen, veraltet etc)
        begegnungen = []
        for begegnung in begegnungen_all:
            if begegnung['status'] == '1': # status 1 = aktiv
                begegnungen.append(begegnung)

        if (begegnungen): # check if api returned entries

            context.chat_data['temp_spiel_eintragen__possible_begegnungen'] = begegnungen

            # get all enemy team ids
            possible_opponent_team_ids = []
            for begegnung in begegnungen:
                if not begegnung['fk_heimteam'] == team_id:
                    possible_opponent_team_ids.append(begegnung['fk_heimteam'])
                elif not begegnung['fk_auswaertsteam'] == team_id:
                    possible_opponent_team_ids.append(begegnung['fk_auswaertsteam'])
                    
            body_json = {"team_ids" : possible_opponent_team_ids}
            answer_api = requests.get('https://blankiball.de/api/team/read.php', json=body_json) # get all Begegnungen of the Users Team
            possible_opponent_teams = json.loads(answer_api.text)['records']

            context.chat_data['temp_spiel_eintragen__possible_opponent_teams'] = possible_opponent_teams

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
            return SPIEL_EINTRAGEN__GEGNERAUSWAEHLEN
        
        else:
            # TODO Verschiedene Antworten, je nach Zustand des Teams im Turnier 
            #  - Turnier hat noch nicht begonnen
            #  - Turnier ist beendet
            #  - Es muss auf entscheidungsspiele bei anderen Teams gewartet werden, bis neue Spiele feststehen
            update.message.reply_text('Ihr habt grad keine anstehenden Spiele\n\nMacht doch nen Freundschaftsspiel mit Richard aus, der hat so wenige Freunde ❤️', reply_markup=ReplyKeyboardMarkup(keyboard_main))
            return HOME
    
    else:
        if team_id and not team_kuerzel: # kuerzel not set, but team_id. user is logged in, but he/she logged in in earlier version. back then only the team_id was set
            update.message.reply_text('Meine Abläufe haben sich erneuert, ich brauch leider noch mal deine persönlichen Daten. Die kannst du in den Settings hinterlegen. Bis gleich 👋', reply_markup=ReplyKeyboardMarkup(keyboard_main))
            return HOME
            pass
        else: 
            # TODO update.message.reply_text('Ich weiß noch nicht in welchem Team du spielst, aber deiner Telefonnummer nach könntest du "Max" aus Team "Beispielteam" sein. Stimmt das?', reply_markup=ReplyKeyboardMarkup(keyboard_answer))
            update.message.reply_text('Ich weiß noch nicht in welchem Team du spielst! Geh mal in die Settings, da kannst du deine Identität bestätigen', reply_markup=ReplyKeyboardMarkup(keyboard_main))
            return HOME

def spiel_eintragen__ergebnis_erfragen_team1(update: Update, context: CallbackContext) -> int: # after state SPIEL_EINTRAGEN__GEGNERAUSWAEHLEN
    
    answer_string = update.message.text
    answer_string_split = answer_string.split()

    team_kuerzel_with_brackets = answer_string_split[-1]
    team_name_split = answer_string_split[:-1]  
    team_kuerzel = team_kuerzel_with_brackets[1:-1]
    team_name = " ".join(team_name_split)
    possible_opponent_teams = context.chat_data['temp_spiel_eintragen__possible_opponent_teams']

    # get the team with the fitting kuerzel and name
    opponent_team = None
    for team in possible_opponent_teams:
        if team['kuerzel'] == team_kuerzel and team['name'] == team_name:
            opponent_team = team
            break

    possible_begegnungen = context.chat_data['temp_spiel_eintragen__possible_begegnungen']

    chosen_begegnung = None
    for begegnung in possible_begegnungen:
        if begegnung['fk_heimteam'] == opponent_team['id'] or begegnung['fk_auswaertsteam'] == opponent_team['id']:
            chosen_begegnung = begegnung
            break

    # else: # kuerzel not set. in last method team_id and team_kuerzel were checked. something went wrong
    #     update.message.reply_text('Ich weiß nicht in welchem Team du spielst! Geh mal in die Settings, da kannst du dich einloggen', reply_markup=ReplyKeyboardMarkup(keyboard_main))
    #     return HOME

    current_spiel = Spiel()
    context.chat_data['temp_spiel_eintragen__opponent_team'] = opponent_team #TODO delete after use
    context.chat_data['temp_spiel_eintragen__begegnung'] = chosen_begegnung #TODO delete after use
    context.chat_data['temp_spiel_eintragen__spiel'] = current_spiel #TODO delete after use
    del(context.chat_data['temp_spiel_eintragen__possible_opponent_teams'])
    del(context.chat_data['temp_spiel_eintragen__possible_begegnungen'])

    update.message.reply_text('Wie viele Flaschen habt ihr ausgetrunken? (Strafbiere zählen nicht)', reply_markup=ReplyKeyboardMarkup(keyboard_biere_ergebnis))
    return SPIEL_EINTRAGEN__ERGEBNIS_EINTRAGEN_TEAM1

def spiel_eintragen__ergebnis_erfragen_team2(update: Update, context: CallbackContext) -> int: # after state SPIEL_EINTRAGEN__ERGEBNIS_EINTRAGEN_TEAM1
    
    answer_string = update.message.text
    try:
        biere_userteam: int = int(answer_string)
        if biere_userteam < 0 or biere_userteam > 3:
            raise Exception("beer value too low or high")
    except:
        update.message.reply_text('Du musst schon ne Zahl zwischen 0 und 3 eingeben. Alles andere kann ich in meine Akten nicht eintragen', reply_markup=ReplyKeyboardMarkup(keyboard_biere_ergebnis))
        return SPIEL_EINTRAGEN__ERGEBNIS_EINTRAGEN_TEAM1

    current_begegenung = context.chat_data.get('temp_spiel_eintragen__begegnung')
    user_team_id = context.user_data.get('team_id')
    current_spiel: Spiel = context.chat_data.get('temp_spiel_eintragen__spiel')
    
    if current_begegenung['fk_heimteam'] == user_team_id:
        current_spiel.biereheimteam = biere_userteam
    elif current_begegenung['fk_auswaertsteam'] == user_team_id:
        current_spiel.biereauswaertsteam = biere_userteam
    else:
        update.message.reply_text('Da is was schief gelaufen, meine Akten scheinen fehlerhaft zu sein 🤷‍♂️\n\nWende dich mal an meinen Chef, den Jonas, und gib ihm folgende Aktennummer: 103003. Wenn der Lust hat hilft er vielleicht', reply_markup=ReplyKeyboardMarkup(keyboard_main))
        return HOME    

    update.message.reply_text('Wie viele Flaschen haben eure Gegner*innen ausgetrunken? (Strafbiere zählen immer noch nicht)', reply_markup=ReplyKeyboardMarkup(keyboard_biere_ergebnis))
    return SPIEL_EINTRAGEN__ERGEBNIS_EINTRAGEN_TEAM2

def spiel_eintragen__auf_richtigkeit_pruefen(update: Update, context: CallbackContext) -> int: # after state SPIEL_EINTRAGEN__ERGEBNIS_EINTRAGEN_TEAM2
    answer_string = update.message.text
    try:
        biere_gegnerinnenteam: int = int(answer_string) # exception when user gave no number
        if biere_gegnerinnenteam < 0 or biere_gegnerinnenteam > 3:
            raise Exception("beer value too low or high")
    except:
        update.message.reply_text('Du musst schon ne Zahl zwischen 0 und 3 eingeben. Alles andere kann ich in meine Akten nicht eintragen', reply_markup=ReplyKeyboardMarkup(keyboard_biere_ergebnis))
        return SPIEL_EINTRAGEN__ERGEBNIS_EINTRAGEN_TEAM2

    current_begegenung = context.chat_data.get('temp_spiel_eintragen__begegnung')
    opponent_team = context.chat_data.get('temp_spiel_eintragen__opponent_team')
    current_spiel: Spiel = context.chat_data.get('temp_spiel_eintragen__spiel')
    
    if not current_spiel.biereheimteam and current_begegenung['fk_heimteam'] == opponent_team['id']:
        current_spiel.biereheimteam = biere_gegnerinnenteam
    elif not current_spiel.biereauswaertsteam and current_begegenung['fk_auswaertsteam'] == opponent_team['id']:
        current_spiel.biereauswaertsteam = biere_gegnerinnenteam
    else:
        update.message.reply_text('Da is was schief gelaufen, meine Akten scheinen fehlerhaft zu sein 🤷‍♂️\n\nWende dich mal an meinen Chef, den Jonas, und gib ihm folgende Aktennummer: 103004. Wenn der Lust hat hilft er vielleicht', reply_markup=ReplyKeyboardMarkup(keyboard_main))
        return HOME    

    user_team_id = context.user_data.get('team_id')

    # build string for question if everything is correct

    # get beers of user team and opponent team
    if user_team_id == current_begegenung['fk_heimteam'] and opponent_team['id'] == current_begegenung['fk_auswaertsteam']:
        user_team_beers = current_spiel.biereheimteam
        opponent_team_beers = current_spiel.biereauswaertsteam
    elif user_team_id == current_begegenung['fk_auswaertsteam'] and opponent_team['id'] == current_begegenung['fk_heimteam']:
        user_team_beers = current_spiel.biereauswaertsteam
        opponent_team_beers = current_spiel.biereheimteam
    else:
        # TODO send error messages in central method with errorcode
        update.message.reply_text('Da is was schief gelaufen, meine Akten scheinen fehlerhaft zu sein 🤷‍♂️\n\nWende dich mal an meinen Chef, den Jonas, und gib ihm folgende Aktennummer: 103005. Wenn der Lust hat hilft er vielleicht', reply_markup=ReplyKeyboardMarkup(keyboard_main))
        return HOME

    # get opponent team name and kuerzel
    opponent_team_name = opponent_team['name']
    opponent_team_kuerzel = opponent_team['kuerzel']

    # get verb to tell if the user team won or lost 
    if user_team_beers > opponent_team_beers:
        verb_lose_or_win = "gewonnen"
    elif opponent_team_beers > user_team_beers:
        verb_lose_or_win = "verloren"
    elif opponent_team_beers == user_team_beers:
        update.message.reply_text('Loide, Unentschieden gibts nicht bei Blankiball 🤦‍♂️\nAlles oder nichts. Ehre oder Tod. All in or nothing. Hitler oder Merkel.\n\nDann spielt halt jetzt noch den Sieg aus. 3vs3 Basketball, Daumencatchen, Schnick-Schnack-Schnuck oder so. Könnt ihr euch aussuchen', reply_markup=ReplyKeyboardMarkup(keyboard_main))
        return HOME


    message = f'Also habt ihr mit {user_team_beers}:{opponent_team_beers} gegen Team \"{opponent_team_name}\" ({opponent_team_kuerzel}) {verb_lose_or_win}?'
    update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(keyboard_everything_correct))
    return SPIEL_EINTRAGEN__ERGEBNIS_BESTAETIGEN

def spiel_eintragen__spiel_final_speichern(update: Update, context: CallbackContext) -> int: # after state SPIEL_EINTRAGEN__ERGEBNIS_BESTAETIGEN
    answer_string = update.message.text
    update.message.reply_text("-- Dialog beendet --", reply_markup=ReplyKeyboardMarkup(keyboard_main))
    return HOME

def einstellungen_zeigen(update: Update, context: CallbackContext) -> int: # after state HOME
    keyboard_answer =[['Team einstellen']]
    update.message.reply_text('Aye Aye! Was willst du einstellen?', reply_markup=ReplyKeyboardMarkup(keyboard_answer))
    return EINSTELLUNGEN

def einstellungen__team_aendern__moegliche_teams_zeigen(update: Update, context: CallbackContext) -> int: # after state EINSTELLUNGEN
    answer_api = requests.get('https://blankiball.de/api/team/read.php?current_tournament=true') # get all possible teams the user could be in
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

    if (answer_string_split[0] == 'hexhex' and len(answer_string_split) == 2 and not answer_string_split[1][0] == '('): # for example "hexhex JBG" (kuerzel darf nicht mit ( beginnen!!))
        admin_mode = True
        team_kuerzel = answer_string_split[1]
        answer_api = requests.get('https://blankiball.de/api/team/read.php') # get ALL possible teams, even the ones that are not in the current tournament (for example in test tournaments)
        possible_teams = json.loads(answer_api.text)['records']
    else:
        admin_mode = False
        team_kuerzel_with_brackets = answer_string_split[-1]
        team_name_split = answer_string_split[:-1]  
        team_kuerzel = team_kuerzel_with_brackets[1:-1]
        team_name = " ".join(team_name_split)
        possible_teams = context.chat_data['einstellungen_possible_teams']

    # get the team with the fitting kuerzel and name
    chosen_team = None
    if(not admin_mode):
        for team in possible_teams:
            if team['kuerzel'] == team_kuerzel and team['name'] == team_name:
                chosen_team = team
                break
    else:
        for team in possible_teams:
            if team['kuerzel'] == team_kuerzel: # in admin mode the user didnt give a team name, we only compare the kuerzel
                chosen_team = team
                break

    if chosen_team:
        context.chat_data['temp_einstellungen_team_aendern_chosen_team_kuerzel'] = chosen_team['kuerzel']
        del(context.chat_data['einstellungen_possible_teams'])
        update.message.reply_text('Wie ist das Passwort eures Teams?\n\n(hab ich deinem Teamkapitän bei eurer Anmeldung zugeschickt)', reply_markup=ReplyKeyboardRemove())
        return EINSTELLUNGEN__TEAM_AENDERN__PASSWORT_EINGEBEN
    else:
        del(context.chat_data['einstellungen_possible_teams'])
        update.message.reply_text('Gibt kein Team das so heißt wie das was du da eingegeben hast')
        update.message.reply_sticker(sticker="CAACAgIAAxUAAWDHVbrUtdyHyl-SyKqCsVkmOuNPAALJAAMfAUwVjsN8pui5_AwfBA", reply_markup=ReplyKeyboardMarkup(keyboard_main)) # annoyed macron sticker
        return HOME
        
def einstellungen__team_aendern__team_verifizieren_und_speichern(update: Update, context: CallbackContext) -> int: # after state EINSTELLUNGEN__TEAM_AENDERN__PASSWORT_EINGEBEN

    chosen_team_kuerzel = context.chat_data['temp_einstellungen_team_aendern_chosen_team_kuerzel']
    password = update.message.text
    try: update.message.delete()
    except: pass # bot could not delete message (most likely because he doesnt have the rights to do that, for example in a group)
    
    request_string = 'https://blankiball.de/api/team/check_password.php?kuerzel=' + str(chosen_team_kuerzel) + '&pw=' + password
    answer_api = requests.get(request_string) # ask if password is right for this team
    answer = json.loads(answer_api.text)['records']
    
    if not len(answer) == 0:
        chosen_team = answer[0] # if multiple teams have the same kuerzel and password, the first is chosen for the login
        context.user_data['team_id'] = chosen_team['id']
        context.user_data['team_kuerzel'] = chosen_team['kuerzel']
        update.message.reply_text('Passwort stimmt ✅\n\nDu bist für Team "' + chosen_team['name'] + '"angemeldet 👌\n\nJetzt kann ich für dich eure Spielergebnisse eintragen, dir euren Spielplan zeigen etc', reply_markup=ReplyKeyboardMarkup(keyboard_main))
    else:
        update.message.reply_text('Das Passwort ist nicht richtig 🙁 Hast du dich vertippt? Oder hat dein Teamkapitän dich hops genommen?')
        update.message.reply_sticker(sticker="CAACAgIAAxUAAWDHVbqxrxn5P7Y7oUyyaLMoJhK8AALGAAMfAUwVj1Fqci01g7gfBA", reply_markup=ReplyKeyboardMarkup(keyboard_main)) # sad macron sticker
        
    del(context.chat_data['temp_einstellungen_team_aendern_chosen_team_kuerzel'])

    return HOME

def zeit_normal(update: Update, context: CallbackContext) -> int: # after state HOME
    time_until_tournament = datetime(2021, 9, 6, 14) - datetime.now()
    hours, remainder = divmod(time_until_tournament.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    days_string = 'Tage' if time_until_tournament.days != 1 else 'Tag'
    hours_string = 'Stunden' if hours != 1 else 'Stunde'  
    minutes_string = 'Minuten' if minutes != 1 else 'Minute'  
    seconds_string = 'Sekunden' if seconds != 1 else 'Sekunde'
    answer_string = 'Noch ' + str(time_until_tournament.days) + ' ' + days_string + ', ' + str(hours) + ' ' + hours_string + ', ' + str(minutes) + ' ' + minutes_string + ' und ' + str(seconds) + ' ' + seconds_string + ' durchhalten! Du schaffst das!'
    update.message.reply_text(answer_string, reply_markup=ReplyKeyboardMarkup(keyboard_main))
    return HOME

def zeit_angeschrien(update: Update, context: CallbackContext) -> int: # after state HOME
    time_until_tournament = datetime(2021, 9, 6, 14) - datetime.now()
    hours, remainder = divmod(time_until_tournament.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    days_string = 'Tage' if time_until_tournament.days != 1 else 'Tag'
    hours_string = 'Stunden' if hours != 1 else 'Stunde'  
    minutes_string = 'Minuten' if minutes != 1 else 'Minute'  
    seconds_string = 'Sekunden' if seconds != 1 else 'Sekunde'
    answer_string = 'Noch ' + str(time_until_tournament.days) + ' ' + days_string + ', ' + str(hours) + ' ' + hours_string + ', ' + str(minutes) + ' ' + minutes_string + ' und ' + str(seconds) + ' ' + seconds_string + ' bis ich deine FRESSE POLIERE'
    
    update.message.reply_text('SCHREI MICH NICHT AN!')
    update.message.reply_text(answer_string, reply_markup=ReplyKeyboardMarkup(keyboard_main))
    return HOME

def mehr_features(update: Update, context: CallbackContext) -> int: # after state HOME
    update.message.reply_text("Jo das ist noch längst nicht alles. Aber ich bin noch nicht fertig eingewiesen, deswegen kannst du mich bis jetzt nur nach der Zeit bis zum Turnier fragen. 🤷‍♂️\n\nSpäter kann ich für dich Turnierergebnisse eintragen 📝, ich kann dir deinen Spielplan schicken 🗓, du kannst mich nach den Turnierregeln fragen 🚷 und vieles mehr. Bis dahin dauerts aber noch ein bisschen. Hold tight!", reply_markup=ReplyKeyboardMarkup(keyboard_main))
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
                MessageHandler(Filters.regex('^(' +  keyboard_main_settings +')$'), einstellungen_zeigen),
                MessageHandler(Filters.regex('^(' +  keyboard_main_teaser_how_long.replace('?', '\?') +')$'), zeit_normal),
                MessageHandler(Filters.regex('^(' +  keyboard_main_teaser_HOW_LONG.replace('?', '\?') +')$'), zeit_angeschrien),
                MessageHandler(Filters.regex('^(' +  keyboard_main_teaser_features.replace('?', '\?') +')$'), mehr_features)
                ],
            SPIEL_EINTRAGEN__GEGNERAUSWAEHLEN: [
                MessageHandler(Filters.text, spiel_eintragen__ergebnis_erfragen_team1)],
            SPIEL_EINTRAGEN__ERGEBNIS_EINTRAGEN_TEAM1: [
                MessageHandler(Filters.text, spiel_eintragen__ergebnis_erfragen_team2)],
            SPIEL_EINTRAGEN__ERGEBNIS_EINTRAGEN_TEAM2: [
                MessageHandler(Filters.text, spiel_eintragen__auf_richtigkeit_pruefen)],
            SPIEL_EINTRAGEN__ERGEBNIS_BESTAETIGEN: [
                MessageHandler(Filters.text, spiel_eintragen__spiel_final_speichern)],
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
    