import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_table_experiments as dt
import plotly.graph_objs as go
import pymatgen
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.analysis.phase_diagram import PDPlotter
from pymatgen import MPRester
from flask_caching import Cache
import re
from synth_app.layout.plot_functions import gen_plotly_layout, gen_plotly_markers
from synth_app.layout.plot_layouts import xrd_layout, xas_layout

# Author: Matthew McDermott
# Date: October 18, 2018
# Contact: mcdermott@lbl.gov

mpr = MPRester() # establish API rester for retrieving Materials Project data

app = dash.Dash('synth-app') # create Dash app
app.title = "Synthesis App"

# configure cache using flask_caching
cache = Cache(app.server, config={
     'CACHE_TYPE': 'filesystem',
     'CACHE_DIR': 'cache-directory',
     'CACHE_THRESHOLD': 1000
})
TIMEOUT = 0

#################  App Layout ##################

app.layout = html.Div([
    html.Div([
        html.H1('Synthesis App',
            style={
                'textAlign': 'center'},
            className = 'twelve columns'),
        html.A(
            html.Img(src="https://materialsproject.org/static/images/Logo/Mp-logo-v5.ad467cf84f15.png",
                    style={
                        'position': 'absolute',
                        'height': '75px',
                        'width': 'auto',
                        'top': '15px',
                        'right':'30px'}), href='https://materialsproject.org', target="_blank")
        ], className ='row'),

    html.Div([
        html.H4('Enter between 2 and 4 different elements/formulas separated by dashes:'),
        dcc.Input(
            id = 'element-input',
            placeholder='Ex. Na-Cl',
            type='text',
            value='Na-Cl',
            style={'width':'200px', 'fontSize':'16'}),
        html.Button('Enter',
            id='enter-button',
            n_clicks=0),
        html.P('(Example: Na-Cl)', style={'display':'inline','margin-left':'15', 'color': 'DarkGray'}),
        ], className = 'row'),

    html.Div([
        html.Div([
            html.H4('Phase Diagram'),
            dcc.Graph(id='phase-diagram', config={'displayModeBar':False,
                                                  'displaylogo':False}),
            ],className='five columns'
            ),
        html.Div([
            html.Div([
                html.Div([
                    html.H5('X-Ray Diffraction Plot'),
                    dcc.Graph(id='xrd-plot',config={'displayModeBar': False})
                    ],className='ten columns'),
                html.Div([
                    html.P('Radiation Source:'),
                    dcc.RadioItems(
                        id='xrd-selector',
                        options=[
                            {'label': 'Cu', 'value': 'xrd.Cu'},
                            {'label': 'Ag', 'value': 'xrd.Ag'},
                            {'label': 'Mo', 'value': 'xrd.Mo'},
                            {'label': 'Fe', 'value': 'xrd.Fe'},
                        ],
                        value='xrd.Cu',
                        ),
                    ],className='two columns',style={'margin-top':'50','margin-left':'0'})
                ],className='row'),
            html.Div([
                html.Div([
                    html.H5('X-Ray Absorption Spectra'),
                    dcc.Graph(id='xas-plot', config={'displayModeBar': False}),
                    ],className='ten columns'),
                html.Div([
                    html.P('Element:'),
                    dcc.RadioItems(
                        id='xas-selector',
                        options=[
                            {'label': 'Na', 'value': 'Na'},
                            {'label': 'Cl', 'value': 'Cl'},
                        ],
                        value='Na',
                        ),
                    ],className='two columns',style={'margin-top':'50','margin-left':'0'})
                ], className='row')
            ], className='seven columns'),
        ], className='row', style={'margin-top':'15'}),

    html.Div([
        html.H4("Compounds"),
        html.Div([
            dt.DataTable(
                rows=[],
                columns=["mp-id", "Formula", "Form. Energy (eV/atom)", "E Above Hull (eV/atom)", "Stable?"],
                row_selectable=False,
                filterable=True,
                editable=False,
                sortable=True,
                selected_row_indices=[],
                id='compounds-table'
            )
        ], className='ten columns')
    ], className='row', style={'margin-bottom':'35'}),
    html.Div([
        html.Div([
            html.P('App created by ', style={'display': 'inline'}),
            html.A("@mattmcdermott", href="http://perssongroup.lbl.gov/people.html", target="_blank"),
            html.P(),
            html.P('Phase diagram reference available ', style={'display': 'inline'}),
            html.A("here", href="https://materialsproject.org/docs/phasediagram", target="_blank")
        ], className = 'ten columns'),
        html.Div([
            html.Img(
                src="https://lh4.googleusercontent.com/Ov0Em9GoHbUS6i-cyknyzUcgLY5IsOX9-vvEYuZewiqBNOcWbirttB7KtSFG10tR-XHZYxKreQ=w16383",
                style={
                    'float': 'right',
                    'height': '50px',
                    'width': 'auto'}
            )
            ], className = 'two columns')
        ], className = 'row', style={'margin-bottom':'20'}),
], className='eleven columns offset-by-one')


#################  Dash Callbacks  ##################

# Create a new phase diagram using pymatgen's PDPlotter()
@app.callback(
    Output('phase-diagram', 'figure'),
    [Input('enter-button', 'n_clicks')],
    [State('element-input','value')]
)
def update_phasediagram(nclicks, system):
    system = system.split("-") # create system from user input
    dim = len(system)  # find dimension of system
    entries = mpr.get_entries_in_chemsys(system) # use MPRester to acquire all entries in chem system
    pd = PhaseDiagram(entries) # create phase diagram using pymatgen
    plotter = PDPlotter(pd) # create plotter object using pymatgen

    data = [] # initialize plot data list
    if dim==2:
        for line in plotter.pd_plot_data[0]:
            data.append(go.Scatter(x=list(line[0]), y=list(line[1]), # create all phase diagram lines
                                        mode="lines", 
                                        hoverinfo = 'none',
                                        line={'color': 'rgba (0, 0, 0, 1)', 'dash': 'solid', 'width': 3.0},
                                        showlegend = False))
        x_list = []
        y_list = []
        text_list = []
        unstable_xy_list = list(plotter.pd_plot_data[2].values())
        unstable_entry_list = list(plotter.pd_plot_data[2].keys())

        for unstable_xy, unstable_entry in zip(unstable_xy_list,unstable_entry_list):
            x_list.append(unstable_xy[0])
            y_list.append(unstable_xy[1])
            mpid = unstable_entry.entry_id
            formula = list(unstable_entry.composition.reduced_formula)
            e_above_hull = round(pd.get_e_above_hull(unstable_entry),3)

            #add formula subscripts
            s = []
            for char in formula:
                if char.isdigit():
                    s.append("<sub>" + char + "</sub>")
                else:
                    s.append(char)
            clean_formula = ""
            clean_formula = clean_formula.join(s)

            energy = round(pd.get_form_energy_per_atom(unstable_entry),3)
            text_list.append(clean_formula + ' (' + mpid + ')' + '<br>'
                             + str(energy) + ' eV' + ' (' + str(e_above_hull) + ' eV' + ')')

        data.append(go.Scatter(x=x_list, y=y_list,
                                    mode="markers",
                                    hoverinfo = 'text',
                                    hovertext=text_list,
                                    visible = 'legendonly',
                                    name = 'Unstable',
                                    marker = dict(color = '#ff0000',size = 12, symbol = 'x')))

    elif dim==3:
        for line in plotter.pd_plot_data[0]:
            data.append(go.Scatter(x=list(line[0]), y=list(line[1]), # create all phase diagram lines
                                        mode="lines",
                                        hoverinfo = 'none',
                                        line={'color': 'rgba (0, 0, 0, 1)', 'dash': 'solid', 'width': 3.0},
                                        showlegend = False))
        x_list = []
        y_list = []
        xy_list = []
        text_list = []
        unstable_xy_list = list(plotter.pd_plot_data[2].values())
        unstable_entry_list = list(plotter.pd_plot_data[2].keys())

        for unstable_xy, unstable_entry in zip(unstable_xy_list, unstable_entry_list):
            mpid = unstable_entry.entry_id
            formula = unstable_entry.composition.reduced_formula
            energy = round(pd.get_form_energy_per_atom(unstable_entry), 3)
            e_above_hull = round(pd.get_e_above_hull(unstable_entry), 3)

            s = []
            for char in formula:
                if char.isdigit():
                    s.append("<sub>" + char + "</sub>")
                else:
                    s.append(char)
            clean_formula = ""
            clean_formula = clean_formula.join(s)

            if unstable_xy not in xy_list:
                x_list.append(unstable_xy[0])
                y_list.append(unstable_xy[1])
                xy_list.append(unstable_xy)
                text_list.append(clean_formula + ' (' + mpid + ')' + '<br>'
                                 + str(energy) + ' eV' + ' (' + str(e_above_hull) + ' eV' + ')')
            else:
                index = xy_list.index(unstable_xy)
                text_list[index] += '<br>'+ clean_formula + ' (' + mpid + ')' + '<br>' + str(energy) + ' eV' + ' (' + str(
                                    e_above_hull) + ' eV' + ')'

        data.append(go.Scatter(x=x_list, y=y_list,
                                    mode="markers",
                                    hoverinfo = 'text',
                                    hovertext=text_list,
                                    visible = 'legendonly',
                                    name = 'Unstable',
                                    marker = dict(color = '#ff0000',size = 12, symbol = 'x')))
    elif dim==4:
        for line in plotter.pd_plot_data[0]:
            data.append(go.Scatter3d(x=list(line[0]), y=list(line[1]), z=list(line[2]), # create all phase diagram lines
                                        mode="lines",
                                        hoverinfo = 'none',
                                        line={'color': 'rgba (0, 0, 0, 1)', 'dash': 'solid', 'width': 3.0},
                                        showlegend = False))
        x_list = []
        y_list = []
        z_list = []
        xyz_list = []
        text_list = []
        unstable_xyz_list = list(plotter.pd_plot_data[2].values())
        unstable_entry_list = list(plotter.pd_plot_data[2].keys())

        for unstable_xyz, unstable_entry in zip(unstable_xyz_list, unstable_entry_list):
            mpid = unstable_entry.entry_id
            formula = unstable_entry.composition.reduced_formula
            energy = round(pd.get_form_energy_per_atom(unstable_entry), 3)
            e_above_hull = round(pd.get_e_above_hull(unstable_entry), 3)

            s = []
            for char in formula:
                if char.isdigit():
                    s.append("<sub>" + char + "</sub>")
                else:
                    s.append(char)
            clean_formula = ""
            clean_formula = clean_formula.join(s)

            if unstable_xyz not in xyz_list:
                x_list.append(unstable_xyz[0])
                y_list.append(unstable_xyz[1])
                z_list.append(unstable_xyz[2])
                xyz_list.append(unstable_xyz)
                text_list.append(clean_formula + ' (' + mpid + ')' + '<br>'
                                 + str(energy) + ' eV' + ' (' + str(e_above_hull) + ' eV' + ')')
            else:
                index = xyz_list.index(unstable_xyz)
                text_list[index] += '<br>'+ clean_formula + ' (' + mpid + ')' + '<br>' + str(energy) + ' eV' + ' (' + str(
                                    e_above_hull) + ' eV' + ')'

        data.append(go.Scatter3d(x=x_list, y=y_list, z=z_list,
                                    mode="markers",
                                    hoverinfo = 'text',
                                    hovertext=text_list,
                                    visible = 'legendonly',
                                    name = 'Unstable',
                                    marker = dict(color = '#ff0000',size = 4, symbol = 'x')))

    plotlyfig = go.Figure(data=data)
    plotlyfig.layout=gen_plotly_layout(plotlyfig, plotter, pd)
    plotlyfig.add_trace(gen_plotly_markers(plotlyfig, plotter, pd))
    return plotlyfig

# Update compounds table with all compounds
@app.callback(
    Output('compounds-table','rows'),
    [Input('phase-diagram', 'figure')])
@cache.memoize(timeout=TIMEOUT)
def update_table(figure):
    rows =[]

    for subentry in figure['data'][-1]['hovertext']:
        mpid = re.search('\(([^)]+)', subentry).group(1)
        formula = subentry.split()[0].replace("<sub>","").replace("</sub>","")
        energy = float(subentry.split()[1].split('>')[-1])
        e_above_hull = 0.000
        rows.append({'mp-id':mpid,'Formula':formula,'Form. Energy (eV/atom)':energy,'E Above Hull (eV/atom)':e_above_hull,'Stable?': 'Yes'})

    for unstable_subentry in figure['data'][-2]['hovertext']:
        mpid = re.search('\(([^)]+)', unstable_subentry).group(1)
        formula = unstable_subentry.split()[0].replace("<sub>","").replace("</sub>","")
        energy = float(unstable_subentry.split()[1].split('>')[-1])
        e_above_hull = float(unstable_subentry.split()[3].split('(')[1])
        rows.append({'mp-id':mpid,'Formula':formula,'Form. Energy (eV/atom)':energy,'E Above Hull (eV/atom)':e_above_hull,'Stable?': 'No'})

    return rows

# Create a new XRD plot using data from MAPI
@app.callback(
    Output('xrd-plot', 'figure'),
    [Input('phase-diagram', 'clickData'), Input('xrd-selector','value')])
@cache.memoize(timeout=TIMEOUT)
def update_xrd_plot(hoverData, rad_source):
    if hoverData is None:
        comp = "NaCl"
        mpid = "mp-22862"
    else:
        hovertext = hoverData['points'][0]['hovertext']
        comp = hovertext.split()[0]
        mpid = re.search('\(([^)]+)', hovertext).group(1)

    data = mpr.query(criteria={"task_id": mpid}, properties=[rad_source])
    x = []
    y = []
    hkl = []
    d_spacing = []
    #width_array = []
    for point in data[0][rad_source]['pattern']:
        x.append(point[2])
        y.append(point[0])
        hkl.append(point[1])
        d_spacing.append(point[3])
        #width_array.append(0.5)
    textbox = ["hkl: " + str(hkl[i]) + "<br>" + "d: " + str(d_spacing[i]) for i in range(0,len(hkl))]

    plotdata = [go.Bar(
        x=x,
        y=y,
        text=textbox,
        #width=width_array
    )]

    xrd_plot = go.Figure(data = plotdata, layout= xrd_layout)
    xrd_plot.layout['title'] = "XRD: " + comp + "<i>" + " (Source: " + rad_source.strip("xrd.") + ")" +  "</i>"
    xrd_plot.layout['titlefont'] = dict(size = 20.0)
    return xrd_plot

# Create a new XAS plot using data from MAPI
@app.callback(
    Output('xas-plot', 'figure'),
    [Input('phase-diagram', 'clickData'), Input('xas-selector','value')])
@cache.memoize(timeout=TIMEOUT)
def update_xas_plot(hoverData,elem):
    if hoverData is None:
        comp = "NaCl"
        mpid = "mp-22862"
    else:
        hovertext = hoverData['points'][0]['hovertext']
        comp = hovertext.split()[0]
        mpid = re.search('\(([^)]+)', hovertext).group(1)

    url_path = '/materials/' + mpid + '/xas/' + elem
    data = mpr._make_request(url_path)
    x = []
    y = []
    if len(data) != 0:
        x = data[0]['spectrum'].x
        y = data[0]['spectrum'].y
        plotdata = [go.Scatter(x=x,y=y)]
        xas_plot = go.Figure(data= plotdata, layout = xas_layout)
        xas_plot.layout['title'] = "XAS: " + comp + "<i>" + " (" + elem + ")" + "</i>"
        xas_plot.layout['titlefont'] = dict(size = 20.0)
        return xas_plot
    else:
        return go.Figure(layout=xas_layout)

# Process hover data from phase diagram to determine XAS element selection options
@app.callback(
    Output('xas-selector', 'options'),
    [Input('phase-diagram', 'clickData')])
def set_xas_options(hoverData):
    if hoverData is None:
        comp = "NaCl"
    else:
        hovertext = hoverData['points'][0]['hovertext']
        comp = hovertext.split()[0].replace("<sub>","").replace("</sub>","")

    comp_obj = pymatgen.Composition(comp)
    elem_options = [str(comp_obj.elements[i]) for i in range(0,len(comp_obj))]
    return [{'label': i, 'value': i} for i in elem_options]

# Select first absorbing element as default in XAS plot
@app.callback(
    Output('xas-selector', 'value'),
    [Input('xas-selector', 'options')])
def set_xas_value(options):
    return options[0]['value']

external_css = ["https://codepen.io/chriddyp/pen/bWLwgP.css",
                "https://codepen.io/mattmcd1/pen/KxXxNv.css"]

for css in external_css:
    app.css.append_css({"external_url": css})

if __name__ == '__main__':
    app.run_server(debug=True)
