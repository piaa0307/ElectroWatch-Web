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

def send_notification(bot, chat_id, site_code, port_id, kw_saat_ini, percentage):
    message = (f"⚠️ Peringatan! Pemakaian daya lokasi ini melebbihi batas\n"
               f"STO: {site_code}\nPort ID: {port_id}\nKW Saat Ini: {kw_saat_ini}\nPersentase: {percentage:.2f}%")
    bot.send_message(chat_id=chat_id, text=message)

def calculate_percentage_kw(site_code, port_id, kw_saat_ini, kw_value, bot):
    try:
        kw_saat_ini = float(kw_saat_ini)
        kw_value = float(kw_value)
        if kw_value == 0:
            return
        
        percentage = (kw_saat_ini / kw_value) * 100

        if percentage > 10:
            send_notification(bot, TELEGRAM_BOT_CHAT_ID, site_code, port_id, kw_saat_ini, percentage)
    except ValueError:
        pass

def get_all_status_data():
    conn = mysql.connector.connect(**database)
    cursor = conn.cursor()

    query = "SELECT site_code, port_id, status FROM tbl_data_analog;"
    cursor.execute(query)
    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data

def check_and_notify_status(bot):
    all_status_data = get_all_status_data()
    for site_code, port_id, status in all_status_data:
        calculate_percentage_kw(site_code, port_id, status, status, bot)

def start(update, context):
    user_id = update.effective_chat.id
    context.chat_data[user_id] = {}

    check_and_notify_status(context.bot) 
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_notify_status, trigger='interval', seconds=360, args=[updater.bot])
    scheduler.start()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()