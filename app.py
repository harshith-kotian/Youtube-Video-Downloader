import requests
import logging
from flask import Flask, jsonify, request

# Initialize the Flask application
app = Flask(__name__)

# Enable logging for debugging
logging.basicConfig(level=logging.DEBUG)

@app.route('/api/info', methods=['GET'])
def get_video_info():
    # Retrieve the YouTube video URL from the query parameters
    url = request.args.get('url')

    # If URL is not provided, return an error
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # Send a GET request to Invidious API to fetch video info
        response = requests.get(f"https://api.invidious.io/api/v1/videos?url={url}")

        # Log the response status and content for debugging
        logging.debug(f"Response status code: {response.status_code}")
        logging.debug(f"Response content: {response.text}")

        # Check if the response status code is 200 (success)
        if response.status_code == 200:
            try:
                # Try to parse the response as JSON
                data = response.json()
                return jsonify(data)  # Return the JSON data as a response
            except ValueError:
                # If response is not valid JSON, return an error message
                return jsonify({"error": "Invalid JSON response from Invidious API"}), 500
        else:
            # If the API request failed, return an error with the status code
            return jsonify({"error": "Failed to fetch data from Invidious API", "status_code": response.status_code}), 500
    except requests.exceptions.RequestException as e:
        # Handle exceptions related to the request (e.g., network issues)
        return jsonify({"error": f"Request failed: {str(e)}"}), 500


if __name__ == '__main__':
    # Run the app in debug mode for development
    app.run(debug=True)