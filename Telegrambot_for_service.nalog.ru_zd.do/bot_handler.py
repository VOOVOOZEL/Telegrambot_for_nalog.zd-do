import get_result
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

PROXY = {'proxy_url': 'socks5://t1.learn.python.ru:1080',
    'urllib3_proxy_kwargs': {'username': 'learn', 'password': 'python'}}


def main():
    mybot = Updater("There must be your API", request_kwargs=PROXY)

    dp = mybot.dispatcher
    dp.add_handler(CommandHandler("start", greet_user))
    dp.add_handler(MessageHandler(Filters.text, talk_to_me))

    mybot.start_polling()
    mybot.idle()


def greet_user(bot, update):
    text = 'Вызван /start'
    update.message.reply_text(text)


def talk_to_me(bot, update):
    user_text = update.message.text
    try:
        int(user_text)
    except ValueError:
        update.message.reply_text('Номер ИНН должен содержать только цифры')
        return
    if len(user_text) != 10:
        update.message.reply_text('Номер ИНН должен содержать 10 цифр')
        return
    res = get_result.get_result_from_site(user_text)
    update.message.reply_text(res)

main()