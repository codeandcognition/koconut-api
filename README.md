# koconut-api
Python API for checking correctness &amp; knowledge tracing for [Koconut (now Codeitz)](https://github.com/codeandcognition/koconut). 
Benji Xie (bxie@uw.edu)

# Set-up
The Koconut API runs on Python 3 (tested on 3.7.3, but 3.6 should work). All Python library dependencies (namely Flask, NumPy, Pandas) are listed in the [requirements.txt](https://github.com/codeandcognition/koconut-api/blob/master/requirements.txt) file. Ensure you have Python3 running and have downloaded all dependencies (via `pip`). If you don't want to make global changes to your Python configuration, consider creating a virtual environment ([venv](https://docs.python.org/3/library/venv.html)) for the Koconut API.

## Running API locally
1. Clone the repo.
2. In the parent directory of the repo, type the following command: `export FLASK_APP=run_python.py`. This command sets the environment variable and tells Flask to run the run_python.py file on execution.
3. Run flask with the following command: `flask run`. You should see a response specifying that Flask is serving the app.
4. To verify the app is running, go to [127.0.0.1:5000](127.0.0.1:5000) and see a very exciting "Hello python service!" message. You should also see a 200 response in your console where Flask is running.

To do something more interesting, let's execute a POST request (e.g w/ [Postman](https://www.getpostman.com/))! to the /bkt endpoint (127.0.0.1:5000/bkt) with the JSON object in [example_bkt_data.json](https://github.com/codeandcognition/koconut-api/blob/master/example_data/example_bkt_data.json) in the body of the request. After doing that, you should see another 200 response on your console and a request body which includes a "pkNew" attribute being set ot 0.3383...

Congratulations! You've run the koconut API locally. 👏🏽

## Deploying on Heroku
The Procfile is already setup to use gunicorn, so this code should just be able to be deployed to Heroku. After a successful deployment, verify that `/` and `/bkt` endpoints work (just as was done in running API locally).
