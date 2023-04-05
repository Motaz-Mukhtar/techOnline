from flask import Flask, jsonify, make_response
from flask_cors import CORS
from api.v1.views import app_views
from modules import storage


app_api = Flask(__name__)
app_api.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app_api.register_blueprint(app_views)

cors = CORS(app_api, resources={r'/api/v1/*': {'origins': '*'}})


@app_api.teardown_appcontext
def close_db(error):
    """ Close Storage """
    storage.close()


@app_api.errorhandler(404)
def not_found(error):
    """
        Return Not Found response (404)
    """
    return make_response(jsonify({'error': 'Not Found'}), 404)


if __name__ == "__main__":
    app_api.run('0.0.0.0', 5001, debug=True)