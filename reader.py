import os
import re
import json
import streamlit as st

from datetime import datetime

filename = "ChatGPT on 07 12 2023/conversations3.json"
file_path = os.path.realpath(__file__)
directory = os.path.dirname(file_path)
filename = os.path.join(directory, filename)

def load_data():
    with open(filename, 'r') as file:
        json_data = json.load(file)

        for item in json_data:
            if isinstance(item, dict) and "mapping" in item:
                process_mapping(item["mapping"])
            else:
                print("Mapping not found in this item.")

    return json_data

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def modify_latex_for_streamlit(text):
    """
    Uses regular expressions to modify LaTeX sequences in the text for Streamlit's Markdown compatibility.
    """
    text = re.sub(r'\\\(', '$', text)
    text = re.sub(r'\\\)', '$', text)
    text = re.sub(r'\\\[', '$$', text)
    text = re.sub(r'\\\]', '$$', text)
    return text

def display_message(mapping, node_id, level=0):
    if node_id not in mapping:
        return

    node = mapping[node_id]
    message = node.get('message')

    # Determine the role of the author
    author_role = message.get("author", {}).get("role", "").lower() if message else ""

    # Display the message content with appropriate formatting
    if message and 'content' in message and 'parts' in message['content']:
        parts = message['content']['parts']
        for part in parts:
            if part.strip():
                # Modify part for LaTeX if it's from system or assistant
                if author_role in ["system", "assistant"]:
                    part = modify_latex_for_streamlit(part)

                # Indentation for nested messages
                indent = "    " * level
                formatted_part = indent + part.replace("\n", "\n" + indent)

                # Display user messages as plain text in white color, others in Markdown
                if author_role == "user":
                    st.markdown(f'<span style="color: yellow;">{formatted_part}</span>', unsafe_allow_html=True)
                else:
                    st.markdown(formatted_part, unsafe_allow_html=True)

    # Recursively display children messages
    for child_id in node.get('children', []):
        display_message(mapping, child_id, level + 1)


def process_mapping(mapping):
    """
    Processes each node in the mapping of the JSON data.
    """
    for key, node in mapping.items():
        if "message" in node and node["message"]:
            message = node["message"]
            author_role = message.get("author", {}).get("role", "").lower()
            if "content" in message and "content_type" in message["content"] and message["content"]["content_type"] == "text":
                display_message(message["content"], author_role)



def process_json_recursively(json_data):
    """
    Recursively processes JSON data to modify LaTeX sequences and display messages.
    """
    if isinstance(json_data, dict):
        for value in json_data.values():
            process_json_recursively(value)
    elif isinstance(json_data, list):
        for item in json_data:
            process_json_recursively(item)


def convert_timestamp(timestamp):
    if timestamp:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return 'No Timestamp'


def display_conversation_details(conversation):
    if conversation:
        st.write("Title:", conversation.get('title', 'No Title'))
        st.write("Create Time:", conversation.get('create_time', 'No Create Time'))
        st.write("Update Time:", conversation.get('update_time', 'No Update Time'))

        mapping = conversation.get('mapping', {})
        root_nodes = [node_id for node_id, node in mapping.items() if node.get('parent') is None]

        for root_node in root_nodes:
            display_message(mapping, root_node)

def display_latex():
    latex_string = r"$$ e^{i\pi} + 1 = 0 $$"
    st.markdown(latex_string, unsafe_allow_html=True)


def main():
    local_css("style.css")

    st.title('OpenAI dump Reader')
    
    conversations = load_data()

    titles = [conv['title'] for conv in conversations if 'title' in conv]

    st.sidebar.header("Conversations")
    selected_title = st.sidebar.radio("Select a conversation:", titles, index=0)

    if selected_title:
        selected_conversation = next((conv for conv in conversations if conv['title'] == selected_title), None)
        if selected_conversation:
#            st.header("Conversation Details")
            st.markdown("Title: **{}**".format(selected_conversation.get('title', 'No Title')))
            st.markdown("Create Time: **{}**".format(convert_timestamp(selected_conversation.get('create_time'))))
            st.markdown("Update Time: **{}**".format(convert_timestamp(selected_conversation.get('update_time'))))

            mapping = selected_conversation.get('mapping', {})
            root_nodes = [node_id for node_id, node in mapping.items() if node.get('parent') is None]

            for root_node in root_nodes:
                display_message(mapping, root_node)


if __name__ == '__main__':
    main()
