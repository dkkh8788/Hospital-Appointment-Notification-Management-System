from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import json

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['appointment_system']

# Define collections
patients_collection = db["patients"]
doctors_collection = db["doctors"]

# Clear existing collections for fresh data
patients_collection.delete_many({})
doctors_collection.delete_many({})

# Sample patients data with email and phone
patients = [
    {"patient_id": "123", "name": "Alice Johnson", "age": 30, "gender": "Female", "email": "alice.johnson@example.com", "phone": "+91-9876543210", "medical_history": ["Hypertension"]},
    {"patient_id": "124", "name": "Bob Smith", "age": 45, "gender": "Male", "email": "bob.smith@example.com", "phone": "+91-9123456789", "medical_history": ["Diabetes"]},
    {"patient_id": "125", "name": "Carol White", "age": 38, "gender": "Female", "email": "carol.white@example.com", "phone": "+91-9234567890", "medical_history": ["Asthma"]},
    {"patient_id": "126", "name": "David Brown", "age": 52, "gender": "Male", "email": "david.brown@example.com", "phone": "+91-9345678901", "medical_history": ["High Cholesterol"]},
    {"patient_id": "127", "name": "Eva Green", "age": 27, "gender": "Female", "email": "eva.green@example.com", "phone": "+91-9456789012", "medical_history": ["Allergies"]},
    {"patient_id": "128", "name": "Frank Adams", "age": 34, "gender": "Male", "email": "frank.adams@example.com", "phone": "+91-9567890123", "medical_history": ["Back Pain"]},
    {"patient_id": "129", "name": "Grace Lewis", "age": 29, "gender": "Female", "email": "grace.lewis@example.com", "phone": "+91-9678901234", "medical_history": ["Migraines"]},
    {"patient_id": "121", "name": "Henry Wilson", "age": 41, "gender": "Male", "email": "henry.wilson@example.com", "phone": "+91-9789012345", "medical_history": ["Arthritis"]},
    {"patient_id": "122", "name": "Isla Young", "age": 22, "gender": "Female", "email": "isla.young@example.com", "phone": "+91-9890123456", "medical_history": ["Anemia"]},
    {"patient_id": "130", "name": "Jack Hall", "age": 36, "gender": "Male", "email": "jack.hall@example.com", "phone": "+91-9901234567", "medical_history": ["Gastroesophageal reflux"]}
]

# Insert sample patients data
patients_collection.insert_many(patients)
print("Inserted sample patients data.")

# Sample doctors data with email, phone, and 7 days of availability (more slots on weekends)
doctors = [
    {
        "doctor_id": 8888,
        "name": "Dr. Emily Stone",
        "specialty": "Cardiology",
        "email": "emily.stone@hospital.com",
        "phone": "+91-9812345678",
        "availability": {
            "2023-10-16": ["09:00", "11:00", "14:00"],
            "2023-10-17": ["10:00", "13:00", "16:00"],
            "2023-10-18": ["09:00", "12:00", "15:00"],
            "2023-10-19": ["08:00", "11:00", "14:00"],
            "2023-10-20": ["09:00", "12:00", "16:00"],
            "2023-10-21": ["10:00", "13:00", "15:00", "17:00", "19:00"],
            "2023-10-22": ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00"]
        }
    },
    {
        "doctor_id": 8887,
        "name": "Dr. Michael Lee",
        "specialty": "Endocrinology",
        "email": "michael.lee@hospital.com",
        "phone": "+91-9823456789",
        "availability": {
            "2023-10-16": ["09:00", "12:00", "15:00"],
            "2023-10-17": ["08:00", "11:00", "14:00"],
            "2023-10-18": ["09:00", "13:00", "16:00"],
            "2023-10-19": ["08:00", "12:00", "15:00"],
            "2023-10-20": ["09:00", "11:00", "14:00"],
            "2023-10-21": ["10:00", "12:00", "14:00", "16:00", "18:00"],
            "2023-10-22": ["09:00", "11:00", "13:00", "15:00", "17:00"]
        }
    },
    {
        "doctor_id": 8884,
        "name": "Dr. Sarah Davis",
        "specialty": "Dermatology",
        "email": "sarah.davis@hospital.com",
        "phone": "+91-9834567890",
        "availability": {
            "2023-10-16": ["10:00", "12:00", "15:00"],
            "2023-10-17": ["09:00", "13:00", "17:00"],
            "2023-10-18": ["08:00", "11:00", "14:00"],
            "2023-10-19": ["09:00", "12:00", "15:00"],
            "2023-10-20": ["10:00", "13:00", "16:00"],
            "2023-10-21": ["09:00", "11:00", "13:00", "15:00", "17:00"],
            "2023-10-22": ["08:00", "10:00", "12:00", "14:00", "16:00"]
        }
    },
    {
        "doctor_id": 8885,
        "name": "Dr. John Carter",
        "specialty": "Pediatrics",
        "email": "john.carter@hospital.com",
        "phone": "+91-9845678901",
        "availability": {
            "2023-10-16": ["09:00", "12:00", "15:00"],
            "2023-10-17": ["10:00", "13:00", "16:00"],
            "2023-10-18": ["08:00", "11:00", "14:00"],
            "2023-10-19": ["09:00", "12:00", "15:00"],
            "2023-10-20": ["10:00", "13:00", "16:00"],
            "2023-10-21": ["09:00", "11:00", "14:00", "17:00"],
            "2023-10-22": ["08:00", "10:00", "13:00", "15:00", "17:00"]
        }
    },
    {
        "doctor_id": 8886,
        "name": "Dr. Olivia Walker",
        "specialty": "Neurology",
        "email": "olivia.walker@hospital.com",
        "phone": "+91-9856789012",
        "availability": {
            "2023-10-16": ["08:00", "11:00", "14:00"],
            "2023-10-17": ["10:00", "12:00", "15:00"],
            "2023-10-18": ["09:00", "13:00", "17:00"],
            "2023-10-19": ["08:00", "11:00", "14:00"],
            "2023-10-20": ["09:00", "12:00", "16:00"],
            "2023-10-21": ["10:00", "12:00", "14:00", "16:00", "18:00"],
            "2023-10-22": ["09:00", "11:00", "13:00", "15:00", "17:00"]
        }
    }
]

# Insert sample doctors data
doctors_collection.insert_many(doctors)
print("Inserted sample doctors data.")
