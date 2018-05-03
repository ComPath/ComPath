# -*- coding: utf-8 -*-

"""This module contains the user interface blueprint for the application"""

import datetime
import logging

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_security import roles_required

from compath.models import User
from compath.utils import get_pathway_model_by_id, get_pathway_model_by_name

log = logging.getLogger(__name__)

db_blueprint = Blueprint('db', __name__)
time_instantiated = str(datetime.datetime.now())


@db_blueprint.route('/admin/configuration')
@roles_required('admin')
def view_config():
    """Render the configuration."""
    return render_template('admin/config.html', config=current_app.config)


@db_blueprint.route('/admin/delete/db/')
@roles_required('admin')
def delete_db():
    """Destroy the database and recreates it."""
    log.info('Deleting the database')
    current_app.manager.drop_all()
    return jsonify(
        status=200,
        message='Database empty',
    )


@db_blueprint.route('/admin/user/<int:user_id>')
@roles_required('admin')
def view_user(user_id):
    """Return the given user's history.

    :param int user_id: The identifier of the user to summarize
    """
    user = current_app.manager.session.query(User).get(user_id)
    return render_template('user/activity.html', user=user)


@db_blueprint.route('/admin/users')
@roles_required('admin')
def view_users():
    """Render a list of users."""
    return render_template('admin/users.html', users=current_app.manager.session.query(User))


@db_blueprint.route('/admin/delete/mappings')
@roles_required('admin')
def delete_mappings():
    """Delete all mappings."""
    current_app.manager.delete_all_mappings()

    return jsonify(
        status=200,
        message='All Mappings have been deleted',
    )


@db_blueprint.route('/pathway/infer/hierarchy')
def infer_hierarchy():
    """Infer hierarchy for a given pathway.

    ---
    tags:
      - mappings
    parameters:
      - name: resource
        type: string
        required: true
      - name: pathway-name
        type: string
        required: true
      - name: pathway-id
        type: string
        required: true

    responses:
      200:
        description:
    """
    resource = request.args.get('resource')
    if not resource:
        flash("Invalid request. Missing 'resource-1' arguments in the request", category='warning')
        return redirect(url_for('.curation'))
    if resource not in current_app.manager_dict:
        flash("'{}' does not exist or has not been loaded in ComPath".format(resource), category='warning')
        return redirect(url_for('.curation'))

    pathway_name = request.args.get('pathway_name')
    if not pathway_name:
        flash("Missing pathway name", category='warning')
        return redirect(url_for('.curation'))

    pathway_id = request.args.get('pathway_id')
    if not pathway_id:
        flash("Missing pathway identifier", category='warning')
        return redirect(url_for('.curation'))

    pathway_from_name = get_pathway_model_by_name(current_app.manager_dict, resource, pathway_name)
    pathway_from_id = get_pathway_model_by_id(current_app, resource, pathway_id)

    if pathway_from_name != pathway_from_id:
        abort(500, 'The identifier and the name do not point the same pathway')

    inferred_hierarchies = current_app.manager.infer_hierarchy(resource, pathway_id, pathway_name)

    return jsonify(inferred_hierarchies)
