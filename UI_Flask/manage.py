from flask import *

from config import Configuration

from apps.main.views import main
from apps.weather.views import weather
from apps.news.views import news
from apps.admin.views import admin


app = Flask(__name__, static_folder=None, template_folder=None)
app.register_blueprint(main)
app.register_blueprint(weather, url_prefix='/weather')
app.register_blueprint(news, url_prefix='/news')
app.register_blueprint(admin, url_prefix='/admin')


app.config.from_object(Configuration)


if __name__ == "__main__":
    from raven.contrib.flask import Sentry
    sentry = Sentry(app, dsn='https://082b8cf14f494e2f9ea84e2b7614347f:89d3be577d8c416b9324294869126180@sentry.io/1188746')
    app.run(host="0.0.0.0")
