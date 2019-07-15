ssl_cert = "/etc/letsencrypt/live/thedeax.tk/fullchain.pem"
ssl_key = "/etc/letsencrypt/live/thedeax.tk/privkey.pem"

from flask_app import app as application
import cherrypy

if __name__ == '__main__':
    cherrypy.tree.graft(application, "/")
    cherrypy.server.unsubscribe()
    server = cherrypy._cpserver.Server()
    server.socket_host = "0.0.0.0"
    server.socket_port = 8000
    server.thread_pool = 30
    server.ssl_module            = 'pyopenssl'
    server.ssl_certificate       = ssl_cert
    server.ssl_private_key       = ssl_key
    server.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()
