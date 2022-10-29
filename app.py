import imghdr
from flask import Flask, request, jsonify, make_response
from werkzeug.utils import secure_filename
import dlib
import cv2
import face_recognition
import os
import postgresql


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.jpeg']
app.config['UPLOAD_PATH'] = 'uploads'


def save_face_to_db(local_filename, remote_file_url):
    # Create a HOG face detector using the built-in dlib class
    face_detector = dlib.get_frontal_face_detector()

    # Load the image
    image = cv2.imread(local_filename)

    # Run the HOG face detector on the image data
    detected_faces = face_detector(image, 1)
    print("Found {} faces in the image file {}".format(len(detected_faces), local_filename))

    db = postgresql.open(os.environ.get('DATABASE_STRING'))

    # Loop through each face we found in the image
    for i, face_rect in enumerate(detected_faces):
        # Detected faces are returned as an object with the coordinates
        # of the top, left, right and bottom edges
        print("- Face #{} found at Left: {} Top: {} Right: {} Bottom: {}".format(i, face_rect.left(), face_rect.top(),
                                                                                 face_rect.right(), face_rect.bottom()))
        crop = image[face_rect.top():face_rect.bottom(), face_rect.left():face_rect.right()]
        encodings = face_recognition.face_encodings(crop)

        if len(encodings) > 0:
            query = "INSERT INTO vectors (file, vec_low, vec_high) VALUES ('{}', CUBE(array[{}]), CUBE(array[{}]))".format(
                remote_file_url,
                ','.join(str(s) for s in encodings[0][0:64]),
                ','.join(str(s) for s in encodings[0][64:128]),
            )
            db.execute(query)
            return True
    return False


def find_face_in_db(local_filename):
    # Create a HOG face detector using the built-in dlib class
    face_detector = dlib.get_frontal_face_detector()

    # Load the image
    image = cv2.imread(local_filename)

    # Run the HOG face detector on the image data
    detected_faces = face_detector(image, 1)

    print("Found {} faces in the image file {}".format(len(detected_faces), local_filename))

    db = postgresql.open(os.environ.get('DATABASE_STRING'))

    # Loop through each face we found in the image
    for i, face_rect in enumerate(detected_faces):
        # Detected faces are returned as an object with the coordinates
        # of the top, left, right and bottom edges
        print("- Face #{} found at Left: {} Top: {} Right: {} Bottom: {}".format(i, face_rect.left(), face_rect.top(),
                                                                                 face_rect.right(), face_rect.bottom()))
        crop = image[face_rect.top():face_rect.bottom(), face_rect.left():face_rect.right()]

        encodings = face_recognition.face_encodings(crop)
        threshold = 0.6
        if len(encodings) > 0:
            query = "SELECT file FROM vectors WHERE sqrt(power(CUBE(array[{}]) <-> vec_low, 2) + power(CUBE(array[{}]) <-> vec_high, 2)) <= {} ".format(
                ','.join(str(s) for s in encodings[0][0:64]),
                ','.join(str(s) for s in encodings[0][64:128]),
                threshold,
            ) + \
                    "ORDER BY sqrt(power(CUBE(array[{}]) <-> vec_low, 2) + power(CUBE(array[{}]) <-> vec_high, 2)) ASC".format(
                        ','.join(str(s) for s in encodings[0][0:64]),
                        ','.join(str(s) for s in encodings[0][64:128]),
                    )
            return db.query(query)
        else:
            return []


def validate_image(stream):
    header = stream.read(512)  # 512 bytes should be enough for a header check
    stream.seek(0)  # reset stream pointer
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')


@app.errorhandler(413)
def uploaded_file_too_large(e):
    return make_response(jsonify(error='File too large'), 413)


@app.route('/', methods=['GET'])
def index():
    return 'Hello There!'


@app.route("/faces", methods=['POST'])
def faces():
    uploaded_file = request.files['file']
    file_url = request.form.get('url', False)
    filename = secure_filename(uploaded_file.filename)
    if filename != '' and file_url:
        file_ext = os.path.splitext(filename)[1]
        if file_ext in app.config['UPLOAD_EXTENSIONS']:  # and file_ext == validate_image(uploaded_file.stream):
            file_path = os.path.join(app.config['UPLOAD_PATH'], filename)
            uploaded_file.save(file_path)
            face_added = save_face_to_db(file_path, file_url)
            os.remove(file_path)
            if face_added:
                return make_response(jsonify(status='PROCESSED'), 201)
            else:
                return make_response(jsonify(status='FAILED'), 500)
    return make_response(jsonify(error='Invalid file or URL'), 400)


@app.route('/faces/searches', methods=['POST'])
def faces_searches():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext in app.config['UPLOAD_EXTENSIONS']:  # and file_ext == validate_image(uploaded_file.stream):
            file_path = os.path.join(app.config['UPLOAD_PATH'], filename)
            uploaded_file.save(file_path)
            face_matches = find_face_in_db(file_path)
            os.remove(file_path)
            return make_response(jsonify(matches=[item for sublist in face_matches for item in sublist]), 200)
    return make_response(jsonify(error='Invalid file'), 400)


if __name__ == "__main__":
    app.run(debug=True, port=9000)
