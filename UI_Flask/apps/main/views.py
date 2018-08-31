
from flask import *
# from flask.ext.babel import Babel, gettext
import requests
from config import *

main = Blueprint('main', __name__, template_folder='templates', static_folder='static')

def write_data(pth, r):
    with open('click_stat.dat', 'a') as f:
        f.write("{0}\t{1}\n".format(r, pth))


page_rank = {}

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


@main.route('/')
def index():
    print(request.headers)
    user_log(request.remote_addr, request.headers.get('User-Agent', default=None), req="AlphaGate",
                     loc=(request.cookies.get("lat"), request.cookies.get("lon")), uuid=request.cookies.get('uuid',
                                                                                                            default=0))
    return render_template('alpha_gate.html')


@main.route('/gsearch')
def search_index():
    user_log(request.remote_addr, request.headers.get('User-Agent', default=None), req="Search",
                     loc=(request.cookies.get("lat"), request.cookies.get("long")), uuid=request.cookies.get('uuid',
                                                                                                            default=0))
    loc = str(request.accept_languages).split(",")[0]
    try:
        exmp = requests.get(BACK_URL + "/example").text
    except requests.exceptions.ConnectionError:
        exmp = "Backend server does not working"
    return render_template('index.html', loc=loc, exmp=exmp)


@main.route('/redirect')
def redir():

    pth = request.args.get('url')
    user_log(request.remote_addr, request.headers.get('User-Agent', default=None), req="Redirect/"+pth,
                     loc=(request.cookies.get("lat"), request.cookies.get("long")), uuid=request.cookies.get('uuid',
                                                                                                            default=0))
    r = request.args.get('r')
    write_data(pth, r)
    return redirect(pth)


@main.route('/search')
def get_search():
    try:
        res = requests.get(BACK_URL + "/search?s={0}&p={1}".format(request.args.get('s'),
                                                                              request.args.get('p', default=1,
                                                                                               type=int))).json()
        exmp = requests.get(BACK_URL + "/example").text
    except requests.exceptions.ConnectionError:
        res = {'time': 0.0, 'total': 0, 'data': [["Conn error", "", "Sorry! We have connection error!"]]}
        exmp = ''
    user_log(request.remote_addr, request.headers.get('User-Agent', default=None), req="Search/"+request.args.get('s'),
                     loc=(request.cookies.get("lat"), request.cookies.get("long")), uuid=request.cookies.get('uuid',
                                                                                                            default=0))
    p = request.args.get('p', default=1, type=int)
    return render_template(
        'search_jinja.html',
        exmp=exmp,
        active_page=p,
        results=res['data'],
        pages=int(res['total'] / 20) + 1 if res['total'] % 20 else res['total'] // 20,
        r_name=request.args.get('s'),
        total=res['total'],
        time=res['time']
    )


@main.errorhandler(404)
def not_found_error():
    return render_template('404.html'), 404
