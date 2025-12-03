# Use a Python image that includes the necessary runtime environment
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install all dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port Streamlit runs on (8501 is the default)
EXPOSE 8501

# This command runs your Streamlit app when the container starts
# --server.address=0.0.0.0 is crucial for deployment platforms
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
