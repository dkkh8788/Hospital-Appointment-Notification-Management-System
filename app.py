from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
from bson.json_util import dumps
from datetime import datetime
import requests
import json

# Initialize Flask app and MongoDB connection
app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")
db = client["appointment_system"]
patients_collection = db["patients"]
doctors_collection = db["doctors"]
appointments_collection = db["appointments"]

# Helper function to convert MongoDB ObjectId to JSON serializable format
def json_serializable(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError("Type not serializable")

# API to GET All patients
@app.route('/all_patients', methods=['GET'])
def get_all_patients():
    patients = list(patients_collection.find())
    if patients:
        for patient in patients:
            patient["_id"] = str(patient["_id"])
        return jsonify(patients), 200
    else:
        return jsonify({"error": "No patients found"}), 404

# API to GET All doctors
@app.route('/all_doctors', methods=['GET'])
def get_all_doctors():
    doctors = list(doctors_collection.find())
    if doctors:
        for doctor in doctors:
            doctor["_id"] = str(doctor["_id"])
        return jsonify(doctors), 200
    else:
        return jsonify({"error": "No doctors found"}), 404

# API to GET All booked appointments
@app.route('/all_appointments', methods=['GET'])
def get_all_appointments():
    appointments = list(appointments_collection.find())
    if appointments:
        for appointment in appointments:
            appointment["_id"] = str(appointment["_id"])
        return jsonify(appointments), 200
    else:
        return jsonify({"error": "No appointments found"}), 404

def post_notify_request(url, hdrs, data):
    try:
        #response = requests.post(url, headers=hdrs, json=data, timeout=30)  # Adjust timeout as needed
        response = requests.post(url, headers=hdrs, json=data)  # Adjust timeout as needed
        response.raise_for_status()  # Raise an exception for error HTTP status codes
        if response.status_code == 200:
            print("Notified succsfully:", response.json())
        return response.json()
    except requests.exceptions.ConnectTimeout as e:
        print(f"Failed to Notify. Connection timeout: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Failed to Notify. Request error: {e}")
        return None

def notify_prepare(email, date, time, patient_name, doctor_name, operation, old_date, old_time): 
    # Define the URL for the request
    url = "invalid url"
    if operation == "cancellation_appointment" :
        url = "http://a04aec4ee247c4b74afe0a0b88e403bc-1942226443.us-east-1.elb.amazonaws.com/notify/cancel_appointment"
    if operation == "reschedule_appointment" :
        url = "http://a04aec4ee247c4b74afe0a0b88e403bc-1942226443.us-east-1.elb.amazonaws.com/notify/reschedule_appointment"
    if operation == "new_appointment" :
        url = "http://a04aec4ee247c4b74afe0a0b88e403bc-1942226443.us-east-1.elb.amazonaws.com/notify/new_appointment"

    # Define headers
    headers = {
        "Content-Type": "application/json",
    }
 
    # Define the body (payload) of the request
    data = {
        "recipient_email": "2023mt03164@wilp.bits-pilani.ac.in",
        "appointment_date": date,
        "appointment_time": time,
        "patient_name": patient_name,
        "doctor_name": doctor_name,
    }
 
    if operation == "reschedule_appointment":
        data["old_date"] = old_date
        data["old_time"] = old_time

    # Send the POST request
    response = post_notify_request(url, headers, data)


# API to book an appointment for a patient
@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    data = request.json
    patient_id = data.get("patient_id")
    doctor_id = data.get("doctor_id")
    appointment_time = data.get("appointment_time")

    patient = patients_collection.find_one({"patient_id": patient_id})
    doctor = doctors_collection.find_one({"doctor_id": doctor_id})

    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    # Check if patient already has an appointment at the same time
    existing_appointment = appointments_collection.find_one({"patient_id": patient_id, "appointment_daytime": appointment_time})
    if existing_appointment:
        return jsonify({"error": "Patient already has an appointment at this time"}), 400

    date, time = appointment_time.split(' ')

    if date in doctor["availability"] and time in doctor["availability"][date]:
        appointment_datetime = datetime.strptime(appointment_time, '%Y-%m-%d %H:%M')
        current_datetime = datetime.now()

        if current_datetime < appointment_datetime or current_datetime >= appointment_datetime:

            appointment = {
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "appointment_daytime": appointment_time,
                "appointment_date": date,
                "appointment_time": time,
                "patient_name": patient["name"],
                "doctor_name": doctor["name"],
                "recipient_email": patient["email"],
                "doctor_contact_number": doctor["phone"],
                "patient_contact_number": patient["phone"],

                "status": "Booked"
            }
            appointment_id = appointments_collection.insert_one(appointment).inserted_id
            appointment["_id"] = str(appointment_id)

            # Remove the booked time slot from the doctor's availability
            doctor["availability"][date].remove(time)
            doctors_collection.update_one(
                {"_id": doctor["_id"]},
                {"$set": {"availability": doctor["availability"]}}
            )
            notify_prepare(patient["email"], date, time, patient["name"], doctor["name"], "new_appointment")
            return jsonify(appointment), 201
        else:
            return jsonify({"error": "Cannot book past appointments"}), 400
    else:
        return jsonify({"error": "Doctor is not available at this time"}), 400

# API for a doctor to view their appointments
@app.route('/view_doctor_appointments/<doctor_id>', methods=['GET'])
def view_appointments_for_doctor(doctor_id):
    doctor_appointments = list(appointments_collection.find({"doctor_id": int(doctor_id)}))
    if doctor_appointments:
        for appt in doctor_appointments:
            appt["_id"] = str(appt["_id"])
        return jsonify(doctor_appointments), 200
    else:
        return jsonify({"error": "No appointments found"}), 404


# API for a doctor to view their appointments for a specific date
@app.route('/view_appointments/<doctor_id>/<date>', methods=['GET'])
def view_appointments_for_doctor_by_day(doctor_id, date):
    doctor_appointments = list(appointments_collection.find({"doctor_id": int(doctor_id), "appointment_daytime": {"$regex": f"^{date}"}}))
    if doctor_appointments:
        for appt in doctor_appointments:
            appt["_id"] = str(appt["_id"])
        return jsonify(doctor_appointments), 200
    else:
        return jsonify({"error": "No appointments found for this date"}), 404

@app.route('/cancel_appointments/<doctor_id>/<date>', methods=['DELETE'])
def cancel_appointments_for_doctor(doctor_id, date):
    appointments_to_be_deleted = appointments_collection.find({"doctor_id": int(doctor_id), "appointment_date": {"$regex": f"^{date}"}}).to_list()
    result = appointments_collection.delete_many({"doctor_id": int(doctor_id), "appointment_date": {"$regex": f"^{date}"}})

    for appointment in appointments_to_be_deleted:
        #patient_email = appointment["recipient_email"]
        patient_email = "2023mt03164@wilp.bits-pilani.ac.in"
        appointment_date = appointment["appointment_date"]
        appointment_time = appointment["appointment_time"]
        patient_name = appointment["patient_name"]
        doctor_name = appointment["doctor_name"]
        notify_prepare(patient_email, appointment_date, appointment_time, patient_name, doctor_name, "cancellation_appointment")

    return jsonify({"message": f"Cancelled {result.deleted_count} appointments for Dr. {doctor_id} on {date}"}), 200


@app.route('/cancel_appointment', methods=['DELETE'])
def cancel_patient_appointment():
    """Cancels an appointment by a patient and updates doctor's availability."""

    data = request.json
    patient_id = data.get("patient_id")
    appointment_datetime = data.get("appointment_datetime")

    if not patient_id or not appointment_datetime:
        return jsonify({"error": "Patient ID and appointment date-time are required"}), 400

    appointment = appointments_collection.find_one({"patient_id": patient_id, "appointment_daytime": appointment_datetime})

    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    # Cancel appointment and update doctor's availability
    appointment_date = appointment["appointment_date"]
    appointment_time = appointment["appointment_time"]
    doctor_id = appointment["doctor_id"]

    appointments_collection.delete_one({"_id": appointment["_id"]})

    # Update doctor's availability by adding the cancelled time slot back
    doctor = doctors_collection.find_one({"doctor_id": doctor_id})
    doctor["availability"][appointment_date].append(appointment_time)
    doctors_collection.update_one(
        {"_id": doctor["_id"]}, {"$set": {"availability": doctor["availability"]}}
    )

    # Notify patient about cancellation success
    #patient_email = appointment["recipient_email"]
    patient_email = "2023mt03164@wilp.bits-pilani.ac.in"
    patient_name = appointment["patient_name"]
    doctor_name = appointment["doctor_name"]
    notify_prepare(patient_email, appointment_date, appointment_time, patient_name, doctor_name, "cancellation_appointment")

    return jsonify({"message": "Appointment cancelled successfully"}), 200

# API for a doctor to accept or reject an appointment
@app.route('/appointment_action', methods=['POST'])
def accept_reject_appointment():
    data = request.json
    appointment_id = data.get("appointment_id")
    action = data.get("action")

    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    if action == 'accept':
        appointments_collection.update_one({"_id": ObjectId(appointment_id)}, {"$set": {"status": "Accepted"}})
    elif action == 'reject':
        appointments_collection.update_one({"_id": ObjectId(appointment_id)}, {"$set": {"status": "Rejected"}})
    else:
        return jsonify({"error": "Invalid action"}), 400

    updated_appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    updated_appointment["_id"] = str(updated_appointment["_id"])
    return jsonify(updated_appointment), 200

# API for a doctor to set their availability for a specific date
@app.route('/set_availability', methods=['POST'])
def set_availability():
    data = request.json
    doctor_id = data.get("doctor_id")
    date = data.get("date")
    available_times = data.get("available_times")

    doctor = doctors_collection.find_one({"doctor_id": doctor_id})
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    doctors_collection.update_one(
        {"doctor_id": doctor_id},
        {"$set": {f"availability.{date}": available_times}}
    )
    updated_doctor = doctors_collection.find_one({"doctor_id": doctor_id})
    return jsonify({"availability": updated_doctor["availability"]}), 200

@app.route('/reschedule_appointment', methods=['POST'])
def reschedule_appointment():
    data = request.json
    patient_id = data.get("patient_id")
    old_appointment_time = data.get("old_appointment_datetime")
    new_appointment_time = data.get("new_appointment_datetime")

    if not patient_id or not old_appointment_time or not new_appointment_time:
        return jsonify({"error": "Patient ID, old appointment time, and new appointment time are required"}), 400

    # Find the existing appointment
    old_appointment = appointments_collection.find_one({"patient_id": patient_id, "appointment_daytime": old_appointment_time})
    if not old_appointment:
        return jsonify({"error": "Appointment not found"}), 404

    # Check if the new appointment time is available with the doctor
    doctor_id = old_appointment["doctor_id"]
    doctor = doctors_collection.find_one({"doctor_id": doctor_id})
    new_date, new_time = new_appointment_time.split(' ')
    if new_date not in doctor["availability"] or new_time not in doctor["availability"][new_date]:
        return jsonify({"error": "Doctor is not available at the new time"}), 400

    # Update the appointment with the new time
    appointments_collection.update_one(
        {"_id": old_appointment["_id"]},
        {"$set": {"appointment_daytime": new_appointment_time, "appointment_date": new_date, "appointment_time": new_time}}
    )

    # Remove the old appointment time from the doctor's availability
    old_date, old_time = old_appointment_time.split(' ')
    doctor["availability"][old_date].append(old_time)
    doctors_collection.update_one(
        {"_id": doctor["_id"]},
        {"$set": {"availability": doctor["availability"]}}
    )

    # Notify the patient about the successful rescheduling
    #patient_email = old_appointment["recipient_email"]
    patient_name = old_appointment["patient_name"]
    doctor_name = old_appointment["doctor_name"]
    patient_email = "2023mt03164@wilp.bits-pilani.ac.in"
    notify_prepare(patient_email, new_date, new_time, patient_name, doctor_name, "reschedule_appointment", old_date, old_time)

    return jsonify({"message": "Appointment rescheduled successfully"}), 200


# Error handler for JSON serialization
@app.errorhandler(TypeError)
def handle_invalid_usage(error):
    error = jsonify({"error": str(error)})
    error.status_code = 500
    return error

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
