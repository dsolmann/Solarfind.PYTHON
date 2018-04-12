from flask import *


admin = Blueprint('admin', __name__, template_folder='templates', static_folder='static')

a = ('admin', '1234')


@admin.route('/login', methods=['POST', 'GET'])
def auth():
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
