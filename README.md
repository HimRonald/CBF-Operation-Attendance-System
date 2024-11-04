# CBF Operation Attendance System

This system was built for the Cambodia Book Fair 2024 to manage volunteer attendance efficiently. It allows volunteers to check in and out using a QR code scanner, and provides an interface for administrators to view and download attendance records.

## Features

- Volunteer check-in and check-out using QR codes
- Dashboard to view attendance records
- Export attendance records to Excel
- Import volunteer data from CSV files

## How to Use

### Prerequisites

- Python 3.x
- Flask
- SQLAlchemy
- Pandas
- Openpyxl
- pytz

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/HimRonald/CBF-Operation-Attendance-System.git
    cd CBF-Operation-Attendance-System
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Set up the database configuration in `database/config.py`.

4. Initialize the database:
    ```sh
    python app.py
    ```

### Running the Application

1. Start the Flask application:
    ```sh
    python app.py
    ```

2. Open your web browser and navigate to `http://127.0.0.1:5000/`.

### Usage

- **Home Page**: Navigate to the home page to see the main interface.
- **Scanner Page**: Use the scanner page to check in and out by scanning QR codes.
- **Dashboard Page**: View attendance records and search by date or volunteer name/team.
- **Download Attendance**: Export attendance records to an Excel file by selecting a date.
- **Import Volunteers**: Upload a CSV file to import volunteer data.

## Repository

For more details, visit the [GitHub repository](https://github.com/HimRonald/CBF-Operation-Attendance-System).
