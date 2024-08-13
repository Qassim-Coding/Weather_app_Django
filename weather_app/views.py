from django.shortcuts import render
import datetime
import requests
# requests au pluriel est une librairie à part
import os
from django.conf import settings

def index(request):
    # Récupérer l'API Key à partir des variables d'environnement
    API_KEY = os.getenv("WEATHER_API_KEY")
    if not API_KEY:
        # En cas d'absence de la variable d'environnement API_KEY, renvoie une page d'erreur avec un message explicatif.
        return render(request, "weather_app2/error.html", {"message": "La clé API n'est pas configurée."})

    # Définir l'URL pour obtenir les données météo actuelles.
    current_weather_url = "https://api.openweathermap.org/data/2.5/weather?q={}&appid={}"
    # Définir l'URL pour obtenir les prévisions météo (3 heures d'intervalle).
    forecast_url = "https://api.openweathermap.org/data/2.5/forecast?q={}&appid={}"

    if request.method == "POST":
        # Si la méthode est POST, cela signifie que l'utilisateur a soumis une ville (ou deux).
        city1 = request.POST['city1']  # Récupérer le nom de la première ville.
        city2 = request.POST.get('city2', None)  # Récupérer le nom de la deuxième ville (facultatif).

        # Récupérer les données météo pour la première ville.
        weather_data1, daily_forecasts1 = fetch_weather_and_forecast(city1, API_KEY, current_weather_url, forecast_url)

        # Vérifie si les données météo pour la première ville sont disponibles
        if weather_data1 is None:
            # Si aucune donnée n'est disponible, renvoie une page d'erreur avec un message explicatif.
            return render(request, "weather_app2/error.html", {"message": f"Impossible de récupérer les données pour la ville {city1}."})

        if city2:
            # Récupérer les données météo pour la deuxième ville.
            weather_data2, daily_forecasts2 = fetch_weather_and_forecast(city2, API_KEY, current_weather_url, forecast_url)

            # Vérifie si les données météo pour la deuxième ville sont disponibles
            if weather_data2 is None:
                # Si aucune donnée n'est disponible, renvoie une page d'erreur avec un message explicatif.
                return render(request, "weather_app2/error.html", {"message": f"Impossible de récupérer les données pour la ville {city2}."})
        else:
            weather_data2, daily_forecasts2 = None, None  # Si aucune deuxième ville n'est saisie, initialise les données à None.

        # Préparer les données pour les transmettre au template.
        context = {
            "weather_data1": weather_data1,
            "daily_forecasts1": daily_forecasts1,
            "weather_data2": weather_data2,
            "daily_forecasts2": daily_forecasts2,
        }

        # Afficher les données météo dans le template `index.html`.
        return render(request, "weather_app2/index.html", context)
    else:
        return render(request, "weather_app2/index.html")  # Si la méthode n'est pas POST, affiche simplement la page d'accueil.

def fetch_weather_and_forecast(city, api_key, current_weather_url, forecast_url):
    # Récupération des données météo actuelles
    response = requests.get(current_weather_url.format(city, api_key)).json()
    print("Current weather response:", response)

    if response.get('cod') != 200:
        return None, None

    weather_data = {
        "city": city,
        "temperature": round(response["main"]["temp"] - 273.15, 2),
        "description": response["weather"][0]["description"],
        "icon": response["weather"][0]["icon"],
    }

    # Récupération des prévisions météo toutes les 3 heures
    forecast_response = requests.get(forecast_url.format(city, api_key)).json()
    print("Forecast response:", forecast_response)

    if forecast_response.get('cod') != "200":
        return weather_data, None

    daily_forecasts = []
    added_dates = set()  # Pour garder une trace des dates déjà ajoutées

    for forecast in forecast_response['list']:
        forecast_date = forecast["dt_txt"].split(" ")[0]  # Extraire la date (sans l'heure)
        if forecast_date not in added_dates:
            # Convertir la date en jour de la semaine
            day_name = datetime.datetime.strptime(forecast_date, "%Y-%m-%d").strftime("%A")
            forecast_data = {
                "day": day_name,
                "temperature": round(forecast["main"]["temp"] - 273.15, 2),
                "description": forecast["weather"][0]["description"],
                "icon": forecast["weather"][0]["icon"],
            }
            daily_forecasts.append(forecast_data)
            added_dates.add(forecast_date)  # Marquer la date comme ajoutée
        if len(daily_forecasts) >= 5:
            break  # Stopper après 5 jours de prévisions

    return weather_data, daily_forecasts
