from flask import Flask
import os

def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = os.environ.get('secret_key')

    from . import subrsum 
    app.register_blueprint(subrsum.bp)

    return app