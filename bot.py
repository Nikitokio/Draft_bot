from __future__ import print_function

from datetime import datetime, time, timedelta, date
from dateutil.relativedelta import relativedelta

import logging

import settings
from utils import get_keyboard_from_list, month_choice_keyboard, get_name_cur_and_next_month

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup

import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


def get_all_avalible_days(start_date):
    next_month_day = start_date + relativedelta(months = 1)
    end_date = next_month_day.replace(day = 1)
    temp_date = start_date
    appointment_days = []
    while temp_date < end_date :
        # print(temp_date, temp_date.isoweekday())
        if temp_date.isoweekday() == 3 or temp_date.isoweekday() == 7:
            if len(available_time_window_list(temp_date)) > 0:
                appointment_days.append(temp_date.day)
        temp_date = temp_date + timedelta(days = +1)
    return appointment_days  

def get_calendar_service():
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        # with open('token.json', 'w') as token:
        #     token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service

service = get_calendar_service() 

def make_calendar_event(start_date):
    # service = get_calendar_service()

    start = start_date.isoformat()
    end = (start_date + timedelta(hours=1)).isoformat()

    event_result = service.events().insert(calendarId='primary',
        body={
            "summary": 'Automating calendar',
            "description": 'This is a tutorial example of automating google calendar with python',
            "start": {"dateTime": start, "timeZone": 'Europe/Moscow'},
            "end": {"dateTime": end, "timeZone": 'Europe/Moscow'},
        }
    ).execute()

def get_days_events(start_date):
    # service = get_calendar_service() 

    min_time = start_date.isoformat() + 'Z'

    max_time = start_date.replace(hour = 21, minute = 0).isoformat() + 'Z'

    events_result = service.events().list(calendarId='primary', timeMin=min_time,
                                        timeMax=max_time, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    events_list = []

    for event in events:
        start = event['start']['dateTime']
        end = event['end']['dateTime']
        start = datetime. strptime(start[0:19], "%Y-%m-%dT%H:%M:%S")
        end = datetime. strptime(end[0:19], "%Y-%m-%dT%H:%M:%S")
        event_start_end = {}
        event_start_end['start'] = start
        event_start_end['end'] = end
        events_list.append(event_start_end)

    return events_list 

def reg_appointment_event(start_date):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    start = start_date.isoformat()
    end = start_date.replace(hour=start_date.hour + 1).isoformat()
    event = {
    'description': 'Test tg bot event',
    'start': {
        'dateTime': start
    },
    'end': {
        'dateTime': end 
    }
    }

    event = service.events().insert(calendarId='primary', body=event).execute()



def available_time_window_list(start_date):
    start_date = start_date.replace(second=0, microsecond=0)        
    if start_date.date() == date.today() and start_date.time() > time(9, 0):
        cur_time = start_date
        if cur_time.minute > 30:
            cur_time = start_date.replace(hour=start_date.hour + 1, minute=0)
        else:
            cur_time = start_date.replace(minute=30)
    else:
        start_time = time(9, 0)
        cur_time = datetime.combine(start_date.date(), start_time)
    time_window_list = []
    end_time = datetime.combine(start_date.date(), time(20, 0))
    events_list = get_days_events(start_date)
    while cur_time <= end_time:
        time_window = {}
        time_window['start_time'] = cur_time
        time_window['end_time'] = cur_time + timedelta(hours=+1)
        good_window = True
        for events in events_list:
            if (events['start'] >= time_window['start_time']  and events['start'] < time_window['end_time']) or \
                (events['end'] > time_window['start_time']  and events['end'] <= time_window['end_time']) or \
                (events['start'] <= time_window['start_time'] and events['end'] >= time_window['end_time']):
                good_window = False
                break
        if good_window:
            time_window_list.append(str(cur_time.time())[:5])
        cur_time = cur_time + timedelta(minutes=+30)
    return time_window_list    

def month_choice(update, context):
    user_data = context.user_data
    user_data.pop('month', None)
    update.message.reply_text(
        "Выберите месяц", 
        reply_markup=month_choice_keyboard()
    )
    return "appointment_day_time"

def get_days_from_month(update, context):
    user_data = context.user_data
    if 'day' in user_data:
        user_data.pop('day', None)
    user_month = update.message.text 
    cur_month_sub_str = 'Текущий месяц'
    if 'month' not in user_data:
        if cur_month_sub_str in user_month:
            start_date = datetime.today()
            user_data['month'] = 'cur_month'
        else:
            start_date = (datetime.today() + relativedelta(months = 1)).replace(day=1)
            user_data['month'] = 'next_month'
    else:
        if user_data['month'] == 'cur_month':
            start_date = datetime.today()
        else:
            start_date = (datetime.today() + relativedelta(months = 1)).replace(day=1)    
    list_of_avaliable_days = get_all_avalible_days(start_date)
    keyboard = get_keyboard_from_list(list_of_avaliable_days, 5)
    keyboard.append(['/back_to_month'])
    keyboard.append(['/cancel'])
    update.message.reply_text(
        "Выберите дату", 
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )

def available_time_window_list_handler(update, context):  
    user_data = context.user_data
    if 'day' not in user_data:
        user_data['day'] = update.message.text 
    if user_data['month'] == 'cur_month':
        start_date = datetime.today()
    else:
        start_date = datetime.today() + relativedelta(months = 1)  
    user_day = user_data['day'] 
    start_date = start_date.replace(day=int(user_day))
    available_time_window = available_time_window_list(start_date)
    keyboard_window_time = get_keyboard_from_list(available_time_window, 5)
    keyboard_window_time.append(['/back_to_day'])
    keyboard_window_time.append(['/cancel'])
    update.message.reply_text(
        "Выберите время", 
        reply_markup=ReplyKeyboardMarkup(keyboard_window_time, one_time_keyboard=True)
    )

def comfirm_month_day_time_choice(update, context):
    user_time = update.message.text
    user_data = context.user_data
    user_data['time'] = datetime.strptime(user_time, '%H:%M').time()
    if user_data['month'] == 'cur_month':
        month_name = get_name_cur_and_next_month()[0]
        start_date = date.today()
    else:
        month_name = get_name_cur_and_next_month()[1]
        start_date = date.today() + relativedelta(months = 1) 
    start_date = start_date.replace(day=int(user_data['day']))
    if start_date.isoweekday() == 3:
        weekday_name = 'Среда'
    else:
        weekday_name = 'Воскресенье'
    ans_string = f"Ваш прием состоится {int(user_data['day'])} {month_name} ({weekday_name}) в {str(user_data['time'].strftime('%H:%M'))}"
    keyboard = [['/confirm'], ['/back_to_time'], ['/cancel']]
    update.message.reply_text(
        ans_string,
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )  

def confirm_month_day_time_app(update, context):
    user_data = context.user_data
    if user_data['month'] == 'cur_month':
        start_date = date.today()
    else:
        start_date = date.today() + relativedelta(months = 1) 
    start_date = start_date.replace(day=int(user_data['day']))
    start_date = datetime.combine(start_date, user_data['time'])
    make_calendar_event(start_date)
    return ConversationHandler.END
    # return "contact"


def cancel(update, context):
    update.message.reply_text(
        'Для записи на прием наберите /start!'
    )
    return ConversationHandler.END

def fullname(update, context):
    user_name = update.message.text
    if len(user_name.split()) < 3:
        update.message.reply_text("Пожалуйста, напишите имя, фамилию и отчество")
        return "contact"
    else:
        context.user_data["contact"] = {"name": user_name}
        update.message.reply_text("Укажите ваш номер телефона в формате 8_________")
        return "contact"

def phone_number(update, context):
    user_phone_number = update.message.text
    if len(user_phone_number) <= 11:
        update.message.reply_text("Укажите номер в формате 8__________")
        return "contact"
    else:
        context.user_data["contact"] = {"phone_number": user_phone_number}
        update.message.reply_text("Что вас беспокоит?")
        return "complaint"

def complaint(update, context):
    user_complaint = update.message.text
    context.user.data["contact"] = {"complaint": user_complaint}
    update.message.reply_text("Спасибо, до встречи")
    return ConversationHandler.END

def main():
    mybot = Updater(settings.BOT_KEY, use_context=True)

    dp = mybot.dispatcher
    
    appointment = ConversationHandler(
        entry_points=[CommandHandler('start', month_choice)],
        states={
            "appointment_day_time" : [
                MessageHandler(Filters.regex('^(Текущий месяц|Следующий месяц)'), get_days_from_month),
                MessageHandler(Filters.regex('^([1-9]|[1,2][0-9]|3[01])$'), available_time_window_list_handler),
                MessageHandler(Filters.regex('^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'), comfirm_month_day_time_choice),
                CommandHandler('back_to_time', available_time_window_list_handler),
                CommandHandler('back_to_day', get_days_from_month),
                CommandHandler('back_to_month', month_choice),
                CommandHandler('confirm', confirm_month_day_time_app)
                ],
            "contact" : [
                MessageHandler(Filters.text, fullname),
                MessageHandler(Filters.regex('^[0-9\-\+]{9,15}$', phone_number))
                ],
            "complaint" : [
                MessageHandler(Filters.text, complaint)
                ]
        },
        fallbacks=[CommandHandler('cancel', cancel), "contact"]
        
    )
    dp.add_handler(appointment)

    logging.info("Бот поехал!")

    mybot.start_polling()
    mybot.idle()

if __name__ == "__main__":
    main()    
