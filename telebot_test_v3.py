import requests
import telebot
from telebot import types
import datetime
from datetime import datetime
import os

# Выгружаем токен из переменной среды
token = os.environ['botTOKEN']
bot = telebot.TeleBot(token)

placeOrEvent = 'placeOrEventNothing'
page = 1
longitude = None
latitude = None

# Обработка запуска бота, создание клавиатуры
@bot.message_handler(commands=['start'])
def welcome(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_places = types.KeyboardButton(text="Места")
    button_events = types.KeyboardButton(text="События")
    keyboard.add(button_places, button_events)
    bot.send_message(message.chat.id, "Что ты хочешь найти?", reply_markup=keyboard)

# Обработка нажатий на кнопки Места и События
@bot.message_handler(content_types=['text'])
def check(message):
    global latitude
    global longitude
    global page

    if (message.text == 'Места' or 'События') and (page == 1):
        # Задаем переменную чтобы различать выбранный вариант
        global placeOrEvent
        placeOrEvent = message.text

        # Создание клавиатуры геолокации
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_location = types.KeyboardButton(text="Передать геолокацию", request_location=True)
        keyboard.add(button_location)
        bot.send_message(message.chat.id, "Нажми на кнопку и передай мне свое местоположение", reply_markup=keyboard)

    elif message.text == 'Еще':
        location(message)

    elif message.text == 'В начало':
        page = 1
        longitude = None
        latitude = None
        welcome(message)

@bot.message_handler(content_types=["location"])
def location(message):
    global longitude
    global latitude
    global page

    if message.location is not None:
        longitude = message.location.longitude
        latitude = message.location.latitude

    if placeOrEvent == 'Места':
        # Запрос к API Kudago места
        places = requests.get(
            'https://kudago.com/public-api/v1.4/places/?fields=title,address,phone,is_closed,foreign_url,description,timetable&categories=amusement,anticafe,art-centers,art-space,attractions,bar,bridge,cinema,clubs,coworking,fountain,museums,palace,park,photo-places,prirodnyj-zapovednik,questroom,restaurants,sights,strip-club,suburb,theatre',
            params={
                ('page', page),
                ('page_size', '5'),
                ('text_format', 'text'),
                ('lon', longitude),
                ('lat', latitude),
                ('radius', '1500'),
                ('expand', 'timetable'),
            })

        # Если запрос выполнен успешно
        if places.status_code == 200:
            jsonDict = places.json()
            jsonResultsList = jsonDict['results']

            # Если выводится первая страница, то показываем количество мест рядом
            placesCount = jsonDict['count']
            if page == 1:
                placesCountStr = 'Мест рядом с вами: ' + str(placesCount)
                bot.send_message(message.chat.id, placesCountStr)

            # Если ничего рядом нет
            if placesCount == 0:
                welcome(message)

            if placesCount > (5*page-5):
                # Выводим данные в чат бота
                for i in range(len(jsonResultsList)):
                    # Смотрим открыто ли заведение
                    if jsonResultsList[i]['is_closed']:
                        isOpen = 'В данный момент заведение открыто'
                    else:
                        isOpen = 'В данный момент заведение закрыто'
                    bot.send_message(message.chat.id, jsonResultsList[i]['title']
                             + '\n' + jsonResultsList[i]['address'] + '\n'
                             + '\n' + jsonResultsList[i]['description'] + '\n'
                             + '\n' + jsonResultsList[i]['timetable']
                             + '\n' + jsonResultsList[i]['phone']
                             + '\n' + jsonResultsList[i]['foreign_url']
                             + '\n' + '\n' + isOpen)

                # Если выведены не все места
                if 5*page < placesCount:
                    # Создание клавиатуры "Еще"
                    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    button_morePlacesOrEvents = types.KeyboardButton(text='Еще')
                    button_back = types.KeyboardButton(text='В начало')
                    keyboard.add(button_morePlacesOrEvents, button_back)
                    moreMessage = 'Нажми на кнопку "Еще" что бы посмотреть больше мест (всего ' + str(placesCount) + ') или на кнопку "В начало" что бы венуться к поиску мест/событий'
                    bot.send_message(message.chat.id, moreMessage, reply_markup=keyboard)
                    page += 1
                else: # В противном случае возвращаемся в начало
                    page = 1
                    longitude = None
                    latitude = None
                    bot.send_message(message.chat.id, 'Места закончились!')
                    welcome(message)

        elif places.status_code == 404:
            print('Request Error')

    elif placeOrEvent == 'События':

        # Запрос к API Kudago События
        events = requests.get(
            'https://kudago.com/public-api/v1.4/events/?fields=dates,title,place,description,price',
            params={
                ('page', page),
                ('page_size', '5'),
                ('text_format', 'text'),
                ('lon', longitude),
                ('lat', latitude),
                ('radius', '8000'),
                ('expand', 'place'),
                ('order_by', '-publication_date'),
                ('actual_since', datetime.today()),
            })

        # Если запрос выполнен успешно
        if events.status_code == 200:
            jsonDict = events.json()
            jsonResultsList = jsonDict['results']

            # Если выводится первая страница, то показываем количество событий рядом
            eventsCount = jsonDict['count']
            if page == 1:
                eventsCountStr = 'Событий Рядом с вами: ' + str(eventsCount)
                bot.send_message(message.chat.id, eventsCountStr)

            # Если ничего рядом нет
            if eventsCount == 0:
                welcome(message)

            if eventsCount > (5*page-5):
                # Выводим данные в чат бота
                for i in range(len(jsonResultsList)):
                    placeList = jsonResultsList[i]['place']
                    datesList = jsonResultsList[i]['dates']
                    startTime = datetime.fromtimestamp(datesList[0]['start']).strftime('%Y-%m-%d %H:%M:%S')
                    endTime = datetime.fromtimestamp(datesList[0]['end']).strftime('%Y-%m-%d %H:%M:%S')
                    bot.send_message(message.chat.id, jsonResultsList[i]['title'] + '\n'
                                 + '\n' +'Начало: '+ startTime + ' '
                                 + '\n' +'Конец: ' + endTime + ' ' + '\n'
                                 + '\n' + placeList['title']
                                 + '\n' + placeList['address'] + '\n'
                                 + '\n' + placeList['phone'] + '\n'
                                 + '\n' + jsonResultsList[i]['description']
                                 + '\n' +'Стоимость:  '+ jsonResultsList[i]['price']
                                 + '\n' + placeList['site_url'])

                # Если выведены не все события
                if 5*page < eventsCount:
                    # Создание клавиатуры "Еще"
                    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    button_morePlacesOrEvents = types.KeyboardButton(text='Еще')
                    button_back = types.KeyboardButton(text='В начало')
                    keyboard.add(button_morePlacesOrEvents, button_back)
                    moreMessage = 'Нажми на кнопку "Еще" что бы посмотреть больше событий (всего ' + str(eventsCount) + ') или на кнопку "В начало" что бы венуться к поиску мест/событий'
                    bot.send_message(message.chat.id, moreMessage, reply_markup=keyboard)
                    page += 1
                else: # В противном случае возвращаемся в начало
                    page = 1
                    longitude = None
                    latitude = None
                    bot.send_message(message.chat.id, 'События закончились!')
                    welcome(message)

        elif events.status_code == 404:
            print('Request Error')

        # morePlacesOrEvents(message)
    else: print('Not place or event error')

bot.polling()