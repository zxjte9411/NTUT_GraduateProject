import telepot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telebot import types
import telegram
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from pprint import pprint
import requests
import re
import json
import bs4
import io
updater = Updater(token='768785868:AAFsyvfHZh8WZSDRaVhQZ2I9b0cQro_QjjQ')
dispatcher = updater.dispatcher

isDetail = 0
stock_num = "0000"
pointList = ['KD', 'OBV', 'AR', 'DMI', 'BR', 'RSI', 'MA', 'PSY']
point = "null"
url = 'http://192.168.1.108'
money = 0


def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="感謝您的使用，請輸入要查詢股票編號")
    dispatcher.add_handler(MessageHandler(Filters.text, handle))


def trading(bot, update):
    if (stock_num == "0000"):
        bot.sendMessage(chat_id=update.message.chat_id, text="請先輸入股票代號")
    else:
        try:
            token, request = getToken('/trading')
            text = {"stock_num": stock_num, "csrfmiddlewaretoken": token}
            respose = request.post(url + '/trading', data=text)
            image = json.loads(respose.text)
            img = requests.get(url + image["img_url"])
            imagefile = io.BytesIO(img.content)
            bot.sendPhoto(chat_id=update.message.chat_id, photo=imagefile)

        except Exception as e:
            print(e)


def stockPoint(bot, update):
    if (stock_num == "0000"):
        bot.sendMessage(chat_id=update.message.chat_id, text="請先輸入股票代號")
    else:
        try:
            global isDetail
            isDetail = 0
            keyboard = [[InlineKeyboardButton("KD", callback_data='KD'), InlineKeyboardButton("OBV", callback_data='OBV')], [InlineKeyboardButton("AR", callback_data='AR'), InlineKeyboardButton("DMI", callback_data='DMI')], [
                InlineKeyboardButton("BR", callback_data='BR'), InlineKeyboardButton("RSI", callback_data='RSI')], [InlineKeyboardButton("MA", callback_data='MA'), InlineKeyboardButton("PSY", callback_data='PSY')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="選擇指標", reply_markup=reply_markup)

        except Exception as e:
            print(e)


def getStockPoint(bot, update):
    try:
        token, request = getToken('/stockPoint')
        text = {"stock_num": stock_num, "tptype": point,
                "csrfmiddlewaretoken": token}
        respose = request.post(url + '/stockPoint', data=text)
        image = json.loads(respose.text)
        img = requests.get(url + image["img_url"])
        imagefile = io.BytesIO(img.content)
        bot.sendPhoto(
            chat_id=update.callback_query.message.chat_id, photo=imagefile)

    except Exception as e:
        print(e)


def detail(bot, update):
    if (stock_num == "0000"):
        bot.sendMessage(chat_id=update.message.chat_id, text="請先輸入股票代號")
    if (money == 0):
        global isDetail
        isDetail = 1
        keyboard = [[InlineKeyboardButton("50000", callback_data=50000), InlineKeyboardButton("1000000", callback_data=100000)], [
            InlineKeyboardButton("150000", callback_data=150000), InlineKeyboardButton("200000", callback_data=200000)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="請選擇投資金額", reply_markup=reply_markup)

    else:
        try:
            keyboard = [[InlineKeyboardButton("KD", callback_data='KD'), InlineKeyboardButton("OBV", callback_data='OBV')], [InlineKeyboardButton("AR", callback_data='AR'), InlineKeyboardButton("DMI", callback_data='DMI')], [
                InlineKeyboardButton("BR", callback_data='BR'), InlineKeyboardButton("RSI", callback_data='RSI')], [InlineKeyboardButton("MA", callback_data='MA'), InlineKeyboardButton("PSY", callback_data='PSY')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="選擇要查詢的指標交易紀錄", reply_markup=reply_markup)

        except Exception as e:
            print(e)


def getDetail(bot, update):
    try:
        txt = ""
        token, request = getToken('/withdraw')
        text = {"stock_num": stock_num, "tptype": point,
                "money": money, "bot": "1", "csrfmiddlewaretoken": token}
        respose = request.post(url + '/withdraw/detail', data=text)
        info = json.loads(respose.text)["details"][point]

        for i in info:
            txt += i["date"] + " 收盤價 " + \
                str(i["close"]) + " 進行 " + i["type"] + "\n"
        bot.sendMessage(
            chat_id=update.callback_query.message.chat_id, text=point + " 指標交易紀錄如下 ")
        bot.sendMessage(
            chat_id=update.callback_query.message.chat_id, text=txt)
    except Exception as e:
        print(e)


def button(bot, update):
    global isDetail
    global point
    if (isDetail == 0):
        point = update.callback_query.data
        print(point)
        getStockPoint(bot, update)
    elif(isDetail == 2):
        point = update.callback_query.data
        getDetail(bot, update)
    else:
        isDetail = 2
        global money
        print(money)
        money = update.callback_query.data
        keyboard = [[InlineKeyboardButton("KD", callback_data='KD'), InlineKeyboardButton("OBV", callback_data='OBV')], [InlineKeyboardButton("AR", callback_data='AR'), InlineKeyboardButton("DMI", callback_data='DMI')], [
            InlineKeyboardButton("BR", callback_data='BR'), InlineKeyboardButton("RSI", callback_data='RSI')], [InlineKeyboardButton("MA", callback_data='MA'), InlineKeyboardButton("PSY", callback_data='PSY')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.sendMessage(chat_id=update.callback_query.message.chat_id,
                        text="選擇要查詢的指標交易紀錄", reply_markup=reply_markup)


def getToken(uri):
    request = requests.Session()
    response = request.get(url + uri)
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    csrfmiddlewaretoken = soup.find(
        "input", {"name": "csrfmiddlewaretoken"})["value"]
    return csrfmiddlewaretoken, request


def handle(bot, update):
    text = update.message.text
    user_id = update.message.from_user.id
    global stock_num
    stock_num = text
    bot.sendMessage(chat_id=update.message.chat_id, text="已輸入股票編號" + stock_num)
    bot.sendMessage(chat_id=update.message.chat_id, text="請鍵入指令")


def main():

    # 第一個參數是接受的指令 `\start` 的字串。

    start_handler = CommandHandler('start', start)
    #close_handler = CommandHandler('close',close)
    trading_handler = CommandHandler('trading', trading)
    stockPoint_handler = CommandHandler('stockPoint', stockPoint)
    detail_handler = CommandHandler('detail', detail)
    # 告訴 api 增加一個新的指令處理方法 (註冊)

    dispatcher.add_handler(start_handler)
    # dispatcher.add_handler(close_handler)
    dispatcher.add_handler(trading_handler)
    dispatcher.add_handler(stockPoint_handler)
    dispatcher.add_handler(detail_handler)
    dispatcher.add_handler(CallbackQueryHandler(button))

    # 進入無限迴圈，也就是開始監聽。
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
