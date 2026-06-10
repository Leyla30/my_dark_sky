# Welcome to My Dark Sky

---

## Task

The goal of this project was to recreate a modern weather forecasting web application similar to Dark Sky using Python and Flask.
The challenge was to build a beautiful UI, integrate a weather API, implement caching, and deploy the application to the cloud.

## Description

This project is a weather web application built with Flask and OpenWeather API.

Features:

* Search weather by city
* Current weather display
* Forecast information
* Beautiful dark UI using Tailwind CSS
* Cache system using JSON files
* Deployed online with Render

The application stores weather requests for 5 minutes to reduce API calls and improve performance.

## Installation

First, clone the repository from Qwasar Gitea:

```bash
git clone git@git.us.qwasar.io:my_dark_sky_214257_daprnd/my_dark_sky.git
```

Move into the project folder:

```bash
cd my_dark_sky
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

Install all required dependencies:

```bash
pip install -r requirements.txt
```

The project uses Flask, Requests, and Gunicorn.

## Usage

Run the Flask application locally using:

```bash
python app.py
```

After starting the server, open your browser and go to:

```bash
http://127.0.0.1:5000
```

You can search for weather information by entering a city name.

The application displays:

* current weather
* temperature
* humidity
* wind speed
* forecast information

The project also includes a caching system that stores API responses for 5 minutes to reduce unnecessary API requests.


## Technologies Used

* Python
* Flask
* OpenWeather API
* Tailwind CSS
* Gunicorn
* Render

### The Core Team

<span><i>Made at <a href='https://qwasar.io'>Qwasar SV -- Software Engineering School</a></i></span> <span><img alt='Qwasar SV -- Software Engineering School Logo' src='https://storage.googleapis.com/qwasar-public/qwasar-logo_50x50.png' width='20px' /></span>
