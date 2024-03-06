import requests
from tkinter import *
import json
import csv
from tkinter import simpledialog
from tkinter import messagebox
import datetime
from PIL import Image, ImageTk
from environemnt_variables import API_KEY

api_key = API_KEY


def get_users_location():
    # getting user's IP address
    response = requests.get("https://api.ipify.org")
    ip_address = response.text

    request_url = 'https://geolocation-db.com/jsonp/' + ip_address
    resp = requests.get(request_url)
    result = resp.content.decode()
    result = result.split("(")[1].strip(")")
    result = json.loads(result)

    # retrieving user's cords
    latitude = result['latitude']
    longitude = result['longitude']

    return latitude, longitude


def check_clouds(clouds):
    if clouds > 80:
        image = Image.open('images/clouds.png')
    elif 40 <= clouds <= 80:
        image = Image.open('images/cloud_sunny.png')
    else:
        image = Image.open('images/sunny.png')

    image_resized1 = image.resize((200, 200))
    image_resized2 = image.resize((25, 25))
    img_bigger = ImageTk.PhotoImage(image_resized1)
    img_smaller = ImageTk.PhotoImage(image_resized2)

    return img_bigger, img_smaller


def get_current_weather(latitude, longitude):
    response = requests.get(f"https://api.openweathermap.org/data/3.0/onecall?lat={latitude}&lon="
                            f"{longitude}&units=metric&exclude=minutely,hourly,daily,alerts&appid="
                            f"{api_key}")
    data = response.json()
    current_data = data['current']
    current_temp = current_data['temp']
    current_humidity = current_data['humidity']
    current_wind_speed = current_data['wind_speed']
    current_clouds = current_data['clouds']
    current_pressure = current_data['pressure']
    current_description = data['current']['weather'][0]['description']
    return current_temp, current_humidity, current_wind_speed, current_clouds, current_pressure, current_description


def get_hourly_weather(latitude, longitude):
    response = requests.get(f"https://api.openweathermap.org/data/3.0/onecall?lat={latitude}&lon="
                            f"{longitude}&units=metric&exclude=minutely,current,daily&appid="
                            f"{api_key}")
    data = response.json()
    hourly_data = data['hourly']
    hour_temps = []
    dt_timestamps = []
    for hours in hourly_data[0:5]:  # list sliced to 5 so it can fit on screen
        hour_dt = hours['dt']
        dt_object = datetime.datetime.utcfromtimestamp(hour_dt)  # changing the time display to 24hr system
        hour_24h = dt_object.hour + 2  # 2 added because of different time zones, no idea why it displays -2hr
        if hour_24h > 24:
            hour_24h -= 24  # if hour exceeds 24hr system it displays it properly
        hourly_temp = hours['temp']
        hour_temps.append(hourly_temp)
        dt_timestamps.append(hour_24h)
    return hour_temps, dt_timestamps


# finds coords of city that has been searched
def find_city_coordinates(city_name, file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # ignoring header
        for row in reader:
            if row[0].lower() == city_name.lower():
                latitude, longitude = round(float(row[1]), 2), round(float(row[2]), 2)
                return latitude, longitude
    return None


# finds weather info of a city, where app was turned on
def find_city_info_by_coords(file_path):
    latitude, longitude = get_users_location()
    with (open(file_path, newline='', encoding='utf-8') as csvfile):
        reader = csv.reader(csvfile)
        next(reader)  # ignores header
        for row in reader:
            if (latitude - 0.1 < float(row[1]) < latitude + 0.1) and (longitude - 0.1 < float(row[2]) < longitude + 0.1):
                city_name = row[0]
                (current_temp, current_humidity, current_wind_speed, current_clouds, current_pressure,
                 current_description) = get_current_weather(latitude, longitude)
                hour_temps_not_rounded, hour_after_dt = get_hourly_weather(latitude, longitude)
                hour_temps_int = [round(temp) for temp in hour_temps_not_rounded]
                hour_temps = [str(temp) for temp in hour_temps_int]
                weather_image_bigger, weather_image_smaller = check_clouds(current_clouds)
                return [city_name, current_temp, current_humidity, current_wind_speed, hour_temps, hour_after_dt,
                        weather_image_bigger, weather_image_smaller, current_pressure, current_description]
    # return None  # returns none if location wasn't found


# creating pop up window for city searching
def open_popup():
    user_input = simpledialog.askstring(title="Search city",
                                        prompt='Search city')
    if user_input is None:
        return None
    city = user_input.lower()
    return city


# finds info about city, that has been searched and displays info on screen
def search_weather():
    city_to_find = open_popup()
    if city_to_find is None:
        return
    try:
        latitude, longitude = find_city_coordinates(city_to_find, 'cities.csv')
    except:
        messagebox.showerror("Error", "City not found")
        return
    else:
        find_city_info_by_coords('cities.csv')
        capitalized_city = city_to_find.capitalize()
        list_info_current = get_current_weather(latitude, longitude)
        current_temp = str(list_info_current[0])
        current_humidity = str(list_info_current[1])
        current_wind_speed = str(round(list_info_current[2], 1))
        current_clouds = list_info_current[3]
        current_pressure = str(list_info_current[4])
        current_description = list_info_current[5]
        weather_image_bigger = check_clouds(current_clouds)[0]
        label_temp.config(text=str(round(float(current_temp))) + '°C')
        label_humidity.config(text='Humidity: ' + current_humidity + '%')
        label_wind.config(text='Wind speed: ' + current_wind_speed + 'km/h')
        label_pressure.config(text='Pressure: ' + current_pressure + 'hP')
        town_label.config(text=capitalized_city + ',')
        label_weather_image.configure(image=weather_image_bigger)
        label_weather_image.image = weather_image_bigger  # Keep a reference to avoid garbage collection
        label_quick_info.config(text=current_description.capitalize())

        temperatures_hourly, hours_hourly = get_hourly_weather(latitude, longitude)

        for i, (hour, temp) in enumerate(zip(hours_hourly, temperatures_hourly)):
            # Get the existing label widgets by index
            weather_image_smaller = check_clouds(current_clouds)[1]
            hour_frame = hourly_frame_bar.winfo_children()[i]
            widget_icon = hour_frame.winfo_children()[0]  # icon is the first child
            hour_label = hour_frame.winfo_children()[1]  # hour is the second child
            temp_widget_label = hour_frame.winfo_children()[2]  # temp is the third child
            widget_icon.configure(image=weather_image_smaller)
            widget_icon.image = weather_image_smaller  # Keep a reference to avoid garbage collection
            hour_label.config(text=str(hour) + ':00')
            temp_widget_label.config(text=str(round(temp)) + '°C')


# setting screen config
window = Tk()
window.title("Weather App")
window.configure(background="lightblue")

w = 600
h = 800

# get screen width and height
ws = window.winfo_screenwidth()  # width of the screen
hs = window.winfo_screenheight()  # height of the screen

# calculate x and y coordinates for the Tk root window
x = (ws/2) - (w/2)
y = (hs/2) - (h/2)

# set the dimensions of the screen
# and where it is placed
window.geometry('%dx%d+%d+%d' % (w, h, x, y))

# adding images (buttons, weather etc.)
image_clouds = PhotoImage(file='images/clouds.png')
image_cloud_sunny = PhotoImage(file='images/cloud_sunny.png')
image_sunny = PhotoImage(file='images/sunny.png')

image_search = PhotoImage(file="images/search.png")
image_details = PhotoImage(file='images/details.png')
image_alerts = PhotoImage(file='images/alerts.png')

image_wind = PhotoImage(file='images/wind.png')
image_humidity = PhotoImage(file='images/humidity.png')
image_pressure = PhotoImage(file='images/pressure.png')

# calling functions and assigning variables so it doesn't request api multiple times
try:
    (city_name, current_temp, current_humidity, current_wind_speed, hour_temps, hour_after_dt, weather_image_bigger,
        weather_image_smaller, current_pressure, current_description) = (find_city_info_by_coords('cities.csv'))
except:
    messagebox.showerror("Error", "Couldn't get current location")
else:

    # empty label for creating top padding
    label_empty_pad = Label(window, bg="lightblue", pady=30)
    label_empty_pad.pack(side='top')

    # setting display of city and country (Poland)
    town_name_frame = Frame(window, bg='lightblue')
    town_name_frame.pack(side='top')

    town_label = Label(town_name_frame)
    town_label.config(text=city_name + ',', bg="lightblue", font=('Courier', 20, 'bold'))
    town_label.pack(side='top')

    country_name_label = Label(town_name_frame, anchor='s')
    country_name_label.config(text='Poland', bg="lightblue", font=('Courier', 10))
    country_name_label.pack(side='bottom')

    # displaying weather image
    label_weather_image = Label(window, image=weather_image_bigger, bg="lightblue")
    label_weather_image.pack(side='top')

    # creating labels for info about weather
    label_temp = Label(window)
    label_temp.config(text=str(round(current_temp)) + '°C', bg="lightblue", font=('Courier', 25, 'bold'), pady=5)
    label_temp.pack(side='top')

    label_quick_info = Label(window)
    label_quick_info.config(text=current_description.capitalize(), bg="lightblue", font=('Courier', 10), pady=5)
    label_quick_info.pack(side='top')

    # frame and labels with wind, humidity and rain and their icons
    label_frame = Frame(window, padx=25, bg='lightblue', pady=5)
    label_frame.pack(side='top', expand=True, fill='x')

    label_wind_icon = Label(label_frame, image=image_wind, bg="lightblue")
    label_wind_icon.pack(side='left')
    label_wind = Label(label_frame, text='Wind speed: ' + str(current_wind_speed) + 'km/h', bg='lightblue', font=('Courier', 10))
    label_wind.pack(side='left')

    # creating frame for humidity to be centered in whole label_frame
    humidity_frame = Frame(label_frame, bg='lightblue')
    humidity_frame.pack(side='left', expand=True)
    label_humidity_icon = Label(humidity_frame, image=image_humidity, bg='lightblue')
    label_humidity_icon.pack(side='left')
    label_humidity = Label(humidity_frame, text='Humidity: ' + str(current_humidity) + '%',
                           bg='lightblue',
                           font=('Courier', 10))
    label_humidity.pack(side='left')

    label_pressure = Label(label_frame, text='Pressure: ' + str(current_pressure) + 'hP', bg='lightblue', font=('Courier', 10))
    label_pressure.pack(side='right')
    label_pressure_icon = Label(label_frame, image=image_pressure, bg='lightblue')
    label_pressure_icon.pack(side='right')

    # creating hourly forecast
    hourly_frame = Frame(window, bg='lightblue', pady=5)
    hourly_frame.pack(side='top', fill='x')

    hourly_info_label = Label(hourly_frame, text='ⓘ Hourly info', bg='lightblue', font=('Courier', 10), pady=10, padx=10)
    hourly_info_label.pack(side='top', anchor='w')

    hourly_frame_bar = Frame(hourly_frame, bg='lightblue', pady=5)
    hourly_frame_bar.pack(side='top', fill='x')

    # for loop creating frames and each one contains one hour info
    for hour, temp in zip(hour_after_dt, hour_temps):
        hour_frame = Frame(hourly_frame_bar, bg='lightblue', pady=10)
        hour_frame.pack(side='left', expand=True)
        hour_widget_icon = Label(hour_frame, image=weather_image_smaller, bg='lightblue')
        hour_widget_icon.pack(side='top')
        hour_label = Label(hour_frame, bg='lightblue')
        hour_label.config(text=str(hour) + ':00')
        hour_label.pack(side='top')
        temp_widget_label = Label(hour_frame, bg='lightblue', padx=10)
        temp_widget_label.config(text=temp + '°C')
        temp_widget_label.pack(side='bottom')

    # creating bottom buttons
    button_frame = Frame(window)
    button_frame.pack(side='bottom', expand=True, pady=10)

    button_search = Button(button_frame, text='search', bg='lightgrey', image=image_search, command=search_weather)
    button_search.pack(side='left')

    button_details = Button(button_frame, text='details', bg='lightgrey', image=image_details)
    button_details.pack(side='left')

    button_alerts = Button(button_frame, text='alerts', bg='lightgrey', image=image_alerts)
    button_alerts.pack(side='left')

    window.mainloop()
