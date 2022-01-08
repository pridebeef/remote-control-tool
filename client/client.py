from flask import Flask, render_template, request
from threading import Thread
import json, socket, ssl

import subprocess, sys

app = Flask(__name__)


wearable_settings = {}
with open("modes.json", "r") as f:
    wearable_settings = json.load(f)


def socket_send(form):
    # tls socket creation
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.verify_mode = ssl.CERT_NONE
    sock = context.wrap_socket(s)
    sock.connect((form["ip"], int(form["port"])))

    # message generation
    message = "{}|{}|".format(form["password"], form["command"])
    if form["command"] == "open_url":
        args = []
        if form["fullscreen"] == "true":
            args.append("fullscreen")
        if form["autoplay"] == "true":
            args.append("autoplay")
        message += "{}|{}".format(form["url"], args)
    if form["command"] == "wearable":
        message += "{}".format(form["mode"])

    print(message)
    sock.sendall(message.encode("utf-8"))
    # received = sock.recv(1024).decode("utf-8")
    print("sent")
    sock.close()
    # print(repr(received)[1:-1])


@app.route("/")
def index():
    return render_template(
        "dashboard.html", wearable_modes=wearable_settings or []
    )


@app.route("/send", methods=["POST"])
def send():
    print(request.form)
    t = Thread(target=socket_send, args=[request.form])
    t.daemon = True
    t.start()
    return "received"


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
