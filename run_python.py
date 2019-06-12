import os
from app import app

if __name__ == "__main__":
    # Make temp directory
    if not os.path.isdir("temp"):
        os.mkdir("temp")

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
