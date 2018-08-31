
from flask import *
news = Blueprint('news', __name__, template_folder='templates', static_folder='static')

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


@news.route('/')
def get_news():
    user_log(request.remote_addr, request.headers.get('User-Agent', default=None), req="News",
                     loc=(request.cookies.get("lat"), request.cookies.get("long")), uuid=request.cookies.get('uuid',
                                                                                                            default=0))
    return render_template('news.html',
                           name="Lorem ipsum",
                           text="This text here for example...",
                           date="11.04.2018"
                           )
