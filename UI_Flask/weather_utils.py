def GetAll(ips='127.0.0.1', city='Moscow'):
    import requests
    try:
        import geoip
        print(ips)
        a = geoip.open_database('service_data/geoip_data.mmdb')
        b = a.lookup(ips)
        result = requests.get('http://api.openweathermap.org/data/2.5/weather?'
                              'lat={lat}&lon={lon}&appid=8145067c7165efd3c8450482714282c7'.format(lat=b.location[0],
                                                                                                  lon=b.location[
                                                                                                      1])).json()
    except:
        r = (54.8276, 37.6714)
        result = requests.get('http://api.openweathermap.org/data/2.5/weather?'
                              'lat={lat}&lon={lon}&appid=8145067c7165efd3c8450482714282c7'.format(lat=r[0],
                                                                                                  lon=r[1])).json()
    temp = int(result['main']['temp']) - 273, 15
    w_descr = result['weather'][0]['description']
    return {'temp': temp, 'w_dscr': w_descr, 'm_json': result}
    # return result
def GetForecast():

    # 8 данных на день
    # api.openweathermap.org/data/2.5/forecast?q=Moscow&appid=8145067c7165efd3c8450482714282c7
    import datetime, requests
    res = requests.get("http://api.openweathermap.org/data/2.5/forecast?q=Moscow&appid=8145067c7165efd3c8450482714282c7")
    res= res.json()
    lsist =  res["list"]
    asd=[]
    nt=datetime.datetime.utcnow()
    lastd = None
    for l in lsist:
        d = datetime.date.fromtimestamp(l['dt'])
        d = d.day-nt.day
        if lastd != None and lastd != d:
          asd.append(round(l['main']['temp']-273, 1))
        lastd=d
        #date=1: завтра и тд
    return asd[:3]
print(GetForecast())