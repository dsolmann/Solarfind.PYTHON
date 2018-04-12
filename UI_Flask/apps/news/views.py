from flask import *


news = Blueprint('news', __name__, template_folder='templates', static_folder='static')


@news.route('/')
def get_news():
    return render_template('news.html',
                           name="Lorem ipsum",
                           text="This text here for example...",
                           date="11.04.2018"
                           )
