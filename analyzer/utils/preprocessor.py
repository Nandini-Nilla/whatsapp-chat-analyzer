import re
import pandas as pd
from datetime import datetime

def preprocess(data, chat_format):
    """
    Preprocess WhatsApp chat data based on the selected format.
    """
    if chat_format == "format1":
        # Regex for format: DD/MM/YYYY, HH:MM AM/PM - User: Message
        pattern = r'(\d{2}/\d{2}/\d{4}),\s(\d{1,2}:\d{2}\s[APap][mM])\s-\s([^:]+):\s(.+)'
    elif chat_format == "format2":
        # Regex for format: [DD/MM/YY, HH:MM:SS AM/PM] User: Message
        pattern = r'\[(\d{2}/\d{2}/\d{2}),\s(\d{1,2}:\d{2}:\d{2}\s[APap][mM])\]\s([^:]+):\s(.+)'
    else:
        raise ValueError("Invalid chat format selected.")

    # Split the data into lines
    lines = data.splitlines()

    # Lists to store parsed data
    dates, times, users, messages = [], [], [], []

    for line in lines:
        match = re.match(pattern, line)
        if match:
            date_str, time_str, user, message = match.groups()
            try:
                # Parse date and time
                if chat_format == "format1":
                    date = datetime.strptime(date_str, '%d/%m/%Y').date()
                    time = datetime.strptime(time_str, '%I:%M %p').time()
                elif chat_format == "format2":
                    date = datetime.strptime(date_str, '%d/%m/%y').date()
                    time = datetime.strptime(time_str, '%I:%M:%S %p').time()
                dates.append(date)
                times.append(time)
                users.append(user)
                messages.append(message)
            except ValueError:
                # Skip invalid date/time formats
                continue
        else:
            # Skip system messages or invalid lines
            continue

    # Convert to DataFrame
    df = pd.DataFrame({
        'date': dates,
        'time': times,
        'user': users,
        'message': messages
    })

    # Ensure 'date' and 'time' columns are of type datetime
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S', errors='coerce').dt.time

    # Drop rows with invalid dates or times
    df.dropna(subset=['date', 'time'], inplace=True)

    # Extract more date-time details
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.hour
    df['minute'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.minute

    # Create time period labels (e.g., "10-11 AM")
    df['period'] = df['hour'].apply(lambda h: f"{h}-{h+1 if h < 23 else 0}")

    return df