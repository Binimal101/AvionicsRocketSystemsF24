from hashlib import sha256
from pprint import pprint
import os
import threading
from queue import Queue
from time import sleep

from flask import Flask, render_template, request, url_for

app = Flask(__name__)

# ROUTES
@app.route("/")
def index():
    return render_template("visualize.html")
