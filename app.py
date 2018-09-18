import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_table_experiments as dt
import plotly.graph_objs as go
import plotly.tools as tls
import pymatgen
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.analysis.phase_diagram import PDPlotter
from pymatgen import MPRester
import re
from synth_app.layout.plot_functions import gen_plotly_layout, gen_plotly_markers
from synth_app.layout.plot_layouts import xrd_layout, xas_layout

mpr = MPRester(api_key='') # establish API rester for retrieving Materials Project data

app = dash.Dash('synth-app') # create Dash app
app.title = "Synthesis App"

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
            dcc.Graph(id='phase-diagram', config={'displayModeBar':'hover','modeBarButtonsToRemove': ['sendDataToCloud','lasso2d','hoverCompareCartesian','hoverClosestCartesian','select2d'], 'displaylogo':False}),
            dcc.Checklist(id='pd-settings',
                options=[{'label': 'Show unstable', 'value': 'unstableTrue'}], values=[])
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
                columns=["mp-id", "Formula", "Formation Energy (eV)", "E Above Hull (eV)"],
                row_selectable=False,
                filterable=True,
                editable=False,
                sortable=True,
                selected_row_indices=[],
                id='compounds-table'
            )
        ], className='ten columns')
    ], className='row'),
    html.Div([
        html.P(),
        html.P('App created by ', style={'display':'inline'}),
        html.A("@mattmcdermott", href="http://perssongroup.lbl.gov/people.html", target="_blank"),
        html.P(),
        html.P('Phase diagram reference available ', style={'display':'inline'}),
        html.A("here", href="https://materialsproject.org/docs/phasediagram", target="_blank")
        ], className = 'twelve columns'),

    html.Div([], id='system-div')
], className='eleven columns offset-by-one')


#################  Dash Callbacks  ##################

# Create a new phase diagram using pymatgen's PDPlotter()

@app.callback(
    Output('phase-diagram', 'figure'),
    [Input('enter-button', 'n_clicks'), Input('pd-settings','values')],
    [State('element-input','value')]
)
def update_phasediagram(nclicks, pdSettings, system):
    system = system.split("-")
    dim = len(system)
    entries = mpr.get_entries_in_chemsys(system)
    pd = PhaseDiagram(entries)
    plotter = PDPlotter(pd)

    data = []
    if dim==2 or dim==3:
        for line in plotter.pd_plot_data[0]:
            data.append(go.Scatter(x=list(line[0]), y=list(line[1]), 
                                        mode="lines", 
                                        hoverinfo = 'none', 
                                        line={'color': 'rgba (0, 0, 0, 1)', 'dash': 'solid', 'width': 3.0}))
        if "unstableTrue" in pdSettings:
            index = 0
            x_list = []
            y_list = []
            text_list = []
            entrylist = list(plotter.pd_plot_data[2].keys())

            for unstable_entry in list(plotter.pd_plot_data[2].values()):
                x_list.append(unstable_entry[0])
                y_list.append(unstable_entry[1])
                mpid = entrylist[index].entry_id
                formula = entrylist[index].composition.reduced_formula
                energy = pd.get_form_energy_per_atom(list(plotter.pd_plot_data[2].keys())[index])
                text_list.append(formula + ' (' + mpid + ')' + '<br>' + str(energy) + ' eV')
                index += 1
            
            data.append(go.Scatter(x=x_list, y=y_list, 
                                        mode="markers", 
                                        hoverinfo = 'text', 
                                        hovertext=text_list, 
                                        marker = dict(color = '#ff0000',size = 8, symbol = 'x')))

    elif dim==4:
        for line in plotter.pd_plot_data[0]:
            data.append(go.Scatter3d(x=list(line[0]), y=list(line[1]), z=list(line[2]), 
                                        mode="lines", 
                                        hoverinfo = 'none', 
                                        line={'color': 'rgba (0, 0, 0, 1)', 'dash': 'solid', 'width': 3.0}))
        if "unstableTrue" in pdSettings:
            index = 0
            x_list = []
            y_list = []
            z_list = []
            text_list = []
            entrylist = list(plotter.pd_plot_data[2].keys())

            for unstable_entry in list(plotter.pd_plot_data[2].values()):
                x_list.append(unstable_entry[0])
                y_list.append(unstable_entry[1])
                z_list.append(unstable_entry[2])
                mpid = entrylist[index].entry_id
                formula = entrylist[index].composition.reduced_formula
                energy = pd.get_form_energy_per_atom(list(plotter.pd_plot_data[2].keys())[index])
                text_list.append(formula + ' (' + mpid + ')' + '<br>' + str(energy) + ' eV')
                index += 1
            
            data.append(go.Scatter3d(x=x_list, y=y_list, z=z_list,
                                        mode="markers", 
                                        hoverinfo = 'text', 
                                        hovertext=text_list, 
                                        marker = dict(color = '#ff0000',size = 4, symbol = 'x')))

    plotlyfig = go.Figure(data=data)
    plotlyfig.layout=gen_plotly_layout(plotlyfig, plotter, pd)
    plotlyfig.add_trace(gen_plotly_markers(plotlyfig, plotter, pd))

    return plotlyfig

@app.callback(
    Output('compounds-table','rows'),
    [Input('phase-diagram', 'figure')]
)
def update_table(figure):
    rows =[]

    for subentry in figure['data'][-1]['hovertext']:
        mpid = re.search('\(([^)]+)', subentry).group(1)
        mpid_info = mpr.get_entry_by_material_id(mpid)
        formula = subentry.split()[0]
        form_energy = round(mpid_info.energy_per_atom,3)
        e_above_hull = round(float(subentry.split()[1].split('>')[-1]),3)

        rows.append({'mp-id':mpid,'Formula':formula,'Formation Energy (eV)':form_energy,'E Above Hull (eV)':e_above_hull})

    return rows


# Create a new XRD plot using data from MAPI
@app.callback(
    Output('xrd-plot', 'figure'),
    [Input('phase-diagram', 'hoverData'), Input('xrd-selector','value')])
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
    width_array = []
    for point in data[0][rad_source]['pattern']:
        x.append(point[2])
        y.append(point[0])
        hkl.append(point[1])
        d_spacing.append(point[3])
        width_array.append(0.75)
    textbox = ["hkl: " + str(hkl[i]) + "<br>" + "d: " + str(d_spacing[i]) for i in range(0,len(hkl))]

    plotdata = [go.Bar(
        x=x,
        y=y,
        text=textbox,
        width=width_array
    )]
    xrd_plot = go.Figure(data = plotdata, layout= xrd_layout)
    xrd_plot.layout['title'] = "XRD: " + comp + "<i>" + " (Source: " + rad_source.strip("xrd.") + ")" +  "</i>"
    xrd_plot.layout['titlefont'] = dict(size = 20.0)
    return xrd_plot

# Create a new XAS plot using data from MAPI
@app.callback(
    Output('xas-plot', 'figure'),
    [Input('phase-diagram', 'hoverData'), Input('xas-selector','value')])
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
    [Input('phase-diagram', 'hoverData')])
def set_xas_options(hoverData):
    if hoverData is None:
        comp = "NaCl"
        mpid = "mp-22862"
    else:
        hovertext = hoverData['points'][0]['hovertext']
        comp = hovertext.split()[0]

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

