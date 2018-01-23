# -*- coding: utf-8 -*-

""" This module contains the flask-admin application to visualize the db"""

import logging
import time

from flask import Flask
from flask_bootstrap import Bootstrap

from compath.main_service import ui_blueprint

log = logging.getLogger(__name__)

bootstrap = Bootstrap()


def create_app(connection=None, url=None):
    """Creates a Flask application

    :type connection: Optional[str]
    :rtype: flask.Flask
    """

    t = time.time()

    app = Flask(__name__)
    bootstrap.init_app(app)
    app.register_blueprint(ui_blueprint)

    log.info('Done building %s in %.2f seconds', app, time.time() - t)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)