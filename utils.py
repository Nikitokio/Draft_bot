from datetime import datetime
from telegram import ReplyKeyboardMarkup



def get_cur_and_next_month():
    month_list = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    today_month = int(str(datetime.today())[5:7]) - 1
    return (month_list[today_month], month_list[(today_month + 1) % 12]) 

def get_name_cur_and_next_month():
    month_list = ['Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня', 'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря']
    today_month = int(str(datetime.today())[5:7]) - 1
    return (month_list[today_month], month_list[(today_month + 1) % 12]) 

def get_keyboard_from_list(list_var, cnt_in_row):
    cnt_counter = 0
    row_list = []
    keyboard = []
    if len(list_var) <= cnt_in_row:
        keyboard.append(list_var)
    else:
        for list_element in list_var:
            if cnt_counter < cnt_in_row:
                row_list.append(list_element)
                cnt_counter += 1
            else:
                keyboard.append(row_list)
                row_list = []
                row_list.append(list_element)
                cnt_counter = 1
    if len(row_list) > 0:
         keyboard.append(row_list)
    return keyboard

def month_choice_keyboard():
    keyboard = [
        [f'Текущий месяц ({get_cur_and_next_month()[0]})'],
        [f'Следующий месяц ({get_cur_and_next_month()[1]})']
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

