from flask import Flask, render_template, jsonify, request
import mysql.connector
import pandas as pd 
from datetime import datetime
import requests

database = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'proyek'
}

app = Flask(__name__)


def get_top_high_data():
    conn = mysql.connector.connect(**database)
    cursor = conn.cursor()

    # Get the site_code and its maximum status value
    query = "SELECT site_code, MAX(CAST(status AS DECIMAL(10,2))) AS max_status FROM tbl_data_analog GROUP BY site_code ORDER BY max_status DESC LIMIT 3;"
    cursor.execute(query)
    data = cursor.fetchall()

    # Fetch the complete row data for each site_code and its maximum status
    top_high_data = []
    for row in data:
        site_code = row[0]
        max_status = row[1]
        
        query = "SELECT * FROM tbl_data_analog WHERE site_code = %s AND CAST(status AS DECIMAL(10,2)) = %s ORDER BY datetime_stamp DESC LIMIT 1;"
        cursor.execute(query, (site_code, max_status))
        site_data = cursor.fetchone()
        
        top_high_data.append(site_data)

    cursor.close()
    conn.close()

    return top_high_data

def calculate_percentage(value, batasKW1):
    if batasKW1 is None or batasKW1 == 0:
        return 'NaN%'

    percentage = (value / batasKW1) * 100
    return f'{percentage:.2f}%'

def get_site_codes_by_region(region):
    try:
        conn = mysql.connector.connect(**database)
        cursor = conn.cursor()

        query = f"SELECT DISTINCT site_code FROM tbl_data_analog WHERE wilayah = '{region}';"
        cursor.execute(query)
        site_codes = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify(site_codes) 

    except Exception as e:
        print(f"Error fetching site codes: {e}")
        return jsonify([]) 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data_analog')
def display_data_analog():
    data = get_data_analog()
    return jsonify(data)

@app.route('/top_high')
def display_top_high():
    data = get_top_high_data()
    return jsonify(data)



@app.route('/table.html')
def show_table_html():
    return render_template('table.html')

@app.route('/show_table')
def show_table_data():
    return render_template('table.html')

@app.route('/save_data', methods=['POST'])
def save_data():
    try:
        data = request.form
        site_code = data.get('site_code')
        killow1 = data.get('killow1')
        killow2 = data.get('killow2')
        persentase = data.get('persentase')

        # Validate input (ensure site_code, killow1, and killow2 are provided)

        # Insert or update the data in the database
        conn = mysql.connector.connect(**database)
        cursor = conn.cursor()

        # Check if the record for the site_code already exists
        query = "SELECT * FROM tbl_data_analog WHERE site_code = %s;"
        cursor.execute(query, (site_code,))
        existing_data = cursor.fetchone()

        if existing_data:
            # Update the existing record
            update_query = "UPDATE tbl_data_analog SET killow1 = %s, killow2 = %s, persentase = %s WHERE site_code = %s;"
            cursor.execute(update_query, (killow1, killow2, persentase, site_code))
        else:
            # Insert a new record
            insert_query = "INSERT INTO tbl_data_analog (site_code, killow1, killow2, persentase) VALUES (%s, %s, %s, %s);"
            cursor.execute(insert_query, (site_code, killow1, killow2, persentase))

        conn.commit()
        cursor.close()
        conn.close()

        return "Data saved successfully."

    except Exception as e:
        print("Error saving data:", e)
        return "An error occurred while saving data."

@app.route('/get_analog_data', methods=['POST'])
def get_analog_data():
    wilayah = request.form.get('wilayah')
    try:
        conn = mysql.connector.connect(**database)
        cursor = conn.cursor()

        query = "SELECT * FROM tbl_data_analog WHERE wilayah = %s ORDER BY datetime_stamp DESC LIMIT 40;"
        cursor.execute(query, (wilayah,))
        result = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(result)

    except Exception as e:
        print("Error fetching analog data:", e)
        return jsonify([])
@app.route('/get_saved_analog_data', methods=['POST'])
def get_saved_analog_data():
    wilayah = request.form.get('wilayah')
    try:
        conn = mysql.connector.connect(**database)
        cursor = conn.cursor()

        query = "SELECT * FROM tbl_data_analog WHERE wilayah = %s ORDER BY datetime_stamp DESC LIMIT 40;"
        cursor.execute(query, (wilayah,))
        result = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(result)

    except Exception as e:
        print("Error fetching analog data:", e)
        return jsonify([])
def get_analog_data_by_wilayah_and_hour(wilayah, jam):
    try:
        conn = mysql.connector.connect(**database)
        cursor = conn.cursor()

        if jam == 'killow1':
            query = "SELECT * FROM tbl_data_analog WHERE wilayah = %s AND HOUR(datetime_stamp) >= 0 AND HOUR(datetime_stamp) < 12 ORDER BY datetime_stamp DESC LIMIT 7;"
        elif jam == 'killow2':
            query = "SELECT * FROM tbl_data_analog WHERE wilayah = %s AND HOUR(datetime_stamp) >= 12 AND HOUR(datetime_stamp) < 24 ORDER BY datetime_stamp DESC LIMIT 7;"
        else:
            return []

        cursor.execute(query, (wilayah,))
        result = cursor.fetchall()

        cursor.close()
        conn.close()

        return result

    except Exception as e:
        print("Error fetching analog data:", e)
        return []
@app.route('/update_kw_values', methods=['POST'])
def update_kw_values():
    data = request.form.to_dict()
    site_code = data.get('site_code')
    kw1 = data.get('kw1')
    kw2 = data.get('kw2')

    if site_code and kw1 and kw2:
        try:
            conn = mysql.connector.connect(**database)
            cursor = conn.cursor()

            # Update the database with the locked values
            query = "UPDATE tbl_data_analog SET batas1 = %s, batas2 = %s WHERE site_code = %s;"
            cursor.execute(query, (kw1, kw2, site_code))
            conn.commit()

            cursor.close()
            conn.close()

            return 'Data berhasil diperbarui di server.'
        except Exception as e:
            return f'Error: {e}'
    else:
        return 'Site Code, kw1, dan kw2 harus disediakan.'


@app.route('/download_excel', methods=['POST'])
def download_excel():
    print("Request received for downloading Excel file.")
    wilayah = request.form.get('wilayah')
    try:
        conn = mysql.connector.connect(**database)
        query = "SELECT * FROM tbl_data_analog WHERE wilayah = %s ORDER BY datetime_stamp DESC;"
        df = pd.read_sql_query(query, conn, params=[wilayah])

        df['datetime_stamp'] = pd.to_datetime(df['datetime_stamp'])

        df.rename(columns={'waktu': 'datetime_stamp'}, inplace=True)

        # Simpan dataframe ke dalam file Excel
        excel_file = f"{wilayah}_data_analog.xlsx"
        df.to_excel(excel_file, index=False, engine='openpyxl')

        conn.close()

        # Mengirimkan file Excel sebagai respon
        return send_file(excel_file, as_attachment=True, attachment_filename=excel_file)

    except Exception as e:
        print("data masuk ke dalam file:", e)
        return "Data terdownload,masuk ke file."
def get_last_data_per_region():
    wilayah = request.form.get('wilayah')

    try:
        conn = mysql.connector.connect(**database)
        cursor = conn.cursor()
        query = "SELECT wilayah, site_code, status, flag FROM tbl_data_analog WHERE wilayah = %s ORDER BY datetime_stamp DESC LIMIT 1;"
        cursor.execute(query, (wilayah,))
        result = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(result)

    except Exception as e:
        print("Error fetching last data per region:", e)
        return jsonify([])

@app.route('/show_history_data')
def show_history_data():
    return render_template('history.html')

@app.route('/get_last_site_code_and_timestamp')
def get_last_site_code_and_timestamp():
    try:
        conn = mysql.connector.connect(**database)
        cursor = conn.cursor()

        # Query SQL untuk mengambil data site code dan datetime_stamp terakhir dari setiap wilayah
        query = "SELECT wilayah, site_code, datetime_stamp FROM nama_tabel GROUP BY wilayah;"
        cursor.execute(query)
        result = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(result)

    except Exception as e:
        print("Error fetching last site code and timestamp:", e)
        return jsonify([])

@app.route('/get_site_code_and_timestamp', methods=['POST'])
def get_site_code_and_timestamp():
    wilayah = request.form['wilayah']
    tanggal = request.form['tanggal']

    try:
        conn = mysql.connector.connect(**database)
        cursor = conn.cursor()

        # Konversi tanggal dari string ke objek datetime
        date_obj = datetime.strptime(tanggal, '%Y-%m-%d')

        # Query SQL untuk mengambil data berdasarkan wilayah dan tanggal yang dipilih
        query = "SELECT wilayah, site_code, datetime_stamp FROM nama_tabel WHERE wilayah = %s AND DATE(datetime_stamp) = %s ORDER BY datetime_stamp DESC;"
        cursor.execute(query, (wilayah, date_obj))
        result = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(result)

    except Exception as e:
        print("Error fetching site code and timestamp:", e)
        return jsonify([])
    return jsonify({'last_date': last_date})

def get_history_data_by_region_and_date(wilayah, tanggal, search_site_code=None):
    try:
        conn = mysql.connector.connect(**database)
        cursor = conn.cursor()

        # Konversi tanggal dari string ke objek datetime
        date_obj = datetime.strptime(tanggal, '%Y-%m-%d')

        # Build the SQL query based on whether search_site_code is provided
        if search_site_code:
            query = "SELECT site_code, status, flag, datetime_stamp FROM tbl_data_analog WHERE wilayah = %s AND DATE(datetime_stamp) = %s AND site_code = %s ORDER BY datetime_stamp DESC;"
            cursor.execute(query, (wilayah, date_obj, search_site_code))
        else:
            query = "SELECT site_code, status, flag, datetime_stamp FROM tbl_data_analog WHERE wilayah = %s AND DATE(datetime_stamp) = %s ORDER BY datetime_stamp DESC;"
            cursor.execute(query, (wilayah, date_obj))
            
        result = cursor.fetchall()

        cursor.close()
        conn.close()

        print("Hasil dari database:", result)  # Tambahkan baris ini untuk debugging

        return result

    except Exception as e:
        print("Error fetching history data:", e)
        return []




@app.route('/get_history_data', methods=['POST'])
def get_history_data():
    wilayah = request.form.get('wilayah')
    tanggal = request.form.get('tanggal')
    search_site_code = request.form.get('searchSiteCode')
    
    data = get_history_data_by_region_and_date(wilayah, tanggal, search_site_code)
    return jsonify(data)


@app.route('/get_last_date_per_region', methods=['POST'])
def get_last_date_per_region():
    wilayah = request.form.get('wilayah')

    conn = mysql.connector.connect(**database)
    df = pd.read_sql_query("SELECT DISTINCT tanggal FROM tbl_data_analog WHERE wilayah = %s ORDER BY tanggal DESC LIMIT 1", conn, params=[wilayah])
    conn.close()

    last_date = None
    if not df.empty:
        last_date = df['tanggal'].iloc[0]

    return jsonify({'last_date': last_date})


if __name__ == '__main__':
    app.run(debug=True)
