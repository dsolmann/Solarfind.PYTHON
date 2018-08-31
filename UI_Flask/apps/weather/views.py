from flask import *
from . import utils

weather = Blueprint('weather', __name__, template_folder='templates', static_folder='static')

def user_log(ip, browser, req, loc=None, uuid=None, lfolder="Logs"):
    import  json
    print("USER ",uuid, ip, loc, browser, "with request", req)
    g = {}
    g['uuid']=uuid
    g['ip']=ip
    g['loc']=loc
    g['browser']=browser
    if req.split("/", maxsplit=1)[0]=="search":
        g['application']='search'
        g['request']=req.split("/", maxsplit=1)[1]
    else:
        g['aplication']=req
    with open(lfolder+"/users.log", 'a') as f:
      json.dump(g, f)
      f.write('\n')
      f.close()



def capitalize(string, lower_rest=False):
    return string[:1].upper() + (string[1:].lower() if lower_rest else string[1:])


@weather.route('/')
def get_weather():
    user_log(request.remote_addr, request.headers.get('User-Agent', default=None), req="Weather",
                     loc=(request.cookies.get("lat"), request.cookies.get("long")), uuid=request.cookies.get('uuid',
                                                                                                            default=0))
    lat = request.cookies.get('lat', default=None)
    longi = request.cookies.get('long', default=None)
    m_data = utils.get_all([lat, longi])
    temp = m_data['temp'][0]
    status = m_data['w_dscr']
    status_img = status.replace(' ', '_') + '.jpg'
    return render_template('weather.html', temp=temp, status=capitalize(status), status_img=status_img,
                           ndata=utils.get_forecast([lat, longi]))
