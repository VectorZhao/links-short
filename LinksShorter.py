import telebot
import requests
import logging
import time
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv('API_URL')
API_KEY = os.getenv('API_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start'])
def help(message):
    help_message = """
Welcome to Links Shorter🔗🤖! Send /help for commands.
Available commands:
/shorten - Shorten a long URL  
/delete - Delete a shortened URL
/stats - Get stats for a shortened URL
/list - List all links
/update - Update a link
    """
    bot.reply_to(message, help_message)


def start(message):
    start_message = """
Welcome to 1uu.me bot! Send /help for commands.
Available commands:
/shorten - Shorten a long URL  
/delete - Delete a shortened URL
/stats - Get stats for a shortened URL
/list - List all links
/update - Update a link
    """

    bot.reply_to(message, start_message)


@bot.message_handler(commands=['shorten'])
def shorten(message):
    msg = bot.reply_to(message, 'Send me the long URL to shorten:')
    bot.register_next_step_handler(msg, process_shorten_step)


def process_shorten_step(message):
    url = message.text
    headers = {'X-API-KEY': API_KEY}
    data = {'target': url}

    try:
        response = requests.post(f'{API_URL}/links', headers=headers, json=data)
        logger.debug('%s 短链接生成成功', time.asctime())
    except Exception as e:
        logger.error('%s 生成短链接失败', time.asctime(), exc_info=True)

    link = response.json()['link']
    bot.reply_to(message, f'Shortened URL: {link}')


@bot.message_handler(commands=['delete'])
def delete(message):
    msg = bot.reply_to(message, 'Send me the shortened URL id to delete:')
    bot.register_next_step_handler(msg, process_delete_step)


def process_delete_step(message):
    url = message.text

    link_id = url.split('/')[-1]
    headers = {'X-API-KEY': API_KEY}

    try:
        response = requests.delete(f'{API_URL}/links/{link_id}', headers=headers)
        logger.debug('%s 链接删除成功', time.asctime())
    except Exception as e:
        logger.error('%s 链接删除失败', time.asctime(), exc_info=True)

    if response.status_code == 200:
        bot.reply_to(message, 'URL deleted successfully!')
    else:
        bot.reply_to(message, 'Error deleting URL.')


@bot.message_handler(commands=['stats'])
def stats(message):
    msg = bot.reply_to(message, 'Send me the shortened URL to get stats:')
    bot.register_next_step_handler(msg, process_stats_step)


def process_stats_step(message):
    url = message.text

    link_id = url.split('/')[-1]
    headers = {'X-API-KEY': API_KEY}

    try:
        response = requests.get(f'{API_URL}/links/{link_id}/stats', headers=headers)
        logger.debug('%s 统计数据获取成功', time.asctime())
    except Exception as e:
        logger.error('%s 获取统计数据失败', time.asctime(), exc_info=True)

    data = response.json()

    message = f"""
Stats for {url}:   

Total clicks: {data['visit_count']}  

All time:
  Top browsers: {format_top_stats(data['allTime']['browser'])}
  Top countries: {format_top_stats(data['allTime']['country'])}

Last 7 days:
  Top browsers: {format_top_stats(data['lastWeek']['browser'])}
  Top countries: {format_top_stats(data['lastWeek']['country'])}
    """
    bot.reply_to(message, message)


def format_top_stats(stats):
    top = sorted(stats, key=lambda x: x['value'], reverse=True)[:3]
    return ', '.join([f"{x['name']} ({x['value']})" for x in top])


@bot.message_handler(commands=['list'])
def list_links(message):
    response = requests.get(f'{API_URL}/links', headers={'X-API-KEY': API_KEY})

    data = response.json()

    links_message = "Your links: \n"

    i = 1
    for link in data['data']:
        links_message += f"No. {i}:\n"
        links_message += f"ID: `{link['id']}`\n"
        links_message += f"Target: `{link['target']}`\n"
        links_message += f"Link: `{link['link']}`\n"

        i += 1

    bot.send_message(chat_id=message.chat.id, text=links_message, parse_mode='Markdown')


@bot.message_handler(commands=['update'])
def update(message):
    msg = bot.reply_to(message, 'Send me the link ID to update:')
    bot.register_next_step_handler(msg, process_update_step)


def process_update_step(message):
    link_id = message.text
    msg = bot.reply_to(message, 'Send me the new target URL:')
    bot.register_next_step_handler(msg, process_update_url_step, link_id)


def process_update_url_step(message, link_id):
    url = message.text
    headers = {'X-API-KEY': API_KEY}
    data = {'target': url}

    response = requests.patch(f'{API_URL}/links/{link_id}', headers=headers, json=data)

    if response.status_code == 200:
        bot.reply_to(message, 'Link updated successfully!')
    else:
        bot.reply_to(message, 'Error updating link')


if __name__ == '__main__':
    bot.polling()
