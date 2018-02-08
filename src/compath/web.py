# -*- coding: utf-8 -*-

""" This module contains the flask-admin application to visualize the db"""

import logging
import time

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect
from compath.main_service import ui_blueprint
from compath import managers

log = logging.getLogger(__name__)

bootstrap = Bootstrap()


def create_app(connection=None):
    """Creates a Flask application

    :type connection: Optional[str]
    :rtype: flask.Flask
    """

    t = time.time()

    app = Flask(__name__)

    app.config['COMPATH_CONNECTION'] = connection

    # TODO: Change for deployment. Create a new with 'os.urandom(24)'
    app.secret_key = 'a\x1c\xd4\x1b\xb1\x05\xac\xac\xee\xcb6\xd8\x9fl\x14%B\xd2W\x9fP\x06\xcb\xff'

    csrf = CSRFProtect(app)
    bootstrap.init_app(app)
    app.register_blueprint(ui_blueprint)

    app.manager_dict = {
        name: Manager(connection=connection)
        for name, Manager in managers.items()
    }

    log.info('Loading resource distributions')

    app.resource_distributions = {
        name: Manager(connection=connection).get_pathway_size_distribution()
        for name, Manager in managers.items()
    }

    log.info('Done building %s in %.2f seconds', app, time.time() - t)

    return app


if __name__ == '__main__':
    app_ = create_app()
    app_.run(debug=True, host='0.0.0.0', port=5000)
