import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import dash_cytoscape as cyto
import networkx as nx
from functools import wraps

# not working properly currently
# Custom decorator to add descriptions to class attributes
def describe(description):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            return f(*args, **kwargs)
        wrapped.description = description
        return wrapped
    return decorator



# Data Structures for ComputeNode, MemoryNode, Operation, and PrimitiveOperation
class Operation:
    @describe("Type of the operation")
    def __init__(self, type, sizeX, sizeY):
        self.type = type
        self.sizeX = sizeX
        self.sizeY = sizeY

class ComputeNode:
    @describe("The name of the compute node")
    def __init__(self, name, dimOne, dimTwo, ops, outputDest):
        self.name = name
        self.dimOne = dimOne
        self.dimTwo = dimTwo
        self.ops = ops
        self.outputDest = outputDest

class MemoryNode:
    @describe("The name of the memory node")
    def __init__(self, name, numBanks, capacity, dataType, location, size, layout):
        self.name = name
        self.numBanks = numBanks
        self.capacity = capacity
        self.dataType = dataType
        self.location = location
        self.size = size
        self.layout = layout

class PrimitiveOperation:
    @describe("Type of the operation")
    def __init__(self, type, dest, src, size):
        self.type = type
        self.dest = dest
        self.src = src
        self.size = size

class SystemArchitecture:
    def __init__(self):
        self.computeNodes = []
        self.memoryNodes = []
        self.primitiveOperations = []

# Instances of ComputeNode, MemoryNode, and PrimitiveOperation
ops = Operation("MAC", 3, 3)
compute_node = ComputeNode("SYSTOLIC", [1, 2, 3], [4, 5, 6], ops, "OUTPUT")

memory_node = MemoryNode("DRAM", 16, 1024, "int32", "DEST", 4096, "SYSTOLIC")
primitive_op = PrimitiveOperation("LD", "OUT", "BUF", 128)

# Create a NetworkX graph
G = nx.DiGraph()  # Use a directed graph

# Add nodes with extended attributes, ensuring only serializable values
def serialize_node_data(node):
    data = vars(node)
    serialized_data = {}
    for key, value in data.items():
        if isinstance(value, (str, int, float, list)):
            serialized_data[key] = value
        elif isinstance(value, Operation):
            serialized_data[key] = vars(value)  # Serialize the Operation object to a dictionary
        else:
            serialized_data[key] = str(value)
    return serialized_data

G.add_node('DRAM', label='DRAM\n---\nMemory Node', color='#3498db', **serialize_node_data(memory_node))
G.add_node('INPUT', label='INPUT\n---\nsome_property: value', color='#2ecc71', some_property='value')
G.add_node('WEIGHT', label='WEIGHT\n---\nMemory Node', color='#e74c3c', **serialize_node_data(memory_node))
G.add_node('SYSTOLIC', label='SYSTOLIC\n---\nCompute Node', color='#9b59b6', **serialize_node_data(compute_node))
G.add_node('OUTPUT', label='OUTPUT\n---\nsome_property: value', color='#f1c40f', some_property='value')
G.add_node('BIAS', label='BIAS\n---\nMemory Node', color='#34495e', **serialize_node_data(memory_node))

# Add edges
G.add_edge('DRAM', 'INPUT')
G.add_edge('DRAM', 'WEIGHT')
G.add_edge('DRAM', 'BIAS')
G.add_edge('INPUT', 'SYSTOLIC')
G.add_edge('WEIGHT', 'SYSTOLIC')
G.add_edge('SYSTOLIC', 'OUTPUT')
G.add_edge('OUTPUT', 'DRAM')
G.add_edge('BIAS', 'SYSTOLIC')

# Convert NetworkX graph to Dash Cytoscape elements
def nx_to_cytoscape(G):
    elements = []
    positions = {
        'DRAM': {'x': 100, 'y': 400},
        'INPUT': {'x': 200, 'y': 300},
        'WEIGHT': {'x': 300, 'y': 200},
        'SYSTOLIC': {'x': 400, 'y': 300},
        'OUTPUT': {'x': 500, 'y': 400},
        'BIAS': {'x': 600, 'y': 300}
    }
    for node, data in G.nodes(data=True):
        node_data = {key: value for key, value in data.items() if key not in ['position']}
        elements.append({
            'data': {'id': node, 'label': data.get('label', ''), 'color': data.get('color', ''), **node_data},
            'position': positions.get(node, {'x': 0, 'y': 0})  # Use predefined positions or default to (0, 0)
        })
    
    for edge in G.edges():
        edge_data = {'source': edge[0], 'target': edge[1]}
        elements.append({
            'data': edge_data
        })
    
    return elements

elements = nx_to_cytoscape(G)

# Create Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# style sheet for the digrams 
app.layout = html.Div([
    dcc.Store(id="node-properties-store", storage_type="memory"),
    html.Div([
        html.H1("Compute Graph", style={'color': 'white', 'padding': '20px'})
    ], style={'background-color': '#2c3e50'}),
    dbc.Container([
        dbc.Row([
            dbc.Col([
                cyto.Cytoscape(
                    id='cytoscape-graph',
                    style={'height': '600px', 'width': '100%'},
                    layout={'name': 'preset'},
                    stylesheet=[
                        {
                            'selector': 'node',
                            'style': {
                                'label': 'data(label)',
                                'background-color': 'data(color)',
                                'shape': 'round-rectangle',
                                'width': '150px',
                                'height': '100px',
                                'text-valign': 'center',
                                'text-halign': 'center',
                                'font-size': '12px',
                                'color': '#000000',
                                'background-opacity': 0.8,
                                'border-width': 2,
                                'border-color': '#2c3e50',
                                'padding': '10px',
                                'text-wrap': 'wrap',
                                'text-max-width': '130px'
                            }
                        },
                        {
                            'selector': 'edge',
                            'style': {
                                'width': 2,
                                'line-color': '#888',
                                'curve-style': 'bezier',
                                'target-arrow-shape': 'triangle',
                                'target-arrow-color': '#888',
                                'arrow-scale': 1.5
                            }
                        }
                    ],
                    elements=elements,
                    mouseoverNodeData=None
                )
            ], width=8),
            dbc.Col([
                html.H4("Node Properties", className="text-center"),
                html.Hr(),
                html.Div(id="node-properties", className="mt-4")
            ], width=4)
        ])
    ], fluid=True, style={'padding': '20px'})
])

# Extract descriptions using reflection
def get_property_descriptions(cls):
    descriptions = {}
    for name, attr in cls.__dict__.items():
        if hasattr(attr, 'description'):
            descriptions[name] = attr.description
    return descriptions

PROPERTY_DESCRIPTIONS = {
    'ComputeNode': get_property_descriptions(ComputeNode),
    'MemoryNode': get_property_descriptions(MemoryNode),
    'PrimitiveOperation': get_property_descriptions(PrimitiveOperation)
}

# handles node properties with tooltips
def handle_node_properties(node_data):
    node_type = node_data.get('label', '').split('\n')[0]
    class_name = node_data.get('__class__', '')
    descriptions = getattr(globals().get(class_name).__init__, 'description', {})
    
    properties = []
    for key, value in node_data.items():
        if key not in ['id', 'label', 'color', '__class__']:
            prop_id = f"{node_data['id']}-{key}-tooltip"
            description = descriptions.get(key, "No description available")
            
            if isinstance(value, dict):
                nested_properties = []
                for nested_key, nested_value in value.items():
                    nested_prop_id = f"{prop_id}-{nested_key}"
                    nested_description = descriptions.get(key, {}).get(nested_key, "No description available")
                    nested_properties.append(
                        html.Div([
                            html.P(f"{nested_key}: {nested_value}", id=nested_prop_id, style={"text-decoration": "", "cursor": "pointer", "margin-left": "10px"}),
                            dbc.Tooltip(nested_description, target=nested_prop_id)
                        ])
                    )
                properties.append(html.Div([html.P(f"{key}: {description}"), html.Div(nested_properties, style={"margin-left": "20px"})]))
            else:
                properties.append(
                    html.Div([
                        html.P(f"{key}: {value}", id=prop_id, style={"text-decoration": "", "cursor": "pointer"}),
                        dbc.Tooltip(description, target=prop_id)
                    ])
                )
    
    return properties


@app.callback(
    Output("node-properties-store", "data"),
    [Input("cytoscape-graph", "tapNodeData")]
)
def update_node_properties_store(data):
    if data:
        data['__class__'] = data.get('label', '').split('\n')[0]
        return data
    return {}

@app.callback(
    Output("node-properties", "children"),
    [Input("node-properties-store", "data")]
)

# Display node properties with tooltips
def display_node_properties(data):
    if data:
        properties = handle_node_properties(data)
        return html.Div(properties, className="card p-3")
    return html.Div("Click a node to see its properties", className="card p-3")

if __name__ == "__main__":
    app.run_server(debug=True)
