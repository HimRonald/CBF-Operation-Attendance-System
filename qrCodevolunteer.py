import qrcode
import pandas as pd
import json
import os
from datetime import datetime

# Create output directory if it doesn't exist
output_dir = 'volunteer_qrcodes'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Read from CSV file
df = pd.read_csv('CBF11th_data.csv')
volunteers = df.to_dict('records')


def generate_qr_codes(volunteers):
    for volunteer in volunteers:
        # Create the filename for the QR code image
        filename = f"{output_dir}/{volunteer['id']}_{volunteer['name'].replace(' ', '_')}.png"

        # Check if the QR code already exists
        if os.path.exists(filename):
            print(
                f"QR code for {volunteer['name']} already exists. Skipping...")
            continue

        # Create a unique identifier and data payload
        volunteer_data = {
            "id": volunteer["id"],
            "name": volunteer["name"],
            "team": volunteer["team"],
        }

        # Convert data to JSON string
        qr_data = json.dumps(volunteer_data)

        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Add the data
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Create the QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")

        # Save the image
        qr_image.save(filename)

        print(
            f"Generated QR code for {volunteer['name']} - {volunteer['team']}")


# Generate QR codes
generate_qr_codes(volunteers)

# Optional: Generate a CSV file with volunteer information and QR code file paths


def generate_volunteer_csv(volunteers):
    volunteer_records = []
    for volunteer in volunteers:
        record = volunteer.copy()
        record['qr_code_file'] = f"{volunteer['id']}_{volunteer['name'].replace(' ', '_')}.png"
        volunteer_records.append(record)

    df = pd.DataFrame(volunteer_records)
    df.to_csv(f"{output_dir}/volunteer_records.csv", index=False)
    print("\nGenerated volunteer records CSV file")


generate_volunteer_csv(volunteers)
