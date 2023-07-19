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

start_command = types.BotCommand("/start", "start the bot")
shorten_command = types.BotCommand("/shorten", "Shorten a long URL")
del_command = types.BotCommand("/delete", "Delete a shortened URL")
stat_command = types.BotCommand("/stats", "Get stats for a shortened URL")
list_command = types.BotCommand("/list", "List all links")
update_command = types.BotCommand("/update", "Update a link")

bot.set_my_commands([start_command, shorten_command, del_command, stat_command, list_command, update_command])

@bot.message_handler(commands=['start'])
def start(message):
    start_message = """
Welcome to Links Shorter bot! Send /help for commands.
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
    try:
      result = urlparse(url)
      if not all([result.scheme, result.netloc]):
        bot.reply_to(message, 'URL 格式不正确')
        return
    except:
      bot.reply_to(message, 'URL 解析错误')
      return

    headers = {'X-API-KEY': API_KEY}
    data = {'target': url}

    response = requests.post(f'{API_URL}/links', headers=headers, json=data)
    if response.status_code not in [200, 201]:
      logger.error('请求失败,状态码%s', response.status_code)  
      bot.reply_to(message, '缩短链接失败,请重试')
      return
    logger.debug('%s 短链接生成成功', time.asctime())
    link = response.json()['link']
    shortened_url_msg = f'Shortened URL: `{link}`'
    bot.send_message(chat_id=message.chat.id, text=shortened_url_msg, parse_mode='Markdown')

@bot.message_handler(commands=['delete'])
def delete(message):
    msg = bot.reply_to(message, 'Send me the shortened URL ID to delete:')
    bot.register_next_step_handler(msg, process_delete_step)

def process_delete_step(message):
    url = message.text

    link_id = url.split('/')[-1]
    headers = {'X-API-KEY': API_KEY}

    response = requests.delete(f'{API_URL}/links/{link_id}', headers=headers)
    if response.status_code != 200:
      logger.error('删除链接失败,状态码%s', response.status_code)
      bot.reply_to(message, '链接删除失败,请重试')
      return

    logger.debug('%s 链接删除成功', time.asctime())
    bot.reply_to(message, '链接已删除!')

@bot.message_handler(commands=['stats'])
def stats(message):
    msg = bot.reply_to(message, 'Send me the shortened URL ID to get stats:')
    bot.register_next_step_handler(msg, process_stats_step)

def process_stats_step(message):
    url = message.text

    link_id = url.split('/')[-1]
    headers = {'X-API-KEY': API_KEY}

    response = requests.get(f'{API_URL}/links/{link_id}/stats', headers=headers)
    if response.status_code != 200:
      logger.error('请求失败,状态码%s', response.status_code)
      bot.reply_to(message, '请求失败,请重试')
      return
    logger.debug('%s 统计数据获取成功', time.asctime())
    data = response.json()

    stats_message = f"""
Stats for {url}:

Total clicks: {data['visit_count']}

Updated At: {data['updatedAt']}
Address: {data['address']}
Banned: {data['banned']}
Created At: {data['created_at']}
ID: {data['id']}
Link: `{data['link']}`
Password: {data['password']}
Target: `{data['target']}`
Updated At: {data['updated_at']}
  """

#All time:
#  Top browsers: {format_top_stats(data['allTime']['stats']['browser'])}
#  Top countries: {format_top_stats(data['allTime']['stats']['country'])}

#Last 7 days:
#  Top browsers: {format_top_stats(data['lastWeek']['stats']['browser'])}
#  Top countries: {format_top_stats(data['lastWeek']['stats']['country'])}

    bot.send_message(chat_id=message.chat.id, text=stats_message, parse_mode='Markdown')

#def format_top_stats(stats):
#  top = sorted(stats, key=lambda x: x['value'], reverse=True)[:3]
#  return ', '.join([f"{x['name']} ({x['value']})" for x in top])

@bot.message_handler(commands=['list'])
def list_links(message):
  links = []
  limit = 10
  skip = 0

  while True:
    params = {'limit': limit, 'skip': skip}
    response = requests.get(f'{API_URL}/links', headers={'X-API-KEY': API_KEY}, params=params)
    data = response.json()
    links.extend(data['data'])
    skip += limit

    if len(data['data']) < limit:
      break

  links_message = ""

  for i, link in enumerate(links):
    links_message += f"No. {i+1}:\n"
    links_message += f"ID: `{link['id']}`\n"
    links_message += f"Target: `{link['target']}`\n"
    links_message += f"Link: `{link['link']}`\n\n"

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
  msg = bot.reply_to(message, 'Send me the new address:')
  bot.register_next_step_handler(msg, process_update_address_step, link_id, url)

def process_update_address_step(message, link_id, url):
  address = message.text
  headers = {'X-API-KEY': API_KEY}
  data = {
    'target': url,
    'address': address
  }

  response = requests.patch(f'{API_URL}/links/{link_id}', headers=headers, json=data)

  if response.status_code == 200:
    new_link = response.json()['link']
    msg = f'链接更新成功! 新链接: `{new_link}`'
    bot.send_message(chat_id=message.chat.id, text=msg, parse_mode='Markdown')
  else:
    bot.reply_to(message, '链接更新失败!')

if __name__ == '__main__':
    logger.debug('%s bot started', time.asctime())
    bot.polling()
    logger.debug('%s bot stopped', time.asctime())


if __name__ == '__main__':
    logger.debug('%s bot started', time.asctime())
    bot.polling()
    logger.debug('%s bot stopped', time.asctime())
