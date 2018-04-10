# -*- coding: utf-8 -*-

"""This module contains the user interface blueprint for the application"""

import datetime
import logging

from flask import Blueprint, current_app, render_template, jsonify
from flask_security import roles_required

from compath.models import User, PathwayMapping

log = logging.getLogger(__name__)

db_blueprint = Blueprint('db', __name__)
time_instantiated = str(datetime.datetime.now())


@db_blueprint.route('/admin/configuration')
@roles_required('admin')
def view_config():
    """Render the configuration"""
    return render_template('admin/config.html', config=current_app.config)


@db_blueprint.route('/admin/delete/db/')
@roles_required('admin')
def delete_db():
    """Destroys the database and recreates it"""
    log.info('Deleting the database')
    current_app.manager.drop_all()
    return jsonify(
        status=200,
        message='Database empty',
    )


@db_blueprint.route('/admin/user/<int:user_id>')
@roles_required('admin')
def view_user(user_id):
    """Returns the given user's history

    :param int user_id: The identifier of the user to summarize
    """
    user = current_app.manager.session.query(User).get(user_id)
    return render_template('user/activity.html', user=user)


@db_blueprint.route('/admin/users')
@roles_required('admin')
def view_users():
    """Renders a list of users"""
    return render_template('admin/users.html', users=current_app.manager.session.query(User))


@db_blueprint.route('/admin/delete/mappings')
@roles_required('admin')
def delete_mappings():
    """Delete all mappings"""
    current_app.manager.session.query(PathwayMapping).delete()
    current_app.manager.session.commit()

    return jsonify(
        status=200,
        message='All Mappings have been deleted',
    )
