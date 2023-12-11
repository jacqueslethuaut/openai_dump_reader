# MIT License
#
# Copyright (c) 2023 Jacques Le Thuaut

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
            if isinstance(part, str) and part.strip():
                # Modify part for LaTeX if it's from system or assistant
                author_role = message.get("author", {}).get("role", "").lower()
                if author_role in ["system", "assistant"]:
                    part = modify_latex_for_streamlit(part)

                # Indentation for nested messages
                indent = "    " * level
                formatted_part = indent + part.replace("\n", "\n" + indent)

                # Display user messages as plain text, others in Markdown
                if author_role == "user":
                    st.markdown(f'<span style="color: yellow;">{formatted_part}</span>', unsafe_allow_html=True)
                else:
                    st.markdown(formatted_part, unsafe_allow_html=True)
            elif isinstance(part, dict) and 'content_type' in part:
                # Process other content types like images
                if part['content_type'] == 'image_asset_pointer':
                    image_url = part.get('asset_pointer', '')
                    st.image(image_url, caption='Image', width=300)  

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
    st.title('OpenAI dump Reader')

    # Initialize session state variables
    if 'search_mode' not in st.session_state:
        st.session_state['search_mode'] = "Title"
    if 'search_button_pressed' not in st.session_state:
        st.session_state['search_button_pressed'] = False
    if 'browse_button_pressed' not in st.session_state:
        st.session_state['browse_button_pressed'] = False
    if 'selected_browse_title' not in st.session_state:
        st.session_state['selected_browse_title'] = None
    if 'selected_search_title' not in st.session_state:
        st.session_state['selected_search_title'] = None

    conversations = load_data()
    st.sidebar.header("Conversations and Search")

    with st.sidebar.expander("Search Conversations", expanded=st.session_state.search_button_pressed):
        search_mode = st.radio("Search by", ["Title", "All Messages"], key='search_mode')
        search_term = st.text_input("Search term", key='search_term')
        if st.button("Search"):
            st.session_state['search_button_pressed'] = True
            st.session_state['browse_button_pressed'] = False

    with st.sidebar.expander("Browse Conversations", expanded=st.session_state.browse_button_pressed):
        titles = [conv['title'] for conv in conversations if 'title' in conv]
        if st.button("Activate All Conversations"):
            st.session_state['browse_button_pressed'] = True
            st.session_state['search_button_pressed'] = False
        st.session_state['selected_browse_title'] = st.radio("Select a conversation:", titles, index=0, key='browse_select')

    # Display logic
    if st.session_state.search_button_pressed and search_term:
        filtered_conversations = filter_conversations(conversations, search_term, search_mode)
        if filtered_conversations:
            st.session_state['selected_search_title'] = st.sidebar.selectbox("Select from search results:", [conv['title'] for conv in filtered_conversations], key='search_select')
            selected_conversation = next((conv for conv in filtered_conversations if conv['title'] == st.session_state['selected_search_title']), None)
            display_conversation(selected_conversation)
    elif st.session_state.browse_button_pressed and st.session_state['selected_browse_title']:
        selected_conversation = next((conv for conv in conversations if conv['title'] == st.session_state['selected_browse_title']), None)
        display_conversation(selected_conversation)

    

def display_conversation(conversation):
    if conversation:
        # Display conversation details
        st.markdown("Title: **{}**".format(conversation.get('title', 'No Title')))
        st.markdown("Create Time: **{}**".format(convert_timestamp(conversation.get('create_time'))))
        st.markdown("Update Time: **{}**".format(convert_timestamp(conversation.get('update_time'))))

        mapping = conversation.get('mapping', {})
        root_nodes = [node_id for node_id, node in mapping.items() if node.get('parent') is None]

        for root_node in root_nodes:
            display_message(mapping, root_node)

def filter_conversations(conversations, term, mode):
    """
    Filter conversations based on the search term and mode.
    """
    if mode == "Title":
        return [conv for conv in conversations if term.lower() in conv.get('title', '').lower()]
    else:
        # Implement logic to search through all messages
        return [conv for conv in conversations if term.lower() in str(conv).lower()]


if __name__ == '__main__':
    main()
