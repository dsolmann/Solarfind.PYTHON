import requests
# import geoip
import datetime


def get_all(b):
    if b[0] != None:
        print(b)
        result = requests.get('http://api.openweathermap.org/data/2.5/weather?'
                              'lat={lat}&lon={lon}&appid=8145067c7165efd3c8450482714282c7'.format(lat=b[0],
                                                                                                  lon=b[1])).json()
    else:
        r = (54.8276, 37.6714)
        result = requests.get('http://api.openweathermap.org/data/2.5/weather?'
                              'lat={lat}&lon={lon}&appid=8145067c7165efd3c8450482714282c7'.format(lat=r[0],
                                                                                                  lon=r[1])).json()
    temp = int(result['main']['temp']) - 273, 15
    w_descr = result['weather'][0]['description']
    return {'temp': temp, 'w_dscr': w_descr, 'm_json': result}
    # return result


def get_forecast(b=(54,37)):
    if b is not None:
        r=b
    else:
        print("Hohohohohohoh!!!", b)
        r=(54,37)
    print("B:",b)
    # 8 данных на день
    # api.openweathermap.org/data/2.5/forecast?q=Moscow&appid=8145067c7165efd3c8450482714282c7
    res = requests.get(
        "http://api.openweathermap.org/data/2.5/forecast?"
        "q=Moscow&appid=8145067c7165efd3c8450482714282c7".format(lat=r[0], lon=r[1]))
    res = res.json()
    lsist = res["list"]
    asd = []
    nt = datetime.datetime.utcnow()
    lastd = None
    for l in lsist:
        d = datetime.date.fromtimestamp(l['dt'])
        d = d.day - nt.day
        if lastd is not None and lastd != d:
            asd.append(round(l['main']['temp'] - 273, 1))
        lastd = d
        # date=1: завтра и тд
    return asd[:3]


print(get_forecast())
