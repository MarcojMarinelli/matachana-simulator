# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code to the working directory
COPY matachanaSim.py .

# Expose the ports the app runs on
EXPOSE 8000
EXPOSE 8001

# Define the command to run your app
CMD ["python3", "matachanaSim.py"]
