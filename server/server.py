from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from threading import Thread, Event
import json, os, signal, socket, socketserver, struct, ssl, sys, time


def webdrive(paths, url, options):
    # browser options, such as: incognito, fullscreen, hide automation notice
    chromeopts = webdriver.ChromeOptions()
    chromeopts.add_argument("--incognito")
    chromeopts.add_experimental_option("useAutomationExtension", False)
    chromeopts.add_experimental_option("excludeSwitches", ["enable-automation"])
    chromeopts.binary_location = paths["browser"]
    if "fullscreen" in options:
        chromeopts.add_argument("--start-fullscreen")
    driver = webdriver.Chrome(paths["driver"], chrome_options=chromeopts)
    driver.get(url)

    # site specific settings flags - after loading site
    if "autoplay" in options:
        if url.startswith("https://hypno.n"):
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#intro-start"))
                )
                element.click()
            except:
                pass
        if url.startswith("https://myn"):
            try:
                # can't find the right thing to block on for loading
                # no element is added and i can't tell what changes
                time.sleep(3)
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "body>div.player>div.contextPlay>img"))
                )
                element.click()
            except:
                pass
        if url.startswith("https://www.youtu"):
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#movie_player>div.ytp-cued-thumbnail-overlay>button"))
                )
                element.click()
            except:
                pass

    # run indefinitely until closed
    while 1:
        time.sleep(1)


class PasswordTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(
        self,
        server_address,
        RequestHandlerClass,
        config,
        bind_and_activate=True,
    ):
        self.password = config["password"]
        self.paths = config["paths"]
        self.wearable = config["wearable"]
        socketserver.TCPServer.__init__(
            self, server_address, RequestHandlerClass, bind_and_activate=True
        )

        key = os.path.join(os.getcwd(), config["ssl"]["key"])
        cert = os.path.join(os.getcwd(), config["ssl"]["cert"])
        print(key)

        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.verify_mode = ssl.CERT_NONE
        context.load_cert_chain(keyfile=key, certfile=cert)

        self.socket = context.wrap_socket(self.socket)

        # if bind_and_activate:
        #    self.server_bind()
        #    self.server_activate()


class BrowserOpenHandler(socketserver.StreamRequestHandler):
    def openurl(self, url, options):
        system = "linux" if os.name == "posix" else "windows"
        self.wfile.write(
            "opened {} on the machine!".format(url).encode("utf-8")
        )
        thread = Thread(
            target=webdrive, args=(self.server.paths[system], url, options)
        )
        thread.start()

    def wearable(self, mode):
        print("wearable: {}".format(mode))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        sock.sendto(
            struct.pack("B", int(mode)),
            (self.server.wearable["ip"], int(self.server.wearable["port"])),
        )
        self.wfile.write(
            "set wearable to {} mode!".format(mode).encode("utf-8")
        )

    def handle(self):
        """
        parse incoming message:
        messages are in the form of sections divided by vertical bar character "|"
        sections defined as the following:
            0:    password
            1:    command
            2...: arguments
        so that example messages could be
            passwordstring|open_url|url|options
            passwordstring|wearable|mode

        commands:
            open_url:
                arguments:
                    0: url
                    1: list of options: string, python list textual representation
            wearable:
                arguments:
                    0: mode: unsigned int
        """
        self.data = self.rfile.readline().strip().decode("utf-8")
        print(self.data)
        parts = self.data.split("|")

        print(parts)

        if len(parts) == 0:
            self.wfile.write("no data received".encode("utf-8"))

        # reject bad authentication
        if parts[0] != self.server.password:
            self.wfile.write("bad authentication".encode("utf-8"))
            return

        # handle command branching
        if parts[1] == "open_url":
            if len(parts) != 4:
                print("expected four parts: received {}".format(parts))
                self.wfile.write("open_url: bad format".encode("utf-8"))
            (_, _, url, options) = parts
            print(
                "{} is sending a request to open {} with {}".format(
                    self.client_address[0], url, options
                )
            )
            self.openurl(url, options)

        if parts[1] == "wearable":
            if len(parts) != 3:
                print("expected three parts: received {}".format(parts))
                self.wfile.write("wearable: bad format".encode("utf-8"))
            (_, _, mode) = parts
            self.wearable(mode)


if __name__ == "__main__":
    with open("server_config.json", "r") as cfg:
        config = json.load(cfg)
        host = config["host"]
        port = config["port"]
        with PasswordTCPServer(
            (host, port), BrowserOpenHandler, config
        ) as server:
            print("listening on {}:{}".format(host, port))
            server_thread = Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            while 1:
                pass
