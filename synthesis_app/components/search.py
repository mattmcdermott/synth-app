import os

import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from crystal_toolkit.components.core import MPComponent, unicodeify_spacegroup
from crystal_toolkit.helpers.layouts import *
from crystal_toolkit import __file__ as module_path

# Author: Matthew McDermott (based on SearchComponent by Matt Horton)
# Contact: mcdermott@lbl.gov

class ChemsysSearchComponent(MPComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _make_search_box(self, search_term=None):

        search_field = dcc.Input(
            id=self.id("input"),
            className="input",
            type="text",
            value=search_term,
            placeholder="e.g. Y-Mn-O",
            style={"min-width": "300px"}
        )
        search_button = Button(
            [Icon(kind="search"), html.Span(), "Search"],
            kind="primary",
            id=self.id("button"),
        )
        search = Field(
            [Control(search_field), Control(search_button)],
            addons=True,
            style={"margin-bottom": "0"}
        )

        return html.Div([html.Label("Search by Chemical System:", className="mpc-label"), search],
                        )

    def chemsys_from_search(self, search_term):
        return search_term.split("-")  # create system from user input

    @property
    def all_layouts(self):

        search = html.Div(self._make_search_box(), id=self.id("search_container"))

        return {"search": search}

    @property
    def standard_layout(self):
        return html.Div([self.all_layouts["search"]])

    def _generate_callbacks(self, app, cache):

        @app.callback(
            Output(self.id(), "data"),
            [
                Input(self.id("input"), "n_submit"),
                Input(self.id("button"), "n_clicks"),
            ],
            [State(self.id("input"), "value")]
        )
        def return_chemsys(n_submit, n_clicks, search_term):
            return self.chemsys_from_search(search_term)


