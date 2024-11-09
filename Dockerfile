FROM python:3.12

# Set the working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
   
RUN pip3 install --upgrade pymongo

# Copy the entire contents of the current directory (local machine) into the /app directory in the container
COPY . /app

# Expose the port the app runs on
EXPOSE 6000

# Command to run the application
CMD ["python3", "app.py"]
