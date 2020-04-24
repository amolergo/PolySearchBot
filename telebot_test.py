import requests
import telebot
import os
from telebot import types

# Выгружаем токен из переменной среды
token = os.environ['botTOKEN']
bot = telebot.TeleBot(token)


# Обработка запуска бота
# Создание клавиатуры
@bot.message_handler(commands=["start"])
def geo(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_places = types.KeyboardButton(text="Места", request_location=True)
    # button_events = types.KeyboardButton(text="События", request_location=True)
    keyboard.add(button_places)
    # keyboard.add(button_events)
    bot.send_message(message.chat.id, "Привет! Нажми на кнопку и передай мне свое местоположение",
                     reply_markup=keyboard)


@bot.message_handler(content_types=["location"])
def location(message):
    if message.location is None:
        return
    # Запрос к API Kudago
    places = requests.get(
        'https://kudago.com/public-api/v1.4/places/?fields=title,address,phone,is_closed,foreign_url,description',
        params={
            ('page_size', '5'),
            ('text_format', 'text'),
            ('lon', message.location.longitude),
            ('lat', message.location.latitude),
            ('radius', '1000'),
        })
    # Если запрос выполнен успешно, выводим данные в чат бота
    if places.status_code == 200:
        jsonDict = places.json()
        print(jsonDict)
        jsonResultsList = jsonDict['results']

        # Вывод количства мест рядом
        placesCountStr = 'Рядом с вами ' + str(jsonDict['count']) + ' мест'
        bot.send_message(message.chat.id, placesCountStr)

        for i in range(len(jsonResultsList)):
            # Смотрим открыто ли заведение
            if jsonResultsList[i]['is_closed']:
                isOpen = 'В данный момент заведение открыто'
            else:
                isOpen = 'В данный момент заведение закрыто'

            bot.send_message(message.chat.id, jsonResultsList[i]['title']
                             + '\n' + jsonResultsList[i]['address']
                             + '\n' + jsonResultsList[i]['phone']
                             + '\n' + jsonResultsList[i]['foreign_url']
                             + '\n' + jsonResultsList[i]['description']
                             + '\n' + '\n' + isOpen)
    elif places.status_code == 404:
        print('Request Error')

    # Так как база данных Kudago неполная, на данный момент было решено отказаться от реализации поиска событий.
    # Невозможно отсортировать события по дате.

    # else:
    #     events = requests.get(' https://kudago.com/public-api/v1.4/events/?fields=dates,title,description,price',
    #                       params={
    #                           ('page_size', '5'),
    #                           # ('fields', 'dates, title, place, description, price, images'),
    #                           ('text_format', 'text'),
    #                           ('lon', message.location.longitude),
    #                           ('lat', message.location.latitude),
    #                           ('radius', '1000'),
    #                       })
    #
    #     if events.status_code == 200:
    #         jsonDict = events.json()
    #         jsonResultsList = jsonDict['results']
    #
    #         num = 'Рядом с вами ' + str(jsonDict['count']) + ' мест'
    #         bot.send_message(message.chat.id, num)
    #         print(jsonDict)
    #
    #         for i in range(len(jsonResultsList)):
    #             # text = str(jsonResultsList[i]['dates'][0]['start'])
    #             # date = datetime.datetime.strptime(text, '%Y%m%d').date()
    #             # print(date)  # 2018-08-19
    #             print(jsonResultsList[i]['dates'][0]['start'])
    #             bot.send_message(message.chat.id, jsonResultsList[i]['title'] + '\n'
    #                              # + jsonResultsList[i]['dates'])
    #                              + '\n' + jsonResultsList[i]['description']
    #                              + '\n' + jsonResultsList[i]['price'])
    #     elif events.status_code == 404:
    #         print('Request Error')

bot.polling()
