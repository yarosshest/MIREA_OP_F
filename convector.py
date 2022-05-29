def pressure(prs):
    return prs * 0.75


def direction(deg):
    if deg < 22.5:
        return "северый"
    elif deg < 67.5:
        return "северо-востоый"
    elif deg < 112.5:
        return "востокый"
    elif deg < 157.5:
        return "юго-востокый"
    elif deg < 202.5:
        return "югый"
    elif deg < 247.5:
        return "юго-западый"
    elif deg < 295.5:
        return "западый"
    elif deg < 337.5:
        return "северо-западый"
    elif deg > 337.5:
        return "северый"


def type_wind(spd):
    if spd < 0.2:
        return "штиль"
    elif spd < 1.5:
        return "тихий"
    elif spd < 3.3:
        return "лёгкий"
    elif spd < 5.4:
        return "слабый"
    elif spd < 7.9:
        return "умеренный"
    elif spd < 10.7:
        return "свежий"
    elif spd < 13.8:
        return "сильный"
    elif spd < 17.1:
        return "крепкий"
    elif spd < 20.7:
        return "очень крепкий"
    elif spd < 24.4:
        return "шторм"
    elif spd < 28.4:
        return "сильный шторм"
    elif spd < 32.6:
        return "жестокий шторм"
    elif spd > 33:
        return "ураган"


def translate_weather(wth):
    if wth == "Thunderstorm":
        return "Гроза"
    elif wth == "Rain":
        return "Дождь"
    elif wth == "Snow":
        return "Снег"
    elif wth == "Atmosphere":
        return "Туманно"
    elif wth == "Clear":
        return "Ясное небо"
    elif wth == "Clouds":
        return "Облачно"