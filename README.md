# TeenPhoneAddictionApp
Teen Phone Addiction Analysis Web App

 ## Project Overview
 This is a Flask-based web application for analyzing teen phone addiction data, developed as a group project for BDAT 1004 Data Analytics Programming. The app allows users to sign up, log in, upload a CSV dataset (from Kaggle), and view basic data summaries for now.

 ## Dataset
 - **Source**: Teen Phone Addiction Dataset from Kaggle (https://www.kaggle.com/datasets/khushikyad001/teen-phone-addiction-and-lifestyle-survey)
 - **Description**: This synthetic dataset simulates real-world data on teenage phone usage habits, mental health indicators, academic performance, and lifestyle behaviors. It aims to help analyze correlations between phone addiction and various aspects of adolescent life, including sleep, exercise, self-esteem, and school performance. It’s designed for educational, research, and machine learning applications such as behavioral prediction, clustering, and health risk classification.

 ## Features
 - **User Authentication**: Secure login and signup with SQLite database storage.
 - **CSV Upload**: Users can upload a CSV file, which is validated and stored.
 - **Data Summary**: Displays basic statistics (rows, columns, null values, descriptive stats).
 - **Minimalist UI**: Clean, modern interface with a responsive design.

 ## Setup Instructions
 1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/TeenPhoneAddictionApp.git
    ```
 2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    ```
 3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
 4. Run the app:
    ```bash
    python app.py
    ```
 5. Open `http://127.0.0.1:5000` in a browser.

 ## Project Structure
 ```
 TeenPhoneAddictionApp/
 ├── app.py              # Main Flask application
 ├── templates/          # HTML templates
 ├── static/css/         # CSS styles
 ├── uploads/            # Uploaded CSV files
 ├── users.db            # SQLite database for users
 ├── requirements.txt    # Dependencies
 ├── .gitignore          # Git ignore file
 ```

 ## Team Members
 - Amanda Ratcliffe
 - Hrishi Raj Sonar
 - Jaganlal Manilal
 - Minnu Varghese