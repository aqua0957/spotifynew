import os

from dotenv import load_dotenv



import streamlit as st

from langchain_core.messages import AIMessage, HumanMessage



from agent_script import invoke_our_graph, create_graph



import asyncio





import time

import requests

import random



load_dotenv()  # Load environment variables from a .env file if present*

titlenum = random.randint(1,9)

if (1 <= titlenum <= 3):
    st.title("What's on your playlist today? 👀")
elif (4 <= titlenum <= 6):
    st.title("It's a great day for music 😊")
elif (7 <= titlenum <= 9):
    st.title("Shall we get the party started? 🎵")

if "messages" not in st.session_state:

    # default initial message to render in message state

    st.session_state["messages"] = [AIMessage(content="How can I help you? (Try: \"Add [song] to queue\" \"Make me a [mood] playlist'\)")]





if "agent" not in st.session_state:

    st.session_state["agent"] = asyncio.run(create_graph())



agent = st.session_state["agent"]

def process_agent_response(prompt):
    """Helper function to process agent response"""
    st.session_state.messages = []
    st.session_state.messages.append(HumanMessage(content=prompt))
    st.session_state["skip_display"] = len(st.session_state.messages) - 1

    with st.chat_message("assistant"):
        output = requests.post("http://localhost:8000/chat", json={"message": prompt})
        output = output.json()
        text = output["response"]["messages"][-1]['content']
        print(text)

        placeholder = st.empty()
        streamed_text = ""

        for token in text.split():
            streamed_text += token + " "
            placeholder.write(streamed_text)
            time.sleep(0.07)

        st.session_state.messages.append(AIMessage(content=text))

left, middle, right = st.columns(3)
if left.button("Previous", icon="◀️", width="stretch"):
    process_agent_response("◀️")
if middle.button("Play/Pause", icon="⏯️", width="stretch"):
    process_agent_response("⏯️")
if right.button("Next", icon="▶️", width="stretch"):
    process_agent_response("▶️")


# Display chat messages (skip if we just processed a button)
if "skip_display" not in st.session_state:
    for msg in st.session_state.messages:
        if type(msg) == AIMessage:
            st.chat_message("assistant").write(msg.content)
        if type(msg) == HumanMessage:
            st.chat_message("user").write(msg.content)
else:
    st.session_state.pop("skip_display")

# Add Help button to sidebar (stays fixed at bottom)
if st.sidebar.button("Help", icon="❔", width="stretch"):
    process_agent_response("Button press: Help")

# takes new input in chat box from user and invokes the graph
if prompt := st.chat_input():
    st.session_state.messages.append(HumanMessage(content=prompt))
    st.chat_message("user").write(prompt)



    # Process the AI's response and handles graph events using the callback mechanism

    with st.chat_message("assistant"):

        serialized_messages = [msg.dict() if hasattr(msg, 'dict') else msg for msg in st.session_state.messages]

        output = requests.post("http://localhost:8000/chat", json={"message": prompt})

        output = output.json()

        text = output["response"]["messages"][-1]['content']

        print(text)

        placeholder = st.empty()

        streamed_text = ""

        for token in text.split():

            streamed_text += token + " "

            placeholder.write(streamed_text)

            time.sleep(0.07)  # Adjust speed as needed



        st.session_state.messages.append(AIMessage(content=text))