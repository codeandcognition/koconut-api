# formerly __init__.py
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

from app import routes
# import routes

# if __name__ == "__main__":
#     # Make temp directory
#     if not os.path.isdir("temp"):
#         os.mkdir("temp")

#     app.run()
