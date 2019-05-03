import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from pymatgen import __version__ as pmg_version

from pymatgen import MPRester
from flask_caching import Cache

from crystal_toolkit.components.core import MPComponent
from crystal_toolkit.helpers.layouts import *
import crystal_toolkit.components as ctc

from synthesis_app.components.search import ChemsysSearchComponent

import os
import logging
from urllib import parse
from random import choice
from uuid import uuid4
from ast import literal_eval

# Author: Matthew McDermott (template by Matt Horton)
# Contact: mcdermott@lbl.gov

DEFAULT_CHEMSYS = ["Y-Mn-O"]
DEFAULT_MPIDS = ["YMn2O5"]

################################################################################
# region SET UP APP
################################################################################

meta_tags = [
    {
        "name": "description",
        "content": "Synthesis App is an interactive viewer for analyzing phase stability "
                   "using Materials Project data, Pymatgen, and Crystal Toolkit."
    }
]

app = dash.Dash(__name__, meta_tags=meta_tags, url_base_pathname="/genesis/", assets_url_path="/genesis",
                external_stylesheets=[BULMA_CSS['external_url'],
                                                                     FONT_AWESOME_CSS[
                                                                         'external_url']])  # create Dash app
app.title = "Synthesis App"
app.scripts.config.serve_locally = True
app.config["suppress_callback_exceptions"] = True
app.server.secret_key = str(uuid4())

server = app.server

DEBUG_MODE = literal_eval(os.environ.get("CRYSTAL_TOOLKIT_DEBUG_MODE", "False").title())

################################################################################
# region SET UP CACHE
################################################################################

try:
    cache = Cache(
        app.server,
        config={
            "CACHE_TYPE": "redis",
            "CACHE_REDIS_URL": os.environ.get("REDIS_URL", ""),
        },
    )
except Exception as exception:
    app.logger.error(
        f"Failed to connect to Redis cache, falling back to "
        f"file system cache: {exception}"
    )
    cache = Cache(app.server, config={"CACHE_TYPE": "filesystem", 'CACHE_DIR': 'cache-directory'})

# Enable for debug purposes:
if DEBUG_MODE:
    from crystal_toolkit.components.core import DummyCache

    cache = DummyCache()

# endregion

################################################################################
# region SET UP LOGGING
################################################################################

logger = logging.getLogger(app.title)

# endregion

################################################################################
# region INSTANTIATE CORE COMPONENTS
################################################################################

ctc.register_app(app)
ctc.register_cache(cache)

struct_component = ctc.StructureMoleculeComponent()
struct_component.default_title = "Structure Viewer"
search_component = ctc.SearchComponent()
chemsys_search_component = ChemsysSearchComponent()
literature_component = ctc.LiteratureComponent(origin_component=struct_component)
xrd_component = ctc.XRayDiffractionPanelComponent(origin_component=struct_component)
xas_component = ctc.XASPanelComponent(origin_component=search_component)
pd_component = ctc.PhaseDiagramComponent()
pd_component.attach_from(chemsys_search_component, this_store_name="chemsys-external")

panels = [
    xrd_component,
    xas_component,
    literature_component
]

body_layout = [
    Reveal(
        [pd_component.all_layouts["table"]],
        title="Phase Diagram Entries",
        id="pd-entries",
        open=True,
    ),
    html.Div([panel.panel_layout for panel in panels], id="panels"),
]

STRUCT_VIEWER_SOURCE = struct_component.id()

banner = html.Div(id="banner")

api_offline, api_error = True, "Unknown error connecting to Materials Project API."
try:
    with MPRester() as mpr:
        api_check = mpr._make_request("/api_check")
    if not api_check.get("api_key_valid", False):
        api_error = (
            "Materials Project API key not supplied or not valid, "
            "please set PMG_MAPI_KEY in your environment."
        )
    else:
        api_offline = False
except Exception as exception:
    api_error = str(exception)
if api_offline:
    banner = html.Div(
        [
            html.Br(),
            MessageContainer(
                [
                    MessageHeader("Error: Cannot connect to Materials Project"),
                    MessageBody(api_error),
                ],
                kind="danger",
            ),
        ],
        id="banner",
    )
# endregion

footer = ctc.Footer(
    html.Div(
        [
            dcc.Markdown(
                f"App created by [@mattmcdermott](https://github.com/mattmcdermott). "
                f"Special thanks to Matt Horton for his contributions to Crystal Toolkit.\n"
                f"Powered by [The Materials Project](https://materialsproject.org), "
                f"[pymatgen v{pmg_version}](http://pymatgen.org) and "
                f"[Dash by Plotly](https://plot.ly/products/dash/). "
            )
        ],
        className="content has-text-centered",
    ),
    style={"padding": "1rem 1rem 1rem", "background-color": "inherit"},
)

#################  App Layout ##################

################################################################################
# region  DEFINE MAIN LAYOUT
################################################################################

master_layout = Container(
    [
        dcc.Location(id="url", refresh=False),
        MPComponent.all_app_stores(),
        html.Br(),
        banner,
        Columns([
            H1("Synthesis App"),
            html.Br(),
            ], centered=True,
            ),
        Columns([
            chemsys_search_component.standard_layout
            ], centered=True),
        Section(
            [
                Columns(
                    [
                        Column(
                            [
                                html.Div(
                                    [
                                        H1("Phase Diagram"),
                                        pd_component.all_layouts["graph"],
                                    ],
                                ),

                                H4("Selected Structure"),
                                search_component.standard_layout,

                            ],
                            style={"max-width": "65vmin"},
                        ),

                        Column(
                            [
                                Column(
                                    [
                                        struct_component.title_layout,
                                        html.Div(
                                            style={'textAlign': 'center'}
                                        ),
                                    ],
                                ),

                                Box(
                                    struct_component.struct_layout,
                                    style={
                                        "width": "65vmin",
                                        "height": "65vmin",
                                        "min-width": "300px",
                                        "min-height": "300px",
                                        "overflow": "hidden",
                                        "padding": "0.25rem",
                                        "margin-bottom": "0.5rem",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            struct_component.legend_layout,
                                            style={"float": "left"},
                                        ),
                                        html.Div(
                                            [struct_component.screenshot_layout],
                                            style={"float": "right"},
                                        ),
                                    ],
                                    style={
                                        "width": "65vmin",
                                        "min-width": "300px",
                                        "margin-bottom": "40px",
                                    },
                                ),
                                html.Br(),
                                Reveal(
                                    [struct_component.options_layout],
                                    title="Display Options",
                                    id="display-options",
                                ),
                            ],
                            narrow=True,
                        ),
                    ],
                    desktop_only=False,
                    centered=False,
                ),
                Columns(
                    [
                        Column(
                            body_layout,
                        )
                    ]
                ),
            ]
        ),
        Section(footer),
    ]
)

app.layout = master_layout


# endregion

################################################################################
# region SET UP DASH CALLBACKS
################################################################################

@app.callback(Output(chemsys_search_component.id("input"), "value"), [Input("url", "href")])
def update_search_term_on_page_load(href):
    if href is None:
        raise PreventUpdate
    pathname = str(parse.urlparse(href).path).split("/")
    if len(pathname) <= 1:
        raise PreventUpdate
    elif not pathname[2]:
        return choice(DEFAULT_CHEMSYS)
    else:
        return pathname[2]


@app.callback(
    Output(chemsys_search_component.id("input"), "n_submit"),
    [Input(chemsys_search_component.id("input"), "value")],
    [State(chemsys_search_component.id("input"), "n_submit")],
)
def perform_search_on_page_load(search_term, n_submit):
    if n_submit is None:
        return 1
    else:
        raise PreventUpdate


@app.callback(Output("url", "pathname"), [Input(chemsys_search_component.id("input"), "value")])
def update_url_pathname_from_search_term(data):
    if data is None:
        raise PreventUpdate
    return data


@app.callback(
    [Output(search_component.id("input"),"value"),
     Output(search_component.id("input"), "n_submit")],
    [Input(pd_component.id("graph"), "clickData"),
     Input(chemsys_search_component.id("input"), "n_submit"),
     Input(chemsys_search_component.id("button"), "n_clicks")],
     [State(chemsys_search_component.id("input"), "value")]
)
def selected_structure(clickData, n_submit, n_clicks, input):
    if (clickData is None) and (input is None):
        raise PreventUpdate

    ctx = dash.callback_context
    triggered = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered == "ChemsysSearchComponent_input" or triggered == "ChemsysSearchComponent_button":
        return input, 1

    elif triggered == "PhaseDiagramComponent_graph":
        if 'hovertext' not in clickData['points'][0].keys():
            raise PreventUpdate
        uncleaned_formula = clickData['points'][0]['hovertext'].split(" ")[0]
        formula = uncleaned_formula.replace("<sub>","")
        formula_clean = formula.replace("</sub>", "")
        return formula_clean, 1


@app.callback(
    Output(STRUCT_VIEWER_SOURCE, "data"),
    [Input(search_component.id(), "data")],
)
def update_structure(search_mpid):

    if search_mpid is None:
        raise PreventUpdate

    with MPRester() as mpr:
        struct = mpr.get_structure_by_material_id(search_mpid["mpid"])

    return MPComponent.to_data(struct)

# endregion

if __name__ == "__main__":
    app.run_server(debug=DEBUG_MODE, port=8060)
