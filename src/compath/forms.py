# -*- coding: utf-8 -*-

"""This module contains the forms used in ComPath."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import TextAreaField
from wtforms.fields import SubmitField, BooleanField
from wtforms.validators import DataRequired


class GeneSetForm(FlaskForm):
    """Pathway enrichment form."""
    geneset = TextAreaField('Geneset', id="geneset-input", validators=[DataRequired()])
    filter_non_significant = BooleanField(default="checked", description='Filter Non-Significant Pathways (FDR>5%)')
    submit = SubmitField('Submit')


class GeneSetFileForm(FlaskForm):
    """Build the form for uploading gene sets."""
    file = FileField(
        'Gene Set File',
        validators=[
            DataRequired(),
            FileAllowed(['txt', 'gmt'], 'Only files with the .txt and .gmt extension are allowed')
        ]
    )
    submit = SubmitField('Submit File')
