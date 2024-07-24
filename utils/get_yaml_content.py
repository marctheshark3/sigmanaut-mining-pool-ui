import requests
import yaml
import hashlib

def get_yaml_content(file_url):
    try:
        # Send a GET request to the URL
        response = requests.get(file_url)
        content = response.text
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the response content as YAML
            return yaml.safe_load(response.content), hashlib.md5(content.encode()).hexdigest()
        else:
            print(f"Failed to retrieve file: Status code {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        # Handle any exceptions that occur during the request
        print(f"An error occurred: {e}")
        return None
    except yaml.YAMLError as e:
        # Handle any exceptions that occur during YAML parsing
        print(f"Failed to parse YAML: {e}")
        return None