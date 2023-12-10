import os
import dash
import json
import markdown2
import pandas as pd

from dash import html, dcc
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, ALL, State
from dash_dangerously_set_inner_html import DangerouslySetInnerHTML

filename = "ChatGPT on 07 12 2023/conversations.json"
file_path = os.path.realpath(__file__)
directory = os.path.dirname(file_path)
filename = os.path.join(directory, filename)
data = pd.read_json(filename)

app = dash.Dash(__name__, suppress_callback_exceptions=False)

app.layout = html.Div([
    # Removed the search input component
    html.Div(id='title-list', style={
        'overflowY': 'scroll',
        'height': '90vh',
        'flex': '0 0 300px',
        'borderRight': 'thin lightgrey solid'
    }),
    html.Div(id='right-pane', style={
        'overflowY': 'scroll',
        'height': '90vh',
        'flex': '1',
    }),
    html.Div(id='trigger-mathjax', style={'display': 'none'}),
], style={'display': 'flex', 'margin': '20px', 'gap': '20px'})

def process_system_assistant_content(content):
    # Correctly escape backslashes for LaTeX processing
    content = content.replace('\\\\', '\\')

    # Now apply Markdown formatting
    return format_markdown(content)

def format_markdown(text):
    # Split the text by lines
    lines = text.split('\n')
    formatted_lines = []
    inside_code_block = False

    for line in lines:
        if line.strip() == '```python':
            inside_code_block = True
            formatted_lines.append(line)
        elif line.strip() == '```' and inside_code_block:
            inside_code_block = False
            formatted_lines.append(line)
        elif inside_code_block:
            formatted_lines.append(line)
        else:
            # Process Markdown formatting without altering LaTeX expressions
            line = line.replace('`', r'\`')  # Escape single backticks
            formatted_lines.append(line)

    return '\n'.join(formatted_lines)


def process_user_content(content):
    content = content.replace('\n', '<br>')
    content = content.replace('\\', '\\\\')
    content = content.replace('$$', '<span class="latex">').replace('$$', '</span>')  
    return content


def parse_conversation(data, node_id):
    if node_id not in data:
        return ""

    node = data[node_id]
    message_data = node.get('message')
    
    if message_data is None:
        return ""
    
    # Determine the author's role
    author_role = message_data.get('author', {}).get('role', 'unknown')
    
    # Based on the role, choose a CSS class
    css_class = ""
    if author_role == "user":
        css_class = "user"
    elif author_role == "assistant":
        css_class = "assistant"
    elif author_role == "system":
        css_class = "system"

    message_parts = message_data.get('content', {}).get('parts', [])
    formatted_message_parts = []

    for part in message_parts:
        if isinstance(part, dict):
            text = part.get('text', '')
            if author_role == 'user':
                text = process_user_content(text)
            else:
                text = process_system_assistant_content(text)
            formatted_text = f'<div class="{css_class}">{text}</div>'
            formatted_message_parts.append(formatted_text)
        elif isinstance(part, str):
            if author_role == 'user':
                part = process_user_content(part)
            else:
                part = process_system_assistant_content(part)
            formatted_text = f'<div class="{css_class}">{part}</div>'
            formatted_message_parts.append(formatted_text)
        else:
            formatted_message_parts.append('[Unsupported data format]')

    formatted_message = "\n".join(formatted_message_parts)
    children_messages = [parse_conversation(data, child_id) for child_id in node.get('children', [])]
    full_conversation_content = formatted_message + "\n".join(children_messages)

    return full_conversation_content


@app.callback(
    Output('right-pane', 'children'),
    [Input({'type': 'title-button', 'index': ALL}, 'n_clicks')],
    [State({'type': 'title-button', 'index': ALL}, 'id')]
)
def display_content(n_clicks, ids):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "Select a conversation from the list on the left."
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        index = json.loads(button_id)['index']
        content_data = data.iloc[index]['mapping']
        
        first_node_id = next(iter(content_data))
        conversation_content = parse_conversation(content_data, first_node_id)
       
        html_content = markdown2.markdown(conversation_content, extras=["fenced-code-blocks", "code-friendly", "cuddled-lists", "mathjax"])

        return DangerouslySetInnerHTML(html_content)


""" @app.callback(
    Output('right-pane', 'children'),
    [Input({'type': 'title-button', 'index': ALL}, 'n_clicks')]
)
def display_conversation(n_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_index = json.loads(button_id)['index']

    # Retrieve the conversation based on the button index
    conversation = data.iloc[button_index]

    # Extract and format the conversation parts
    assistant_content = process_system_assistant_content(conversation.get('assistant', ''))
    system_content = process_system_assistant_content(conversation.get('system', ''))
    user_content = process_user_content(conversation.get('user', ''))

    # Update the right-pane with the conversation content
    return [
        html.Div(assistant_content, className='assistant'),
        html.Div(system_content, className='system'),
        html.Div(user_content, className='user')
    ]
 """

app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism.min.css" rel="stylesheet" />
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/prism.min.js"></script>
        <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-AMS_HTML"></script>
        <script type="text/x-mathjax-config">
            MathJax.Hub.Config({
                tex2jax: {
                    inlineMath: [['$', '$'], ['\\()', '\\)']],
                    displayMath: [['$$', '$$'], ['\\[', '\\]']],
                    processEscapes: true,
                    skipTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
                    ignoreClass: "user"
                }
            });
        </script>
        <script type="text/javascript">
            function reprocessMathJaxForClass(className) {
                var elements = document.getElementsByClassName(className);
                for (var i = 0; i < elements.length; i++) {
                    MathJax.Hub.Queue(["Typeset", MathJax.Hub, elements[i]]);
                }
            }
        </script>
        <style>
            h4 {
                font-family: sans-serif;
                margin: 0;
            }
            #root {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            .conversation {
                border: 1px solid black;
                padding: 20px;
                background-color: #f3f3f3;
            }
            .message {
                white-space: pre-wrap;
                margin: 20px 0;
            }
            .author {
                font-weight: bold;
                margin-bottom: 4px;
            }
            .author::first-letter {
                text-transform: uppercase;
            }
            .code-block {
                background-color: #f7f7f7;
                border: 1px solid #e1e1e8;
                border-radius: 4px;
                padding: 10px;
                overflow: auto;
                font-family: 'Courier New', monospace;
            }
            .copy-code-button {
                margin: 5px;
                padding: 5px 10px;
                border: none;
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                cursor: pointer;
            }
            .system {
                color: gray; /* Example color for system messages */
            }
            .user {
                color: green; /* Example color for user messages */
            }
            .assistant {
                color: blue; /* Example color for assistant messages */
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            <script>
                document.querySelectorAll('pre code').forEach((block) => {
                    let button = document.createElement('button');
                    button.className = 'copy-code-button';
                    button.type = 'button';
                    button.innerText = 'Copy Code';
                    button.addEventListener('click', () => {
                        navigator.clipboard.writeText(block.innerText);
                        button.innerText = 'Copied!';
                        setTimeout(() => { button.innerText = 'Copy Code'; }, 2000);
                    });
                    block.parentNode.insertBefore(button, block);
                });
            </script>
            {%renderer%}
        </footer>
    </body>
</html>"""

@app.callback(
    Output('title-list', 'children'),
    [Input('right-pane', 'children')]  # This input is just a placeholder and won't affect the title list
)
def populate_title_list(_):
    # Create buttons for each conversation title
    return [
        html.Button(title, id={'type': 'title-button', 'index': i}, style={
            'display': 'block',
            'width': '100%',
            'border': 'none',
            'textAlign': 'left',
            'background': 'none',
            'padding': '10px'
        }) for i, title in enumerate(data['title'])
    ]

app.clientside_callback(
    """
    function(n_clicks) {
        if(typeof MathJax !== 'undefined') {
            MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
        }
        return '';
    }
    """,
    Output('trigger-mathjax', 'children'),
    [Input('right-pane', 'children')]
)



if __name__ == '__main__':
    app.run_server(debug=True)