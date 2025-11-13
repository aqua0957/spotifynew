import os
import requests
import subprocess
from groq import Groq
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import MessagesState
import asyncio
from mcp_use.client import MCPClient
from mcp_use.adapters.langchain_adapter import LangChainAdapter

load_dotenv()

def check_spotify_credentials():

        """

        Check if Spotify API credentials are valid by attempting to get an access token.

        Returns True if valid, False otherwise.

        """

        client_id = os.getenv("SPOTIFY_CLIENT_ID")

        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

       

        # Check if credentials exist

        if not all([client_id, client_secret, redirect_uri]):

            print("❌ Missing Spotify credentials in .env file")

            return False

       

        # Test credentials by requesting a client credentials token

        auth_url = "https://accounts.spotify.com/api/token"

        auth_headers = {

            "Content-Type": "application/x-www-form-urlencoded"

        }

        auth_data = {

            "grant_type": "client_credentials",

            "client_id": client_id,

            "client_secret": client_secret

        }

       

        try:

            response = requests.post(auth_url, headers=auth_headers, data=auth_data)

            if response.status_code == 200:

                print("✅ Spotify credentials are valid")

                return True

            else:

                print(f"❌ Spotify credentials invalid. Status: {response.status_code}")

                print(f"Response: {response.json()}")

                return False

        except Exception as e:

            print(f"❌ Error checking Spotify credentials: {e}")

            return False


def check_groq_credentials():

        """

        Check if Groq API credentials are valid by attempting to get an access token.

        Returns True if valid, False otherwise.

        """

        client = Groq(
            # This is the default and can be omitted
             api_key=os.environ.get("GROQ_API_KEY"),
        )

       

        # Check if credentials exist

        if not client:

            print("❌ Missing Groq credentials in .env file")

            return False

       

        # Test credentials by requesting a client credentials token

        models = client.models.list()

        try:

            response = models

            if len(response.model_dump_json()) != 0:

                print("✅ Groq credentials are valid")

                return True

            else:

                print(f"❌ Groq credentials invalid. Status: {response.status_code}")

                print(f"Response: {response.model_dump_json()}")

                return False

        except Exception as e:

            print(f"❌ Error checking Groq credentials: {e}")

            return False
        
def kill_processes_on_port(port):

    """Kill processes on Windows"""

    try:

        # Find processes using the port

        result = subprocess.run(['netstat', '-ano'],

                              capture_output=True, text=True, check=False)

       

        if result.returncode == 0:

            lines = result.stdout.split('\n')

            pids_to_kill = []

           

            for line in lines:

                if f':{port}' in line and 'LISTENING' in line:

                    parts = line.split()

                    if len(parts) >= 5:

                        pid = parts[-1]  # Last column is PID

                        if pid.isdigit():

                            pids_to_kill.append(pid)

           

            if pids_to_kill:

                print(f"Found processes on port {port}: {pids_to_kill}")

                for pid in pids_to_kill:

                    try:

                        subprocess.run(['taskkill', '/F', '/PID', pid],

                                     check=True, capture_output=True)

                        print(f"Killed process {pid} on port {port}")

                    except subprocess.CalledProcessError as e:

                        print(f"Failed to kill process {pid}: {e}")

            else:

                print(f"No processes found on port {port}")

        else:

            print(f"Failed to run netstat: {result.stderr}")

           

    except Exception as e:

        print(f"Error killing processes on port {port}: {e}")

async def create_graph():
     #create client

    client = MCPClient.from_config_file("mcp_config.json")

    #create adapter instance

    adapter = LangChainAdapter()

    #load in tools from the MCP client

    tools = await adapter.create_tools(client)

    ## tools = [t for t in tools if t.name not in['getNowPlaying', 'getRecentlyPlayed', 'getQueue', 'playMusic', 'pausePlayback', 'skipToNext', 'skipToPrevious', 'resumePlayback', 'addToQueue', 'getMyPlaylists','getUsersSavedTracks', 'saveOrRemoveAlbum', 'checkUsersSavedAlbums']]
    ## tools = [t for t in tools if t.name not in['playMusic', 'pausePlayback', 'skipToNext', 'skipToPrevious', 'resumePlayback', 'addToQueue']]

    #define llm

    llm = ChatGroq(model='meta-llama/llama-4-scout-17b-16e-instruct')

    #bind tools

    llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)

    system_msg = """You are a helpful assistant that has access to Spotify tools. You can search for music, create playlists, add tracks to playlists, and get album information.

Available tools:
- searchSpotify: Search for tracks, albums, artists, or playlists on Spotify
- createPlaylist: Create a new playlist. Parameters: name (string, required), description (string, optional), public (boolean false or true, optional - use false not "false")
- addTracksToPlaylist: Add tracks to an existing playlist using track IDs
- getAlbums: Get detailed information about albums by their Spotify IDs
- getAlbumTracks: Get all tracks from a specific album
- saveOrRemoveAlbumForUser: Save or remove albums from the user's library
- getNowPlaying: Get information about the current playing track on Spotify
- getMyPlaylists: Get a list of the current user's playlists on Spotify
- getPlaylistTracks: Get a list of tracks in a specific Spotify playlist
- getRecentlyPlayed: Retrieves a list of recently played tracks from Spotify.
- getUsersSavedTracks: Get a list of tracks saved in the user's "Liked Songs" library

- playMusic: Start playing a track, album, or playlist on Spotify
- pausePlayback: Pause the currently playing track on Spotify
- resumePlayback: Resume the current playing track on Spotify
- skipToNext: Skip to the next track in the current playback queue
- skipToPrevious: Skip to the previous track in the current playback queue
- addToQueue: Adds a track, album, artist, or playlist to the current playback queue.


When creating playlists:
- Always first search for songs using searchSpotify to get track IDs
- Then create a playlist using createPlaylist with name as a string and public as a boolean (true or false, not quoted)
- Finally, add the found tracks using addTracksToPlaylist with the playlist ID and track IDs
- If the user does not specify playlist size, limit playlists to only 10 songs
- Always provide helpful music recommendations based on user preferences
- When passing parameters, ensure: public is a boolean (true/false not "true"/"false"), name and description are strings

If "Button press: Previous track" is recieved, play the previous track.
If "Button press: Next track" is recieved, play the next track.
If "Button press: Play/Pause" is recieved: act as follows:
- If a track is currently playing, pause playback.
- If a track is not currently playing, resume playback.
If "Button press: Help" is recieved, list all the tools available. Use the descriptions as specified previously, however use natural language instead of the explicit tool names. Each tool should be listed on its own line, beginning with a '-' character.

When modifying the playback state or modifying the queue, always send an affirmative statement after excecuting the tool.
If a user requests to start playback with out specifying a track, it can be assumed the user wants to resume playback.

If an action is done successfully do not ask the user for further instructions.
Important: Only use the tools listed above. Do not attempt to call any other tools."""

    #define assistant

    def assistant(state: MessagesState):

        return {"messages": [llm_with_tools.invoke([system_msg] + state["messages"])]}

       # Graph

    builder = StateGraph(MessagesState)



    # Define nodes: these do the work

    builder.add_node("assistant", assistant)

    builder.add_node("tools", ToolNode(tools))

    # Define edges: these determine the control flow

    builder.add_edge(START, "assistant")

    builder.add_conditional_edges(

        "assistant",

        tools_condition,

    )

    builder.add_edge("tools", "assistant")

    graph = builder.compile()

    return graph

async def invoke_our_graph(agent, st_messages):

    response = await agent.ainvoke({"messages": st_messages})

    return response




async def main():

        print("Checking API credentials...\n")

        spotify_valid = check_spotify_credentials()

        groq_valid = check_groq_credentials()

        print(f"\nCredentials Summary:")

        print(f"Spotify: {'✅ Valid' if spotify_valid else '❌ Invalid'}")

        print(f"Groq: {'✅ Valid' if groq_valid else '❌ Invalid'}")

       

        if spotify_valid and groq_valid:

            print("\n🎉 All credentials are working!")

        else:

            print("\n⚠️  Please fix invalid credentials before proceeding.")

        kill_processes_on_port(8090)

        agent = await create_graph()
        
        while True:

            final_text = ""

            message = input("User: ")

            from langchain_core.messages import HumanMessage

            response = await agent.ainvoke({"messages": [HumanMessage(content=message)]})
            for m in response["messages"]:
                m.pretty_print()

if __name__ == "__main__":
    # Run the main function in an event loop
    asyncio.run(main())

