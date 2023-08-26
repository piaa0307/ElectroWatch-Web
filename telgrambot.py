import mysql.connector
from telegram.ext import Updater, CommandHandler
from apscheduler.schedulers.background import BackgroundScheduler

TELEGRAM_BOT_TOKEN = '6508472025:AAHq9J6QOyPWPIOIKvtGI0kDbqWcnL0gJiY'  
TELEGRAM_BOT_CHAT_ID = '586431004'  



database = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'proyek'
}

def send_notification(bot, chat_id, site_code, port_id, status):
    message = f"⚠️ Peringatan! Status saat ini melebihi 200!\nSite Code: {site_code}\nPort ID: {port_id}\nStatus: {status}"
    bot.send_message(chat_id=chat_id, text=message)

def check_and_notify_status():
    latest_status_data = get_latest_status()
    if latest_status_data and latest_status_data[2] > 200:
        site_code, port_id, status = latest_status_data
        send_notification(updater.bot, TELEGRAM_BOT_CHAT_ID, site_code, port_id, status)
        
def get_latest_status():
    conn = mysql.connector.connect(**database)
    cursor = conn.cursor()

    query = "SELECT site_code, status FROM tbl_data_analog ORDER BY datetime_stamp DESC LIMIT 1;"
    cursor.execute(query)
    data = cursor.fetchone()

    cursor.close()
    conn.close()

    return data

def get_all_site_codes_and_status_exceed_200():
    try:
        conn = mysql.connector.connect(**database)
        cursor = conn.cursor()

        query = "SELECT site_code, status FROM tbl_data_analog WHERE status > 200;"
        cursor.execute(query)
        site_codes_status = cursor.fetchall()

        cursor.close()
        conn.close()

        return site_codes_status
    except Exception as e:
        print(f"Error fetching site codes and status: {e}")
        return []

def start(update, context):
    user_id = update.effective_chat.id
    context.chat_data[user_id] = {}  

    site_codes_status = get_all_site_codes_and_status_exceed_200()
    if site_codes_status:
        message = "⚠️ Peringatan!  melebihi 200kw:\n"
        for site_code, status in site_codes_status:
            message += f"Site Code: {site_code}\nStatus: {status}\n"
    else:
        message = "Tidak ada site_code dengan status melebihi 200."

    update.message.reply_text(message)

def main():
    updater = Updater('6508472025:AAHq9J6QOyPWPIOIKvtGI0kDbqWcnL0gJiY', use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    # Buat scheduler untuk menjalankan fungsi check_and_notify_status setiap 60 detik
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_notify_status, trigger='interval', seconds=60)
    scheduler.start()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
