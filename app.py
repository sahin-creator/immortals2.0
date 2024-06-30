from flask import Flask, request, render_template , jsonify, redirect , session , url_for , flash
from pymongo import MongoClient
import os
import bcrypt
import re
from datetime import datetime , timedelta
from werkzeug.utils import secure_filename
import base64
from bson.objectid import ObjectId
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from bson.json_util import dumps
from flask_mail import Mail , Message
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()


app = Flask(__name__,static_url_path='/static', static_folder='static')
app.secret_key = os.urandom(24)  # Secret key for session management
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)


# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['immortals']
collection = db['patient']
appointments_collection = db['appointment']
counters_collection = db['counters']
doctor_collection = db['doctor']
admin_collection = db["admin"]
patients_collection = db['patient']
announcements = db['announcement']
announcements_collection = db["announcement"]
doctor_time_collection = db['doctor_time']


# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# Function to get the next sequence value for a given sequence name
def get_next_sequence_value(sequence_name):
    sequence_document = counters_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        return_document=True
    )
    return sequence_document['sequence_value']

#index page start
@app.route('/')
def index():
    return render_template('index.html')
#register doctor...........................................................................................................................
@app.route('/doctors/register', methods=['POST'])
def register_doctor():
    doctor_data = request.form.to_dict()

    required_fields = ['name', 'category', 'government_id', 'adhar_no', 'email', 'address', 'zip', 'password', 'confirm_password']
    for field in required_fields:
        if not doctor_data.get(field):
            flash(f'{field} is required', 'danger')
            return redirect(url_for('index'))

    email = doctor_data['email']
    password = doctor_data['password']
    confirm_password = doctor_data.get('confirm_password')

    if password != confirm_password:
        flash('Passwords do not match', 'danger')
        return redirect(url_for('index'))

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    doctor_data['password'] = hashed_password.decode('utf-8')
    doctor_data.pop('confirm_password', None)

    doctor_data['doctor_id'] = generate_doctor_id('doctor_id')
    doctor_data['status'] = 'pending'

    doctor_collection.insert_one(doctor_data)
    return redirect(url_for('index'))

def generate_doctor_id(sequence_name):
    sequence_document = counters_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        return_document=True,
        upsert=True
    )
    if not sequence_document:
        counters_collection.insert_one({'_id': sequence_name, 'sequence_value': 1})
        sequence_value = 1
    else:
        sequence_value = sequence_document['sequence_value']
    
    doctor_id = f"doc{sequence_value:03d}"
    return doctor_id

#register patient .............................................................................................................................

@app.route('/register/patient', methods=['POST'])
def register_patient():
    if request.method == 'POST':
        try:
            patient_id = f"patient{get_next_sequence_value('patientId'):03}"
            # Access form data using request.form
            phone_number = request.form['exampleInputPhone']
            if not re.match(r'^[0-9]{10}$', phone_number):
                return jsonify({'error': 'Invalid phone number format', 'message': 'Please enter a 10-digit phone number'})
            #for check pssword
            password = request.form['exampleInputPassword']
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            patient_data = {
                'patient_id': patient_id,
                'name': request.form['exampleInputName'],
                'phone': request.form['exampleInputPhone'],
                'aadhar': request.form['exampleInputAdhar'],
                'dob': request.form['exampleInputDOB'],
                'address': request.form['exampleInputAddress'],
                'pin': request.form['exampleInputPin'],
                'email': request.form['exampleInputEmail'],
                'password': hashed_password
            }
            # Insert patient data into MongoDB
            collection.insert_one(patient_data)
            message = "Registration Successful !! Now go to Login ....."
            return jsonify({'message': message, 'redirect_url': '/'})
        except Exception as e:
            return jsonify({'error': str(e), 'message': 'An error occurred during registration'})

@app.route('/register/admin', methods=['POST'])
def register_admin():
    if request.method == 'POST':
        admin_data = request.form.to_dict()  # Convert ImmutableMultiDict to dictionary
        db.admin.insert_one(admin_data)
        return 'Admin registered successfully'

#patient page...................................................................................................patient page....................
# Patient login
@app.route('/login/patient', methods=['POST'])
def login_patient():
    if request.method == 'POST':
        email = request.form['exampleInputEmail3']
        password = request.form['exampleInputPassword3']
        # Query the database to find the user with the given email
        patient = collection.find_one({'email': email})
        if patient:
            # Check if the provided password matches the hashed password stored in the database
            if bcrypt.checkpw(password.encode('utf-8'), patient['password']):
                # Store the user's email in the session
                session['email'] = email
                session['patient_id'] = patient['patient_id']
                return jsonify({'message': 'Login Successful'})
            else:
                return jsonify({'error': 'Invalid Credentials', 'message': 'Incorrect email or password'})
        else:
            return jsonify({'error': 'User not found', 'message': 'Please register before logging in'})

        

@app.route('/patient')
@app.route('/patient.html')
def patient_page():
    # Fetch patient details based on the logged-in user's email (assuming it's stored in the session)
    if 'email' in session:
        email = session['email']
        patient = collection.find_one({'email': email})
        if patient:
            # Get patient ID from the logged-in patient's details
            patient_id = patient['patient_id']
            # Fetch patient details based on patient ID
            patient_details = collection.find_one({'patient_id': patient_id})
            if patient_details:
                # Ensure that the 'health' attribute exists in the patient_details dictionary
                if 'health' not in patient_details:
                    patient_details['health'] = None
                # Convert 'dob' to datetime object
                patient_details['dob'] = datetime.strptime(patient_details['dob'], '%Y-%m-%d')
                
                # Fetch appointment data for the patient from the database
                appointments = appointments_collection.find({'patient_id': patient_id})
                
                return render_template('patient.html', patient_data=patient_details, appointments=appointments, current_date=datetime.now())
            else:
                return jsonify({'error': 'Patient details not found', 'message': 'Please try again later'})
        else:
            return jsonify({'error': 'User not found', 'message': 'Please register before logging in'})
    else:
        return redirect('/')

#patient announcement......................................................................................................
@app.route('/fetch_patient_announcements')
def fetch_patient_announcements():
    patient_announcements = announcements_collection.find({"type": "patient"})
    announcements_list = []
    for announcement in patient_announcements:
        announcements_list.append(announcement)
    return dumps(announcements_list)

#for ppointment
# Function to get the next sequence value for a given sequence name
def get_next_sequence_value(sequence_name):
    sequence_document = counters_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        return_document=True
    )
    return sequence_document['sequence_value']

# Endpoint for booking appointments
@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    try:
        patient_id = session.get('patient_id')
        if not patient_id:
            return jsonify({'success': False, 'message': 'Please log in'})

        # Fetch the latest appointment for the patient
        last_appointment = appointments_collection.find_one(
            {'patient_id': patient_id},
            sort=[('booking_time', -1)]
        )

        current_time = datetime.now()

        # Check if the last appointment was booked less than 24 hours ago
        if last_appointment:
            time_diff = current_time - last_appointment['booking_time']
            if time_diff.total_seconds() < 24 * 3600:
                next_booking_time = last_appointment['booking_time'] + timedelta(hours=24)
                wait_time = next_booking_time - current_time
                wait_hours = wait_time.seconds // 3600
                wait_minutes = (wait_time.seconds % 3600) // 60
                return jsonify({
                    'success': False,
                    'message': f'You can book another appointment after {wait_hours} hours and {wait_minutes} minutes.'
                })

        # Generate unique appointment ID
        appointment_id = f"appointment{get_next_sequence_value('appointmentId'):04}"
        email = request.form['email']
        doctor = request.form['doctor']
        date = request.form['date']
        time_slot = request.form['time_slot']
        document = request.files.get('document')

        file_data = None
        if document:
            max_file_size = 1 * 1024 * 1024  # 1 MB
            if document.content_length > max_file_size:
                return jsonify({'success': False, 'message': 'File size should not exceed 1 MB'})
            file_data = document.read()

        # Save appointment details to the database
        appointment_data = {
            'appointment_id': appointment_id,
            'doctor': doctor,
            'patient_id': patient_id,
            'date': date,
            'time_slot': time_slot,
            'document': {'prescription': file_data},
            'status': 'pending',
            'booking_time': current_time
        }
        appointments_collection.insert_one(appointment_data)

        # Send confirmation email
        try:
            msg = Message("Appointment Confirmation",
                          recipients=[email])
            msg.body = (f"Dear Patient,\n\nYour appointment has been successfully booked.\n\n"
                        f"Appointment ID: {appointment_id}\n"
                        f"Patient ID: {patient_id}\n"
                        f"Doctor: {doctor}\n"
                        f"Date: {date}\n"
                        f"Time Slot: {time_slot}\n\nThank you.")
            mail.send(msg)
        except Exception as email_error:
            print(f"Failed to send email: {email_error}")
            return jsonify({'success': True, 'message': 'Appointment booked but failed to send confirmation email'})

        return jsonify({'success': True, 'message': 'Appointment booked successfully', 'redirect_url': url_for('patient_page')})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while booking the appointment', 'error': str(e)})



#doctor page----------...................................................................................................doctor page...........

@app.route('/doctor', methods=['POST'])
def doctor_login():
    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        password = request.form['password']
        doctor = doctor_collection.find_one({'doctor_id': doctor_id})

        if doctor and bcrypt.checkpw(password.encode('utf-8'), doctor['password'].encode('utf-8')):
            # Authentication successful for doctor, set session flag and redirect
            session['doctor_logged_in'] = True
            session['doctor_id'] = str(doctor['_id'])  # Storing ObjectId as string
            return redirect(url_for('doctor_dashboard'))
        else:
            # Authentication failed, return error message
            flash('Invalid Doctor ID or password', 'error')
            return redirect(url_for('index'))


@app.route('/doctor/dashboard')
def doctor_dashboard():
    # Check if the user is logged in
    if not session.get('doctor_logged_in'):
        return redirect(url_for('index'))  # Redirect to login if not logged in

    # Retrieve the doctor's information from the database
    doctor_id = session.get('doctor_id')  # Assuming you store doctor's ID in session
    doctor = get_doctor_by_id(doctor_id)

    # Fetch upcoming appointments for the doctor
    upcoming_appointments = get_upcoming_appointments_for_doctor(doctor_id)

    # This route can be the doctor's dashboard or any other authenticated page for doctors
    return render_template('doctor.html', doctor=doctor, upcoming_appointments=upcoming_appointments)

def get_doctor_by_id(doctor_id):
    """
    Retrieve a doctor's information from the database by ID.
    
    Parameters:
        doctor_id (str): The ID of the doctor to retrieve.
        
    Returns:
        dict: A dictionary containing the doctor's information, or None if the doctor is not found.
    """
    doctor = doctor_collection.find_one({'_id': ObjectId(doctor_id)})  # Convert string ID back to ObjectId
    return doctor
# upcomung appointment show in doctor pge ,....................................................................
def get_upcoming_appointments_for_doctor(doctor_id):
    """
    Retrieve upcoming appointments for a specific doctor.
    
    Parameters:
        doctor_id (str): The ID of the doctor.
        
    Returns:
        list: A list of dictionaries containing upcoming appointment details.
    """
    # Assuming 'appointments' is your MongoDB collection for appointments
    upcoming_appointments = list(appointments_collection.find({'doctor': doctor_id}))
    print("Upcoming Appointments:", upcoming_appointments)  # Print the result
    return upcoming_appointments

#admin page...............................................................................................................................admin.....

@app.route('/admin_login', methods=['POST'])
def admin_login():
    email = request.form.get('email')
    gov_id = request.form.get('gov_id')
    password = request.form.get('password')

    admin = admin_collection.find_one({"email": email, "gov_id": gov_id, "password": password})

    if admin:
        session['admin_id'] = str(admin['_id'])
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Invalid credentials. Please try again.', 'danger')
        return redirect(url_for('index'))
    
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('index'))
    
    # Fetch the admin details (assuming there's only one document in the collection)
    admin_details = admin_collection.find_one()

    if admin_details:
        admin_info = {
            "Name": admin_details.get('name', 'N/A'),
            "Govt_Issue_Id": admin_details.get('gov_id', 'N/A'),
            "Aadhar_No": admin_details.get('aadhar', 'N/A'),
            "Hospital": admin_details.get('Hospital', 'N/A'),
            "Email_ID": admin_details.get('email', 'N/A'),
            "Phone_No": admin_details.get('mobile', 'N/A'),
            "Address": admin_details.get('address', 'N/A')
        }
    else:
        admin_info = None

    # Fetch the number of admins
    num_admins = admin_collection.count_documents({})

    # Fetch the number of doctors
    num_doctors = doctor_collection.count_documents({})

    # Fetch the number of patients
    num_patients = collection.count_documents({})

    # Fetch the number of total and pending appointments
    total_appointments = appointments_collection.count_documents({})
    pending_appointments = appointments_collection.count_documents({'status': 'pending'})

    # Fetch the number of pending doctor approvals
    pending_doctor_approvals = doctor_collection.count_documents({'approval_status': 'pending'})

    # Pass the data to the template
    return render_template(
        'admin.html',
        admin_info=admin_info,
        num_admins=num_admins,
        num_doctors=num_doctors,
        num_patients=num_patients,
        total_appointments=total_appointments,
        pending_appointments=pending_appointments,
        pending_doctor_approvals=pending_doctor_approvals
    )

# for approve appointment part........................................................................................................
@app.route('/admin_appointment_approval')
def admin_appointment_approval():
    if 'admin_id' not in session:
        return redirect(url_for('index'))
    return render_template('appointment_approval.html')

@app.route('/search_appointment/<appointment_id>')
def search_appointment(appointment_id):
    appointment = appointments_collection.find_one({'appointment_id': appointment_id})
    if appointment:
        appointment['_id'] = str(appointment['_id'])  # Convert ObjectId to string for JSON serialization
        # Convert binary data to Base64 string if it exists
        if 'document' in appointment and 'prescription' in appointment['document']:
            prescription = appointment['document']['prescription']
            appointment['document']['prescription'] = base64.b64encode(prescription).decode('utf-8')
        return jsonify(appointment)
    else:
        return jsonify({'message': 'Appointment not found'}), 404

# Endpoint to approve an appointment
@app.route('/approve_appointment', methods=['POST'])
def approve_appointment():
    data = request.get_json()
    appointment_id = data.get('appointment_id')
    doctor_id = data.get('doctor_id')
    appointment_date = data.get('appointment_date')
    time_slot = data.get('time_slot')

    result = appointments_collection.update_one(
        {'appointment_id': appointment_id},
        {'$set': {'status': 'scheduled', 'doctor': doctor_id, 'date': appointment_date, 'time_slot': time_slot}}
    )

    if result.modified_count > 0:
        return jsonify({'message': 'Appointment approved successfully'})
    else:
        return jsonify({'message': 'Failed to approve appointment'}), 400

# Endpoint to delete an appointment
@app.route('/delete_appointment/<appointment_id>', methods=['DELETE'])
def delete_appointment(appointment_id):
    result = appointments_collection.delete_one({'appointment_id': appointment_id})
    
    if result.deleted_count > 0:
        return jsonify({'message': 'Appointment deleted successfully'})
    else:
        return jsonify({'message': 'Failed to delete appointment'}), 400
    
#filter doctor......................................
@app.route('/check_doctor', methods=['GET'])
def check_doctor():
    doctor_type = request.args.get('doctor_type')
    available_date = request.args.get('available_date')

    # Query to find doctors by category
    doctor_query = {'category': doctor_type}
    doctors = list(doctor_collection.find(doctor_query))

    # Filter doctors by available date
    if available_date:
        available_date = datetime.strptime(available_date, '%Y-%m-%d')
        max_date = available_date + timedelta(days=7)

        doctor_ids = [doctor['doctor_id'] for doctor in doctors]
        doctor_time_query = {
            'doctor_id': {'$in': doctor_ids},
            'date': {'$gte': available_date.strftime('%Y-%m-%d'), '$lte': max_date.strftime('%Y-%m-%d')}
        }

        available_doctors_times = list(doctor_time_collection.find(doctor_time_query))

        # Doctors who have any appointments during the period
        busy_doctor_ids = {entry['doctor_id'] for entry in available_doctors_times}

        # Doctors who are available or have no appointments in the specified date range
        available_doctors = [doctor for doctor in doctors if doctor['doctor_id'] not in busy_doctor_ids or any(
            entry['status'] == 'available' for entry in available_doctors_times if entry['doctor_id'] == doctor['doctor_id'])]

    else:
        available_doctors = doctors

    # Prepare the response
    response = []
    for doctor in available_doctors:
        response.append({
            'doctor_id': doctor['doctor_id'],
            'name': doctor['name'],
            'hospital': doctor['address'],  # Assuming hospital is stored in address
            'state': 'N/A',  # Replace with actual state if available in database
            'type': doctor['category']
        })

    return jsonify(response)
#patient search..........................................................................................................
@app.route('/patient_search')
def patient_search():
    if 'admin_id' not in session:
        return redirect(url_for('index'))
    return render_template('patient_search.html')

# API endpoint to search for a patient
@app.route('/search_patient/<patient_id>', methods=['GET'])
def search_patient(patient_id):
    patient = patients_collection.find_one({'patient_id': patient_id}, {'_id': 0, 'password': 0})  # Exclude _id and password fields
    if patient:
        # Convert ObjectId to string for serialization
        if '_id' in patient:
            patient['_id'] = str(patient['_id'])
        return jsonify(patient), 200
    else:
        return jsonify({'message': 'Patient not found'}), 404



# API endpoint to update patient health details
@app.route('/update_patient_health/<patient_id>', methods=['POST'])
def update_patient_health(patient_id):
    updated_data = request.json
    result = patients_collection.update_one({'patient_id': patient_id}, {'$set': {'health': updated_data}})
    if result.modified_count > 0:
        return jsonify({'message': 'Health details updated successfully'}), 200
    else:
        return jsonify({'message': 'Patient not found'}), 404

#doctor search ..........................................................................................................................
@app.route('/search_doctor')
def search_doctor():
    if 'admin_id' not in session:
        return redirect(url_for('index'))
    return render_template('doctor_search.html')

#email send...................
def send_approval_email(doctor_email, doctor_id, password):
    subject = "Approval Notification"
    body = f"""
    Dear Doctor,

    We are pleased to inform you that your registration has been approved.

    Your Doctor ID: {doctor_id}
    Your Login Password: Password that given at register time ..

    Please use the above credentials to log in to the system and access your account.

    Best regards,
    The Medical Board

    Note: This is an automated message, please do not reply to this email.
    """
    
    msg = Message(subject, recipients=[doctor_email])
    msg.body = body

    try:
        mail.send(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/api/doctors/<doctor_id>', methods=['PUT'])
def update_doctor_status(doctor_id):
    data = request.json
    status = data.get('status')

    result = doctor_collection.update_one({'doctor_id': doctor_id}, {'$set': {'status': status}})
    
    if result.matched_count > 0:
        if status == 'Approved':
            doctor = doctor_collection.find_one({'doctor_id': doctor_id}, {'_id': 0, 'email': 1, 'password': 1})
            if doctor and 'email' in doctor and 'password' in doctor:
                send_approval_email(doctor['email'], doctor_id, doctor['password'])
        
        return jsonify({"message": f"Doctor {doctor_id} status updated to {status}"}), 200
    else:
        return jsonify({"message": f"Doctor {doctor_id} not found"}), 404

@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    search_input = request.args.get('searchInput', '')
    search_by = request.args.get('searchBy', '')

    filter_query = {}

    if search_by == "doctorId" and search_input:
        filter_query['doctor_id'] = search_input
    elif search_by == "doctorType" and search_input:
        filter_query['category'] = search_input
    elif search_by == "status" and search_input:
        filter_query['status'] = search_input

    doctors = list(doctor_collection.find(filter_query, {'_id': 0}))
    return jsonify(doctors)

# @app.route('/api/doctors/<doctor_id>', methods=['PUT'])
# def update_doctor_status(doctor_id):
#     data = request.json
#     status = data.get('status')

#     result = doctor_collection.update_one({'doctor_id': doctor_id}, {'$set': {'status': status}})
    
#     if result.matched_count > 0:
#         if status == 'Approved':
#             doctor = doctor_collection.find_one({'doctor_id': doctor_id}, {'_id': 0, 'email': 1})
#             if doctor and 'email' in doctor:
#                 send_approval_email(doctor['email'], doctor_id)
        
#         return jsonify({"message": f"Doctor {doctor_id} status updated to {status}"}), 200
#     else:
#         return jsonify({"message": f"Doctor {doctor_id} not found"}), 404

@app.route('/api/doctors/<doctor_id>', methods=['DELETE'])
def delete_doctor(doctor_id):
    result = doctor_collection.delete_one({'doctor_id': doctor_id})

    if result.deleted_count > 0:
        return jsonify({"message": f"Doctor {doctor_id} deleted"}), 200
    else:
        return jsonify({"message": f"Doctor {doctor_id} not found"}), 404
#announcement............................................................................................................................
@app.route('/announcements', methods=['POST'])
def post_announcement():
    data = request.json
    announcement_type = data.get('type')
    message = data.get('message')
    if not announcement_type or not message:
        return jsonify({'error': 'Type and message are required'}), 400
    announcement = {
        'type': announcement_type,
        'message': message,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    result = announcements.insert_one(announcement)
    return jsonify({'_id': str(result.inserted_id), 'message': 'Announcement posted successfully'}), 201

@app.route('/announcements', methods=['GET'])
def get_announcements():
    announcement_type = request.args.get('type')
    query = {}
    if announcement_type:
        query['type'] = announcement_type
    announcement_list = list(announcements.find(query))
    for announcement in announcement_list:
        announcement['_id'] = str(announcement['_id'])
    return jsonify(announcement_list), 200

@app.route('/announcements/<announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id):
    result = announcements.delete_one({'_id': ObjectId(announcement_id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'Announcement not found'}), 404
    return jsonify({'message': 'Announcement deleted successfully'}), 200
# Logout endpoint............................................................................................................................
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear the session data
    session.clear()
    return redirect(url_for('index'))  # Redirect to the index page or any other desired destination


if __name__ == '__main__':
    app.run(debug=True,port=8000)