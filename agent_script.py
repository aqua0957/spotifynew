import os
import requests
import subprocess
from groq import Groq
from dotenv import load_dotenv

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
def main():

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
if __name__ == "__main__":

        main()

