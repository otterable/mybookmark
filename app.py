from flask import Flask, render_template, request, jsonify
import os
from PIL import Image
from io import BytesIO
import base64
import random
import string
import stripe
from flask_cors import CORS  # Import CORS
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)  # Enable CORS for the app
app.config['UPLOAD_FOLDER'] = 'static/useruploads'
stripe.api_key = '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'  # Replace with your Stripe secret key
    
# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        return filename


@app.route('/editor')
def editor():
    # Additional logic can be added here if needed
    return render_template('editor.html')
    
@app.route('/ueber')
def ueber():
    # Additional logic can be added here if needed
    return render_template('ueber.html')

@app.route('/ideen')
def ideen():
    # Additional logic can be added here if needed
    return render_template('ideen.html')

@app.route('/preisliste')
def preisliste():
    # Additional logic can be added here if needed
    return render_template('preisliste.html')
    
@app.route('/save_motive', methods=['POST'])
def save_motive():
    data = request.form['imageData']
    # Remove the prefix that comes before the base64 data
    image_data = data.split(",")[1]

    # Decode the base64 image data
    try:
        decoded_image_data = base64.b64decode(image_data)
    except Exception as e:
        return f"Error decoding image data: {e}", 500

    # Open the image and generate a random filename
    try:
        image = Image.open(BytesIO(decoded_image_data))
    except Exception as e:
        return f"Error opening image: {e}", 500

    random_numbers = ''.join(random.choices(string.digits, k=10))
    filename = f'Bestellnummer: {random_numbers}.png'
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Save the image
    try:
        image.save(filepath)
    except Exception as e:
        return f"Error saving image: {e}", 500

    return filepath

def create_checkout_session_common(file_name, timestamp, unit_amount, copies, size):
    description = f'# Lesezeichen: {copies}, Größe: {size}; {file_name}, {timestamp}'
    total_amount = unit_amount * copies
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {'name': description},
                    'unit_amount': unit_amount,
                },
                'quantity': copies,
            }],
            mode='payment',
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
        )
        return jsonify({'id': session.id})
    except Exception as e:
        return str(e), 403


@app.route('/create-checkout-session/<int:price>/<int:copies>/<size>', methods=['POST'])
def create_checkout_session(price, copies, size):
    file_path = request.form['fileName']
    timestamp_iso = request.form['timestamp']
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    utc_time = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
    utc_plus_one = utc_time.astimezone(pytz.timezone('Europe/Berlin'))
    formatted_timestamp = utc_plus_one.strftime("%d.%m.%Y, %H:%M")
    return create_checkout_session_common(file_name, formatted_timestamp, price, copies, size)



if __name__ == '__main__':
    app.run(debug=True)
