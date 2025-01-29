# Python 3.10 base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port if you need a web server for analytics
# EXPOSE 8080

# Run the application
CMD ["python", "app.py"]



# docker build -t telegram-ai-bot .
# docker run -d --env-file .env --name telegram-bot telegram-ai-bot