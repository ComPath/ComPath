# -*- coding: utf-8 -*-

""" This module contains the forms used in ComPath"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import TextAreaField
from wtforms.fields import RadioField, StringField, SubmitField
from wtforms.validators import DataRequired


class GeneSetForm(FlaskForm):
    geneset = TextAreaField('Geneset', id="geneset-input", validators=[DataRequired(message="Not valid input")])
    submit = SubmitField('Submit')


class GeneSetFileForm(FlaskForm):
    """Builds the form for uploading gene sets with weight"""
    file = FileField('Differential Gene Expression File', validators=[DataRequired()])
    gene_column = StringField('Gene Symbol Column Name', default='Gene.symbol')
    weight_column = StringField('Weight Column', validators=[DataRequired()])
    separator = RadioField(
        'Separator',
        choices=[
            ('\t', 'My document is a TSV file'),
            (',', 'My document is a CSV file'),
        ],
        default='\t')
    submit = SubmitField('Analyze')
