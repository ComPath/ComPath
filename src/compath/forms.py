# -*- coding: utf-8 -*-

""" This module contains the forms used in ComPath"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import TextAreaField
from wtforms.fields import SubmitField
from wtforms.validators import DataRequired, ValidationError


class GeneSetForm(FlaskForm):
    geneset = TextAreaField('Geneset', id="geneset-input", validators=[DataRequired()])
    submit = SubmitField('Submit')


class GeneSetFileForm(FlaskForm):
    """Builds the form for uploading gene sets with weight"""
    file = FileField(
        'Gene Set File',
        validators=[
            DataRequired(),
            FileAllowed(['csv'], 'Only files with the *.csv extension are allowed')
        ],
    )
    submit = SubmitField('Submit File')
