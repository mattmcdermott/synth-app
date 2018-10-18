import plotly.graph_objs as go
from synth_app.layout.plot_layouts import layout_2d, layout_3d, layout_4d

# Plotly layout functions

def gen_plotly_layout(plot, plotter, pd):

    dim = pd.dim

    if (dim == 2):
        annotations_list = []

        for entry in plotter.pd_plot_data[1]:
            x, y = entry[0], entry[1]

            formula = list(plotter.pd_plot_data[1][entry].composition.reduced_formula)
            text = []
            for char in formula:
                if char.isdigit():
                    text.append("<sub>" + char + "</sub>")
                else:
                    text.append(char)
            clean_formula = ""
            clean_formula = clean_formula.join(text)

            new_annotation = {'align': 'center',
                                    'font': {'color': '#000000', 'size': 20.0},
                                    'opacity': 1,
                                    'showarrow': False,
                                    'text': clean_formula + "  ",
                                    'x': x,
                                    'xanchor': 'right',
                                    'yanchor': 'auto',
                                    'xref': 'x',
                                    'y': y,
                                    'yref': 'y'}

            annotations_list.append(new_annotation)

            layout = layout_2d
            layout['annotations'] = annotations_list
        return layout

    elif (dim == 3):
        annotations_list = []

        for entry in plotter.pd_plot_data[1]:
            x, y = entry[0], entry[1]

            formula = list(plotter.pd_plot_data[1][entry].composition.reduced_formula)
            text = []
            for char in formula:
                if char.isdigit():
                    text.append("<sub>" + char + "</sub>")
                else:
                    text.append(char)
            clean_formula = ""
            clean_formula = clean_formula.join(text)

            new_annotation = {'align': 'center',
                                    'font': {'color': '#000000', 'size': 18.0},
                                    'opacity': 1,
                                    'showarrow': False,
                                    'text': clean_formula + "  ",
                                    'x': x,
                                    'xanchor': 'right',
                                    'yanchor': 'top',
                                    'xref': 'x',
                                    'y': y,
                                    'yref': 'y'}

            annotations_list.append(new_annotation)

            layout = layout_3d
            layout['annotations'] = annotations_list
        return layout

    elif (dim == 4):
        annotations_list = []

        for entry in plotter.pd_plot_data[1]:
            x, y, z = entry[0], entry[1], entry[2]

            formula = list(plotter.pd_plot_data[1][entry].composition.reduced_formula)
            text = []
            for char in formula:
                if char.isdigit():
                    text.append("<sub>" + char + "</sub>")
                else:
                    text.append(char)
            clean_formula = ""
            clean_formula = clean_formula.join(text)

            new_annotation = {'align': 'center',
                                    'font': {'color': '#000000', 'size': 18.0},
                                    'opacity': 1,
                                    'showarrow': False,
                                    'text': clean_formula,
                                    'x': x,
                                    'y': y,
                                    'z': z,
                                    'xshift':25,
                                    'yshift':10}

            annotations_list.append(new_annotation)

            layout = layout_4d
            layout['scene'] = dict(annotations=annotations_list, 
                                xaxis=dict(
                                    title=None,
                                    visible=False,
                                    autorange=True,
                                    showgrid=False,
                                    zeroline=False,
                                    showline=False,
                                    ticks='',
                                    showaxeslabels=False,
                                    showticklabels=False,
                                    showspikes=False,                                  
                                    ),
                                yaxis=dict(
                                    title=None,
                                    visible=False,
                                    autorange=True,
                                    showgrid=False,
                                    zeroline=False,
                                    showline=False,
                                    showaxeslabels=False,                                    
                                    ticks='',
                                    showticklabels=False,
                                    showspikes=False,                                    
                                    ),
                                zaxis=dict(
                                    title=None,
                                    visible=False,
                                    autorange=True,
                                    showgrid=False,
                                    zeroline=False,
                                    showline=False,
                                    showaxeslabels=False,                                    
                                    ticks='',
                                    showticklabels=False,
                                    showspikes=False))
        return layout
    
    else:
        raise ValueError("Dimension of phase diagram must be 2, 3, or 4")

def gen_plotly_markers(plot, plotter, pd):
    x_list = []
    y_list = []
    z_list = []
    text = []
    dim = pd.dim

    for entry in plotter.pd_plot_data[1]:
        energy = round(pd.get_form_energy_per_atom(plotter.pd_plot_data[1][entry]),3)
        mpid = plotter.pd_plot_data[1][entry].entry_id
        formula = plotter.pd_plot_data[1][entry].composition.reduced_formula
        s = []
        for char in formula:
            if char.isdigit():
                s.append("<sub>" + char + "</sub>")
            else:
                s.append(char)
        clean_formula = ""
        clean_formula = clean_formula.join(s)

        x_list.append(entry[0])
        y_list.append(entry[1])
        if dim==4:
            z_list.append(entry[2])
        text.append(clean_formula + ' (' + mpid + ')' + '<br>' + str(energy) + ' eV')

        if dim==2 or dim==3:
            markerPlot = go.Scatter(
                x = x_list,
                y = y_list,
                mode = 'markers',
                name = 'Stable',
                marker = dict(
                    color = '#0562AB',
                    size = 11
                    ),
                hoverinfo = 'text',
                hoverlabel = dict(font = dict(size = 14)),
                showlegend=True,
                hovertext = text)
        if dim==4:
             markerPlot = go.Scatter3d(
                x = x_list,
                y = y_list,
                z = z_list,
                mode = 'markers',
                name = 'Stable',
                marker = dict(
                    color = '#0562AB',
                    size = 8
                    ),
                hoverinfo = 'text',
                hoverlabel = dict(font = dict(size = 14)),
                hovertext = text)
    
    return markerPlot