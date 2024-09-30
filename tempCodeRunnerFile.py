import logging
from flask import Flask, request, render_template, url_for, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import numpy as np
import tensorflow as tf
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

# Ensure the directory for uploads exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Database model for User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

# Create database tables
with app.app_context():
    db.create_all()

# Load the trained model
model = tf.keras.models.load_model('Tomato_leaf_disease_detection_classification2.h5')

# Define allowed file extensions for image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', "JPG"}

# Disease labels
disease_labels = ['Bacterial_spot', 'Early_blight', 'Late_blight', 'Leaf_Mold',
                  'Septoria_leaf_spot', 'Spider_mites_Two-spotted_spider_mite',
                  'Target_Spot', 'Tomato_Yellow_Leaf_Curl_Virus', 'Tomato_mosaic_virus',
                  'Healthy']

# Knowledge Base

diseases = {
    'Early Blight': {
        'symptoms': 'dark concentric spots on older leaves, yellowing around the spots, lesions on stems and fruit',
        'treatment': 'Remove affected plant parts, use fungicides containing chlorothalonil or copper, rotate crops and avoid overhead watering'
    },
    'Late Blight': {
        'symptoms': 'water-soaked spots on leaves and stems, white mold growth on the underside of leaves, brown, rotting patches on fruit',
        'treatment': 'Remove and destroy infected plants, apply fungicides like mancozeb or chlorothalonil, ensure good air circulation and avoid wetting foliage'
    },
    'Septoria Leaf Spot': {
        'symptoms': 'small circular spots with dark borders and gray centers on leaves, leaf yellowing and drop starting from the bottom of the plant',
        'treatment': 'Remove and destroy infected leaves, apply fungicides such as chlorothalonil or copper sprays, avoid overhead watering and rotate crops'
    },
    'Fusarium Wilt': {
        'symptoms': 'yellowing of leaves, often starting on one side, wilting of leaves and stems, especially during the day, brown discoloration inside the stem',
        'treatment': 'Use resistant tomato varieties, rotate crops and solarize soil, ensure good drainage and avoid overwatering'
    },
    'Verticillium Wilt': {
        'symptoms': 'yellowing and wilting of lower leaves, brown discoloration in the stem\'s vascular tissue, stunted growth and poor yield',
        'treatment': 'Use resistant tomato varieties, rotate crops and avoid planting in infected soil, remove and destroy affected plants'
    },
    'Tomato Mosaic Virus': {
        'symptoms': 'mottled light and dark green patterns on leaves, distorted or stunted growth, yellow streaking on flowers and fruit',
        'treatment': 'Remove and destroy infected plants, disinfect tools and hands after handling plants, use resistant varieties and control aphid populations'
    },
    'Tomato Spotted Wilt Virus': {
        'symptoms': 'bronze or purple spots on young leaves, wilting and necrosis of leaves, ring spots on fruit and deformed fruit growth',
        'treatment': 'Remove and destroy infected plants, control thrips, use resistant varieties and apply insecticides if necessary'
    },
    'Bacterial Spot': {
        'symptoms': 'small water-soaked spots on leaves, stems, and fruit, spots enlarge and become brown with a yellow halo, fruit may have black, scabby spots',
        'treatment': 'Remove and destroy infected plant parts, apply copper-based bactericides, avoid working with wet plants and rotate crops'
    },
    'Bacterial Speck': {
        'symptoms': 'small dark spots on leaves and fruit, yellow halos around leaf spots, raised, black spots on fruit',
        'treatment': 'Use disease-free seeds and transplants, apply copper-based bactericides, practice crop rotation and avoid overhead watering'
    },
    'Powdery Mildew': {
        'symptoms': 'white powdery growth on leaves, stems, and buds, yellowing and browning of leaves, stunted plant growth',
        'treatment': 'Remove affected leaves, apply sulfur or potassium bicarbonate fungicides, improve air circulation and avoid excess nitrogen fertilization'
    },
    'Anthracnose': {
        'symptoms': 'small sunken circular spots on ripe fruit, spots enlarge and become dark with concentric rings, fruit rots quickly after spotting',
        'treatment': 'Remove and destroy infected fruit, apply fungicides such as chlorothalonil, rotate crops and avoid overhead watering'
    },
    'Blossom-End Rot': {
        'symptoms': 'dark sunken spots on the blossom end of the fruit, spots enlarge and turn leathery, affected fruits may rot',
        'treatment': 'Maintain consistent soil moisture, ensure adequate calcium in the soil, avoid excessive nitrogen fertilization'
    },
    'Root Knot Nematodes': {
        'symptoms': 'swollen galled roots, stunted plant growth, yellowing and wilting of leaves',
        'treatment': 'Use resistant varieties, rotate crops and solarize soil, apply nematicides if necessary'
    },
    'Grey Mold (Botrytis cinerea)': {
        'symptoms': 'gray fuzzy mold on leaves, stems, and fruit, brown, water-soaked spots on leaves, fruit rot with gray mold',
        'treatment': 'Remove and destroy infected plant parts, apply fungicides like chlorothalonil or copper, ensure good air circulation and avoid wetting foliage'
    },
    'Buckeye Rot': {
        'symptoms': 'water-soaked spots on fruit, typically near the soil line, spots enlarge and develop concentric rings, fruit rots and becomes mushy',
        'treatment': 'Avoid contact of fruit with soil, apply fungicides like chlorothalonil or copper, improve soil drainage and use mulch to reduce soil splashing'
    },
    'Southern Blight': {
        'symptoms': 'wilting of plants, starting at the base, white, fan-like fungal growth on the stem near soil line, brown, sunken lesions on stems',
        'treatment': 'Remove and destroy infected plants, apply fungicides such as tebuconazole, rotate crops and solarize soil'
    },
    'Bacterial Wilt': {
        'symptoms': 'sudden wilting of plants, brown discoloration of vascular tissue, sticky, bacterial ooze from cut stems',
        'treatment': 'Remove and destroy infected plants, use resistant varieties, ensure good drainage and avoid overwatering'
    },
    'Alternaria Stem Canker': {
        'symptoms': 'dark sunken lesions on stems and fruit, leaf spots with concentric rings, wilting and defoliation',
        'treatment': 'Remove and destroy infected plant parts, apply fungicides like chlorothalonil, rotate crops and ensure good air circulation'
    }
    
    }

# Symptom-question mapping
symptom_questions = {
    'dark concentric spots on older leaves': 'Did you notice dark concentric spots on older leaves?',
    'yellowing around the spots': 'Is there yellowing around the spots?',
    'lesions on stems and fruit': 'Are there lesions on stems and fruit?',
    'water-soaked spots on leaves and stems': 'Did you notice water-soaked spots on leaves and stems?',
    'white mold growth on the underside of leaves': 'Is there white mold growth on the underside of leaves?',
    'brown, rotting patches on fruit': 'Do you see brown, rotting patches on fruit?',
    'small circular spots with dark borders and gray centers on leaves': 'Are there small circular spots with dark borders and gray centers on leaves?',
    'leaf yellowing and drop starting from the bottom of the plant': 'Is there leaf yellowing and drop starting from the bottom of the plant?',
    'yellowing of leaves, often starting on one side': 'Did you notice yellowing of leaves, often starting on one side?',
    'wilting of leaves and stems, especially during the day': 'Is there wilting of leaves and stems, especially during the day?',
    'brown discoloration inside the stem': 'Do you see brown discoloration inside the stem?',
    'brown discoloration in the stem\'s vascular tissue': 'Is there brown discoloration in the stem\'s vascular tissue?',
    'stunted growth and poor yield': 'Do you observe stunted growth and poor yield?',
    'mottled light and dark green patterns on leaves': 'Are there mottled light and dark green patterns on leaves?',
    'distorted or stunted growth': 'Is there distorted or stunted growth?',
    'yellow streaking on flowers and fruit': 'Do you see yellow streaking on flowers and fruit?',
    'bronze or purple spots on young leaves': 'Are there bronze or purple spots on young leaves?',
    'ring spots on fruit and deformed fruit growth': 'Do you see ring spots on fruit and deformed fruit growth?',
    'small water-soaked spots on leaves, stems, and fruit': 'Did you notice small water-soaked spots on leaves, stems, and fruit?',
    'spots enlarge and become brown with a yellow halo': 'Do the spots enlarge and become brown with a yellow halo?',
    'fruit may have black, scabby spots': 'Does the fruit have black, scabby spots?',
    'small dark spots on leaves and fruit': 'Are there small dark spots on leaves and fruit?',
    'yellow halos around leaf spots': 'Do you see yellow halos around leaf spots?',
    'raised, black spots on fruit': 'Are there raised, black spots on fruit?',
    'white powdery growth on leaves, stems, and buds': 'Is there white powdery growth on leaves, stems, and buds?',
    'yellowing and browning of leaves': 'Are the leaves yellowing and browning?',
    'sunken circular spots on ripe fruit': 'Do you notice sunken circular spots on ripe fruit?',
    'fruit rots quickly after spotting': 'Does the fruit rot quickly after spotting?',
    'dark sunken spots on the blossom end of the fruit': 'Are there dark sunken spots on the blossom end of the fruit?',
    'affected fruits may rot': 'Do the affected fruits rot?',
    'swollen galled roots': 'Are the roots swollen and galled?',
    'gray fuzzy mold on leaves, stems, and fruit': 'Is there gray fuzzy mold on leaves, stems, and fruit?',
    'brown, water-soaked spots on leaves': 'Are there brown, water-soaked spots on leaves?',
    'water-soaked spots on fruit, typically near the soil line': 'Are there water-soaked spots on fruit, typically near the soil line?',
    'fruit rots and becomes mushy': 'Does the fruit rot and become mushy?',
    'wilting of plants, starting at the base': 'Is there wilting of plants, starting at the base?',
    'white, fan-like fungal growth on the stem near soil line': 'Is there white, fan-like fungal growth on the stem near soil line?',
    'brown, sunken lesions on stems': 'Are there brown, sunken lesions on stems?',
    'sudden wilting of plants': 'Is there sudden wilting of plants?',
    'sticky, bacterial ooze from cut stems': 'Is there sticky, bacterial ooze from cut stems?',
    'dark sunken lesions on stems and fruit': 'Are there dark sunken lesions on stems and fruit?',
    'leaf spots with concentric rings': 'Are there leaf spots with concentric rings?',
    'defoliation': 'Is there defoliation?'
}


## Forward Chaining (Iterative)
def forward_chaining(symptoms):
    possible_diseases = []
    
    for disease, info in diseases.items():
        if all(symptom in info['symptoms'] for symptom in symptoms):
            possible_diseases.append(disease)
    
    if not possible_diseases:
        return None, 'Disease not found or insufficient data.'
    
    if len(possible_diseases) == 1:
        return possible_diseases[0], diseases[possible_diseases[0]]['treatment']
    
    return possible_diseases, 'Please provide additional symptoms for confirmation.'

# Backward Chaining
def backward_chaining(disease):
    if disease in diseases:
        return diseases[disease]['symptoms'], diseases[disease]['treatment']
    return None, 'Disease not found.'

# Home route
@app.route('/home')
def home():
    if 'user_id' in session:
        return render_template('index.html', diseases=diseases.keys())
    else:
        return redirect(url_for('login'))
 

@app.route('/diagnose', methods=['POST'])
def diagnose():
    symptoms = request.form.get('symptom').split(',')
    disease, message = forward_chaining(symptoms)
    if isinstance(disease, list):
        return render_template('confirm_symptoms.html', diseases=disease, symptoms=symptoms)
    return render_template('result.html', disease=disease, treatment=message)

@app.route('/validate', methods=['POST'])
def validate():
    disease = request.form.get('disease')
    symptoms, treatment = backward_chaining(disease)
    return render_template('result.html', disease=disease, symptoms=symptoms, treatment=treatment)

@app.route('/confirm', methods=['POST'])
def confirm():
    additional_symptom = request.form.get('additional_symptom')
    symptoms = request.form.get('symptoms').split(',')
    symptoms.append(additional_symptom)
    disease, treatment = forward_chaining(symptoms)
    return render_template('result.html', disease=disease, treatment=treatment)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# Function to preprocess the image
def preprocess_image(image):
    # Resize image to the same size as during training
    image = image.resize((64, 64))
    # Convert image to numpy array
    image_array = np.array(image)
    # Normalize the image to the range [0, 1]
    image_array = image_array / 255.0
    # Expand dimensions to match model's expected input shape
    image_array = np.expand_dims(image_array, axis=0)
    return image_array
@app.route('/')
def root():
    return render_template('login.html')

# User authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        
        new_user = User(name=name, email=email, phone=phone, username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# @app.route('/home')
# def home():
#     return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            image = Image.open(file_path)
            image_array = preprocess_image(image)
            
            prediction = model.predict(image_array)
            predicted_class = np.argmax(prediction, axis=1)[0]
            
            disease_labels = ['Bacterial_spot', 'Early_blight', 'Late_blight', 'Leaf_Mold',
                              'Septoria_leaf_spot', 'Spider_mites_Two-spotted_spider_mite',
                              'Target_Spot', 'Tomato_Yellow_Leaf_Curl_Virus', 'Tomato_mosaic_virus',
                              'Healthy']
            
            predicted_disease = disease_labels[predicted_class]
            
            knowledge = diseases.get(predicted_disease, {'symptoms': 'N/A', 'treatment': 'N/A'})
            
            return render_template('upload_result.html', filename=filename, prediction=predicted_disease,
                                   symptoms=knowledge['symptoms'], treatment=knowledge['treatment'])
    
    return render_template('upload.html')


@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)


@app.route('/guided_questionnaire')
def guided_questionnaire():
    return render_template('guided_questionnaire.html')

@app.route('/questionnaire', methods=['POST'])
def questionnaire():
    symptoms = request.form.getlist('symptoms')
    disease, message = forward_chaining(symptoms)
    if isinstance(disease, list):
        return render_template('confirm_symptoms.html', diseases=disease, symptoms=symptoms)
    return render_template('result.html', disease=disease, treatment=message)

@app.route('/update_symptoms', methods=['POST'])
def update_symptoms():
    additional_symptom = request.form.get('additional_symptom')
    symptoms = request.form.get('symptoms').split(',')
    symptoms.append(additional_symptom)
    disease, treatment = forward_chaining(symptoms)
    return render_template('result.html', disease=disease, treatment=treatment)

if __name__ == '__main__':
    app.run(debug=True)
