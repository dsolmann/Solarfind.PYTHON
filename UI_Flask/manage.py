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
    app.run(host="0.0.0.0")
