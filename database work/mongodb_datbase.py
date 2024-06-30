import pymongo

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")

# Create or get the database
db = client["immortals"]

# Create the patients collection
patients_collection = db["patient"]

# Create the doctors collection
doctors_collection = db["doctor"]

# Create the admin collection
admin_collection = db["admin"]

# Create a separate collection to store the sequence information
counters_collection = db["counters"]

# Initialize the sequence if it doesn't exist for patients
if counters_collection.count_documents({"_id": "patientId"}) == 0:
    counters_collection.insert_one({
        "_id": "patientId",
        "sequence_value": 0
    })

# Initialize the sequence if it doesn't exist for appointments
if counters_collection.count_documents({"_id": "appointmentId"}) == 0:
    counters_collection.insert_one({
        "_id": "appointmentId",
        "sequence_value": 0
    })

# Initialize the sequence if it doesn't exist for doctors
if counters_collection.count_documents({"_id": "doctorId"}) == 0:
    counters_collection.insert_one({
        "_id": "doctorId",
        "sequence_value": 0
    })

# Initialize the sequence if it doesn't exist for admin
if counters_collection.count_documents({"_id": "adminId"}) == 0:
    counters_collection.insert_one({
        "_id": "adminId",
        "sequence_value": 0
    })

# Function to get the next patient ID
def get_next_patient_id():
    sequence_document = counters_collection.find_one_and_update(
        {"_id": "patientId"},
        {"$inc": {"sequence_value": 1}},
        return_document=True
    )
    return "patient" + str(sequence_document["sequence_value"]).zfill(4)

# Function to get the next appointment ID
def get_next_appointment_id():
    sequence_document = counters_collection.find_one_and_update(
        {"_id": "appointmentId"},
        {"$inc": {"sequence_value": 1}},
        return_document=True
    )
    return "appointment" + str(sequence_document["sequence_value"]).zfill(4)

# Function to get the next doctor ID
def get_next_doctor_id():
    sequence_document = counters_collection.find_one_and_update(
        {"_id": "doctorId"},
        {"$inc": {"sequence_value": 1}},
        return_document=True
    )
    return "doc" + str(sequence_document["sequence_value"]).zfill(3)

# Function to get the next admin ID
def get_next_admin_id():
    sequence_document = counters_collection.find_one_and_update(
        {"_id": "adminId"},
        {"$inc": {"sequence_value": 1}},
        return_document=True
    )
    return "admi" + str(sequence_document["sequence_value"]).zfill(3)

# Define sample patient data with health parameters
sample_patients = [
    {
        "patient_id": get_next_patient_id(),
        "name": "John Doe",
        "dob": "29/03/2001",
        "aadhar": "123456789012",
        "address": "123 Main St, City",
        "mobile no": "1234567890",
        "email": "john@example.com",
        "password": "password123",
        "health": {
            "blood_group": "O+",
            "weight_kg": 70,
            "height_cm": 175,
            "blood_pressure": "120/80",
            "blood_sugar": "Normal",
            "spo2": 98
        }
    },
    {
        "patient_id": get_next_patient_id(),
        "name": "Jane Smith",
        "dob": "03/04/2002",
        "aadhar": "987654321098",
        "address": "456 Elm St, Town",
        "mobile": "0987654321",
        "email": "jane@example.com",
        "password": "password456",
        "health": {
            "blood_group": "A-",
            "weight_kg": 65,
            "height_cm": 160,
            "blood_pressure": "130/85",
            "blood_sugar": "Normal",
            "spo2": 97
        }
    }
]

# Define sample doctor data
sample_doctors = [
    {
        "doctor_id": get_next_doctor_id(),
        "aadhar": "123456789012",
        "mobile": "9876543210",
        "email": "doctor@example.com",
        "gov_id": "doctor_license_001",
        "address": "789 Oak St, City",
        "password": "doctorpassword123"
    }
]

# Define sample admin data
sample_admins = [
    {
        "admin_id": get_next_admin_id(),
        "aadhar": "987654321012",
        "mobile": "9876543210",
        "email": "admin@example.com",
        "gov_id": "admin_license_001",
        "address": "456 Elm St, Town",
        "password": "adminpassword123"
    }
]

# Insert sample data into the collections
patients_collection.insert_many(sample_patients)
doctors_collection.insert_many(sample_doctors)
admin_collection.insert_many(sample_admins)

# Print success message
print("Database 'immortals' created with 'patient', 'doctor', 'admin', and 'appointment' collections.")
