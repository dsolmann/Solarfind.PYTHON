
from flask import *

admin = Blueprint('admin', __name__, template_folder='templates', static_folder='static')

a = ('admin', '1234')

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


@admin.route('/login', methods=['POST', 'GET'])
def auth():
    user_log(request.remote_addr, request.headers.get('User-Agent', default=None), req="admin",
                     loc=(request.cookies.get("lat"), request.cookies.get("long")), uuid=request.cookies.get('uuid',
                                                                                                            default=0))
    if request.method == 'POST':
        password = request.args.get('password')
        login = request.args.get('email')
        if login == a[0] and password == a[1]:
            session['user'] = 'admin'
            return redirect(url_for('panel'))
    return render_template('login.html')


@admin.route('/panel')
def panel():
    if session.get('user'):
        return render_template('panel.html')
    abort(403)


@admin.route('/action')
def action(_):
    if session.get('user'):
        return "Sorry, but it is temporarily not available!"
    abort(403)
