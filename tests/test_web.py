# -*- coding: utf-8 -*-

"""
Reference for testing Flask

- Flask Documentation http://flask.pocoo.org/docs/0.12/testing/
- Flask Cookbook: http://flask.pocoo.org/docs/0.12/tutorial/testing/
"""

import logging
from bio2bel.testing import TemporaryConnectionMethodMixin

from compath.views.main_service import ui_blueprint
from compath.web import create_app

log = logging.getLogger(__name__)
log.setLevel(10)

TEST_USER_EMAIL = 'test@example.com'
TEST_USER_PASSWORD = 'password'
TEST_SECRET_KEY = 'tests!!!!'


class WebTest(TemporaryConnectionMethodMixin):
    def setUp(self):
        """Build a connection, a Flask app, and a Flask app testing client."""
        super().setUp()

        self.app = create_app(connection=self.connection)

        self.app.register_blueprint(ui_blueprint)

        self.client = self.app.test_client()

        with self.app.app_context():
            self.app.manager.create_all()

    def test_view_home(self):
        with self.app.app_context():
            self.client.get('/')
