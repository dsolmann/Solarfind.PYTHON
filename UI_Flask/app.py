from flask import *
import weather_utils
import requests
import json

admin = ('admin', '12345678')
app = Flask(__name__)
app.secret_key = 'so_secret!'

back_url = 'http://127.0.0.1:8121'


def write_data(pth, r):
    with open('click_stat.dat', 'a') as f:
        f.write("{0}\t{1}\n".format(r, pth))


page_rank = {}


@app.route('/')
def index():
    return render_template('alpha_gate.html')


@app.route('/news')
def news():
    render_template('news.html')


@app.route('/gsearch')
def index_o():
    loc = str(request.accept_languages).split(",")[0]
    try:
        exmp = requests.get(back_url + "/example").text
    except requests.exceptions.ConnectionError:
        exmp = "Backend server does not working"
    return render_template('index.html', loc=loc, exmp=exmp)


@app.route('/redirect')
def redir():
    pth = request.args.get('url')
    r = request.args.get('r')
    write_data(pth, r)
    return redirect(pth)


@app.route('/flask_api/login')
def auth():
    password = request.args.get('password')
    login = request.args.get('email')
    if login == admin[0] and password == admin[1]:
        resp = make_response(url_for('panel'))
        session['user'] = 'admin'
        return resp
    return redirect(url_for('admin_login'))


@app.route('/admin_panel/panel')
def panel():
    if session.get('user'):
        return render_template('admin_panel/panel.html')
    abort(403)


@app.route('/admin_panel/login')
def admin_login():
    return render_template('admin_panel/login.html')


@app.route('/admin_functional/s_kill')
def panesl():
    if session.get('user'):
        return "Sorry! But is temporarily not available"
    abort(403)


@app.route('/jsearch')
def get_search():
    try:
        res = json.loads(requests.get(back_url + "/search?s={0}&p={1}".format(request.args.get('s'),
                                                                              request.args.get('p', default=1,
                                                                                               type=int))).json())
        exmp = requests.get(back_url + "/example").text
    except requests.exceptions.ConnectionError:
        res = {'time': 0.0, 'total': 0, 'data': [["Conn error", "", "Sorry! We have connection error!"]]}
        exmp = ''
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


@app.route('/weather')
def weather():
    def capitalize(string, lower_rest=False):
        return string[:1].upper() + (string[1:].lower() if lower_rest else string[1:])

    debug_f = request.args.get('debug')
    if debug_f is None:
        debug_f = 0
    print(debug_f)
    ips = request.remote_addr
    m_data = weather_utils.get_all(ips=ips)
    temp = m_data['temp'][0]
    status = m_data['w_dscr']
    print("Temp:", temp, "Status:", status)
    if debug_f != 0:
        status = debug_f
    status_img = status.replace(' ', '_') + '.jpg'
    return render_template('weather.html', temp=temp, status=capitalize(status), status_img=status_img,
                           ndata=weather_utils.get_forecast())


@app.errorhandler(404)
def not_found_error(_):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0")
