from flask import *
from raven.contrib.flask import Sentry
from config import Configuration

from apps.main.views import main

from apps.weather.views import weather
from apps.news.views import news
from apps.admin.views import admin
from apps.akadoton.views import akadoton

import sys
sys.path.append('/Alpha_1/UI_Flask/pycharm-debug-py3k.egg')

app = Flask(__name__, static_folder=None, template_folder=None)
app.register_blueprint(main)
app.register_blueprint(weather, url_prefix='/weather')
app.register_blueprint(news, url_prefix='/news')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(akadoton, url_prefix='/akadoton')


app.config.from_object(Configuration)


sentry = Sentry(app, dsn='https://082b8cf14f494e2f9ea84e2b7614347f:89d3be577d8c416b9324294869126180@sentry.io/1188746')


if __name__ == "__main__":
    app.run(host="0.0.0.0")
