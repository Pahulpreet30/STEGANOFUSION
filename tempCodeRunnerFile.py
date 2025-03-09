from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session,send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import wave
import io
import numpy as np
import cv2
# import io
from werkzeug.utils import secure_filename
import os
from io import BytesIO
import concurrent.futures
from video import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jhdjdkjdlajflj'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///hello.db"
app.config['SQLALCHEMY_BINDS'] = {
    'second_db': 'sqlite:///second_db.db'  # Replace with your actual database URI
}


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    First_Name = db.Column(db.String(200), nullable=False)
    Last_Name = db.Column(db.String(200))
    Password = db.Column(db.String(200), nullable=False)

def getInitials(email):
    name_parts = email.split('@')[0].split('.')
    first_initial = name_parts[0][0].upper() if name_parts else ''
    last_initial = name_parts[1][0].upper() if len(name_parts) > 1 else ''
    return first_initial + last_initial


class SecondData(db.Model):
    __bind_key__ = 'second_db'  # Bind this model to the second database
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(2000), nullable=False)



def encode_audio_data(audio_file, message):
    # Open audio file
    song = wave.open(audio_file, mode='rb')
    frame_bytes = bytearray(list(song.readframes(song.getnframes())))

    # Add a delimiter to mark the end of the message
    message += '*^*^*'
    bits = ''.join(format(ord(char), '08b') for char in message)

    # Modify the audio bytes
    for i, bit in enumerate(bits):
        frame_bytes[i] = (frame_bytes[i] & 254) | int(bit)

    # Save modified bytes into new audio file in memory
    modified_audio = io.BytesIO()
    with wave.open(modified_audio, 'wb') as stego_audio:
        stego_audio.setparams(song.getparams())
        stego_audio.writeframes(frame_bytes)
    song.close()
    modified_audio.seek(0)  # Reset the pointer to the start of the file
    return modified_audio 

def decode_audio_data(audio_file):
    # Open the audio file
    song = wave.open(audio_file, mode='rb')
    frame_bytes = bytearray(list(song.readframes(song.getnframes())))
    song.close()

    # Extract LSBs from each byte
    extracted_bits = [str((byte & 1)) for byte in frame_bytes]
    extracted_message_bits = ''.join(extracted_bits)

    # Convert bits back to characters
    message = ""
    for i in range(0, len(extracted_message_bits), 8):
        byte = extracted_message_bits[i:i+8]
        char = chr(int(byte, 2))
        message += char
        if message[-5:] == "*^*^*":  # Stop at delimiter
            return message[:-5]  # Return the message without the delimiter
    return "No hidden message found."

# image encoding decoding
def msgtobinary(msg):
    if isinstance(msg, str):
        return ''.join(format(ord(i), "08b") for i in msg)
    elif isinstance(msg, (bytes, np.ndarray)):
        return [format(i, "08b") for i in msg]
    elif isinstance(msg, (int, np.uint8)):
        return format(msg, "08b")
    else:
        raise TypeError("Unsupported data type for binary conversion")

def encode_img_data(img, data):
    data += '*^*^*'
    binary_data = msgtobinary(data)
    data_len = len(binary_data)
    
    if data_len > img.size * 3:
        raise ValueError("Insufficient space in image for data")
    
    # Vectorized operations for encoding
    binary_data_array = np.array(list(binary_data) + ['0'] * (img.size * 3 - len(binary_data)), dtype=str)
    binary_data_array = binary_data_array[:img.size * 3]
    
    # Reshape image and perform operations
    flat_img = img.reshape(-1, 3)
    for channel in range(3):
        channel_data = binary_data_array[channel::3][:len(flat_img)]
        binary_pixels = np.array([format(p, '08b')[:-1] for p in flat_img[:len(channel_data), channel]])
        flat_img[:len(channel_data), channel] = np.array([int(b + d, 2) 
                                                         for b, d in zip(binary_pixels, channel_data)])
    
    return flat_img.reshape(img.shape)

def decode_chunk(args):
    chunk, chunk_size = args
    binary_data = ''
    for pixel in chunk:
        for channel in pixel:
            binary_data += format(channel, '08b')[-1]
    return binary_data

def decode_img_data(img):
    # Split image into chunks for parallel processing
    chunks = np.array_split(img.reshape(-1, 3), max(1, img.size // 10000))
    chunk_sizes = [len(chunk) for chunk in chunks]
    
    # Process chunks in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        binary_chunks = list(executor.map(decode_chunk, zip(chunks, chunk_sizes)))
    
    binary_data = ''.join(binary_chunks)
    
    # Convert binary to text more efficiently
    decoded_data = ''
    for i in range(0, len(binary_data) - 7, 8):
        byte = binary_data[i:i+8]
        if not byte.strip('01'):  # Validate binary string
            try:
                decoded_data += chr(int(byte, 2))
                # Check for delimiter every few characters
                if len(decoded_data) >= 5 and decoded_data[-5:] == '*^*^*':
                    return decoded_data[:-5]
            except ValueError:
                continue
    
    return "No hidden message found"



@app.route("/", methods=['GET'])
def home():
    return render_template("index.html")

@app.route("/signup", methods=['POST'])
def signup():
    if request.method == "POST":
        email1 = request.form.get("email1")
        FirstName = request.form.get("FirstName")
        LastName = request.form.get("LastName")
        Password1 = request.form.get("Password1")
        Password2 = request.form.get("Password2")
        
        user = User.query.filter_by(email=email1).first()
        
        if user:
            flash("User Already Exists", category="error")
        elif len(email1) < 4:
            flash("Email must be greater than 4 characters", category="error")
        elif len(FirstName) < 1:
            flash("First Name must have at least one character", category="error")
        elif Password1 != Password2:
            flash("Passwords do not match", category="error")
        elif len(Password1) < 7:
            flash("Password must contain at least 8 characters", category="error")
        else:
            new_user = User(
                email=email1,
                First_Name=FirstName,
                Last_Name=LastName,
                Password=generate_password_hash(Password1, method="scrypt")
            )
            try:
                db.session.add(new_user)
                db.session.commit()
                flash("Account created successfully!", category="success")
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred: {str(e)}", category="error")
    
    return redirect(url_for('home'))


@app.route("/audio", methods=['GET', 'POST'])
def audio():
    if request.method == 'POST':
        # Separate encoding from decoding based on the presence of 'baseFile' or 'decodeFile'
        if 'baseFile' in request.files:  # Encoding process
            audio_file = request.files['baseFile']
            message = request.form['message']
            
            # Encode message in the audio file
            encoded_audio = encode_audio_data(audio_file, message)

            # Send the encoded file back to the user
            return send_file(encoded_audio, as_attachment=True, download_name="encoded_audio.wav", mimetype="audio/wav")
        
        elif 'decodeFile' in request.files:  # Decoding process
            audio_file = request.files['decodeFile']
            hidden_message = decode_audio_data(audio_file)
            return jsonify({"message": hidden_message})  # Send message back to frontend

    return render_template('new2.html')


@app.route("/image", methods=['GET', 'POST'])
def image_steg():
    if request.method == 'POST':
        if 'imageFile' in request.files:
            image_file = request.files['imageFile']
            message = request.form['message']
            
            img = cv2.imdecode(np.frombuffer(image_file.read(), np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                return jsonify({"error": "Invalid image file"}), 400
            
            encoded_image = encode_img_data(img, message)
            _, buffer = cv2.imencode('.png', encoded_image)
            encoded_image_io = io.BytesIO(buffer)
            return send_file(encoded_image_io, 
                           as_attachment=True, 
                           download_name="encoded_image.png", 
                           mimetype="image/png")
            
        elif 'decodeFile' in request.files:
            image_file = request.files['decodeFile']
            img = cv2.imdecode(np.frombuffer(image_file.read(), np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                return jsonify({"error": "Invalid image file"}), 400
            
            hidden_message = decode_img_data(img)
            return jsonify({"message": hidden_message})
    
    return render_template('image.html')


@app.route('/video', methods=['GET', 'POST'])
def video_steganography():
    if request.method == 'POST':
        if 'videoFile' in request.files:
            # Save uploaded video
            video_file = request.files['videoFile']
            video_path = os.path.join('uploads', video_file.filename)
            video_file.save(video_path)

            frame_number = int(request.form['frame'])
            key = request.form['key']
            data = request.form['message']
            new_message = SecondData(data=data)
            db.session.add(new_message)
            db.session.commit()
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return render_template('video.html', error='Error: Unable to open the video file.')

            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            out = cv2.VideoWriter('stego_video.mp4', fourcc, fps, (frame_width, frame_height))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if total_frames == 0:
                cap.release()
                return render_template('video.html', error='Error: The video file has no frames.')

            current_frame = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                current_frame += 1
                if current_frame == frame_number:
                    modified_frame = embed(frame, data, key)
                    out.write(modified_frame)
                else:
                    out.write(frame)

            cap.release()
            out.release()
            return send_file('stego_video.mp4', as_attachment=True)

        elif 'decodeFile' in request.files:
            # Decode video
            decode_file = request.files['decodeFile']
            decode_path = os.path.join('uploads', decode_file.filename)
            decode_file.save(decode_path)
            saved_message = SecondData.query.first()  # Get the first message from the database

            if saved_message:
                return render_template('video.html', decoded_message=saved_message.data)  # Show the saved message
            else:
                return render_template('video.html', error='Error: No saved message found in the database.')

    return render_template('video.html')



@app.route("/login", methods=['POST'])
def login():
    if request.method == "POST":
        email1 = request.form.get("email1")
        Password1 = request.form.get("Password1")
       
        user = User.query.filter_by(email=email1).first()
        if user and check_password_hash(user.Password, Password1):
            # Store only necessary fields in the session
            session['user'] = {
                'id': user.id,
                'email': user.email,
                'name': f"{user.First_Name} {user.Last_Name or ''}".strip(),
                'initials': getInitials(user.email)
            }
            flash("Logged in Successfully!", category="success")
            return redirect(url_for('home'))
        else:
            flash("Incorrect Email or Password, Try Again", category="error")
    return redirect(url_for('home'))



@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True, port=7000)
