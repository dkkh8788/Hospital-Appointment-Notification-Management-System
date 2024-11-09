from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Change this URL if MongoDB is hosted remotely
db = client['appointment_system']

# Collections
patients_collection = db['patients']
doctors_collection = db['doctors']
appointments_collection = db['appointments']

#clean up
patients_collection.drop()
doctors_collection.drop()
appointments_collection.drop()
client.drop_database("appointment_system")
print("cleaned collections and databases")
