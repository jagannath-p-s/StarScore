from flask import Flask, render_template, jsonify, send_file
from bs4 import BeautifulSoup
import requests
import supabase

app = Flask(__name__)

# Supabase configuration
SUPABASE_URL = "https://ldkbzfcoewzynxawicxg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxka2J6ZmNvZXd6eW54YXdpY3hnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTU4NjQwMDQsImV4cCI6MjAzMTQ0MDAwNH0.sE_JK5ZbobAOzWKR6osasEVfZPWhVt08NhRf0XgrsmA"

sb = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/favicon.ico')
def favicon():
    return send_file('favicon.ico', mimetype='image/x-icon')

def extract_review_count(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        review_span = soup.find('span', string=lambda text: text and '(' in text and ')' in text)

        if review_span:
            review_count_text = review_span.get_text(strip=True)
            review_count = ''.join(filter(str.isdigit, review_count_text))
            return int(review_count)
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error: An error occurred while fetching the website: {e}")
        return None

def get_client_data(client_id):
    try:
        clients_table = sb.table('clients')
        record = clients_table.select('reviewurl', 'extractionurl', 'logourl', 'review_count').eq('id', client_id).execute()
        if record.data:
            return record.data[0]
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def insert_or_update_review_count(client_id, count):
    try:
        review_counts_table = sb.table('clients')
        review_counts_table.update({"review_count": count}).eq('id', client_id).execute()
    except Exception as e:
        print(f"Error: {e}")

def update_salesman_points(salesman_id):
    try:
        salesmen_table = sb.table('salesmen')
        record = salesmen_table.select('points').eq('id', salesman_id).execute()
        if record.data:
            current_points = record.data[0]['points'] or 0
            new_points = current_points + 1
            salesmen_table.update({"points": new_points}).eq('id', salesman_id).execute()
    except Exception as e:
        print(f"Error: {e}")

def insert_client_salesman_activity(client_id, salesman_id):
    try:
        client_salesman_activity_table = sb.table('client_salesman_activity')
        client_salesman_activity_table.insert({"client_id": client_id, "salesman_id": salesman_id}).execute()
    except Exception as e:
        print(f"Error: {e}")

@app.route('/app/<int:client_id>/<int:salesman_id>')
def app_route(client_id, salesman_id):
    client_data = get_client_data(client_id)
    if client_data:
        review_url = client_data['reviewurl']
        logo_url = client_data['logourl']

        # Perform extraction and update
        new_count = extract_review_count(client_data['extractionurl'])
        if new_count is not None:
            insert_or_update_review_count(client_id, new_count)

        current_review_count = new_count  # Directly using the newly extracted count
        if current_review_count is not None:
            return render_template('review.html', salesman_id=salesman_id, review_count=current_review_count, review_url=review_url, logo_url=logo_url, client_id=client_id)
        else:
            return "Error fetching review count from database."
    else:
        return "Invalid client ID."

@app.route('/check_review_increment/<int:client_id>/<int:salesman_id>', methods=['GET'])
def check_review_increment(client_id, salesman_id):
    client_data = get_client_data(client_id)
    if not client_data:
        return jsonify({"status": "error", "message": "Invalid client ID."})

    initial_count = client_data.get('review_count', 0)

    new_count = extract_review_count(client_data['extractionurl'])
    if new_count is None:
        return jsonify({"status": "error", "message": "Error fetching new review count."})

    if new_count > initial_count:
        insert_or_update_review_count(client_id, new_count)
        update_salesman_points(salesman_id)
        insert_client_salesman_activity(client_id, salesman_id)
        return jsonify({"status": "success", "message": f"New review submitted. The total number of reviews is now {new_count}.", "new_count": new_count})
    else:
        return jsonify({"status": "error", "message": "No new reviews submitted."})

@app.route('/')
def index():
    return "This application is used to track and incentivize customer reviews."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
