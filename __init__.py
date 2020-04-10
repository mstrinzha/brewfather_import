import eventlet
eventlet.monkey_patch()
from modules import cbpi
import time
from thread import start_new_thread
from flask import Flask, Response, request
from json import dumps
from flask_cors import CORS
import os
import logging
from modules.steps import Step,StepView
from OpenSSL import crypto
import random
import socket

def create_self_signed_cert(certfile, keyfile, certargs, cert_dir="."):
    C_F = os.path.join(cert_dir, certfile)
    K_F = os.path.join(cert_dir, keyfile)
    if not os.path.exists(C_F) or not os.path.exists(K_F):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 4096)
        
        cert = crypto.X509()
        cert.get_subject().C = certargs["Country"]
        cert.get_subject().ST = certargs["State"]
        cert.get_subject().L = certargs["City"]
        cert.get_subject().O = certargs["Organization"]
        cert.get_subject().OU = certargs["Org. Unit"]
        subject = cert.get_subject()
        subject.commonName = ip_address
        cert.set_issuer(subject)
        cert.set_serial_number(random.randrange(100000))
        cert.set_version(2)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10*356*24*60*60)
        subject_alt_names = ", ".join(["IP:%s" % ip_address ])
        
        cert.add_extensions([
        crypto.X509Extension(b'subjectAltName', False,
            ','.join([
#                 'DNS:%s' % hostname,
#                 'DNS:*.%s' % hostname,
#                 'DNS:localhost',
#                 'DNS:*.localhost',
                'IP:%s' % ip_address]).encode()),
        crypto.X509Extension(b"basicConstraints", True, b"CA:false")])

        
        cert.set_pubkey(k)
        cert.sign(k, 'SHA512')
        
        open(C_F, "wb").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        open(K_F, "wb").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

@cbpi.initalizer(order=100)
def init(cbpi):
    base_dir = os.path.dirname(__file__)
    CERT_FILE = os.path.join(base_dir, "cert.pem")
    KEY_FILE = os.path.join(base_dir, "key.pem")
    create_self_signed_cert(CERT_FILE, KEY_FILE,
                            certargs=
                            {"Country": "RU",
                            "State": "Moscow",
                             "City": "Brewery",
                             "Organization": "Home Brewery",
                             "Org. Unit": "Brewer"})
    
    cbpi.app.logger.info("Starting brewfather importer thread")
    
    def serve():
        try:
            app = Flask(__name__)
            CORS(app)
            cors = CORS(app, resources={
                r"/*": {
                   "origins": "*"
                }
            })
            
            
            @app.route('/', methods=['GET'])
            def home_page():
                return Response("Hello from BrewFather importer plugin", mimetype='text/json')
                
            @app.route("/brewfather_import/v1", methods=['POST'])
            def create_user():
                data = request.json
                print dumps(data)
                recipe = data.get('recipe')
                
                mash = recipe.get('mash')
                
                name = mash.get("name", "No Name")
                cbpi.set_config_parameter("brew_name", name)
                recipe_name = recipe.get('name', name)
                steps = mash.get('steps')
                
                Step.delete_all()
                StepView().reset()
                mashstep_type = cbpi.get_config_parameter("step_mash", "MashStep")
                mash_kettle = cbpi.get_config_parameter("step_mash_kettle", None)
                for step in steps:
                    Step.insert(**{"name": step.get("name","Mash Step"), "type": mashstep_type, "config": {"kettle": mash_kettle, "temp": step.get("stepTemp",0), "timer": step.get("stepTime",0)}})
#                 StepView().reset()
                print "1"    
                cbpi.emit("UPDATE_ALL_STEPS", Step.get_all())
                print "2"
                cbpi.notify(headline="Recipe %s loaded successfully" % recipe_name, message="")    
                print "3"
                return ('', 204)
            
            logging.getLogger('flask_cors').level = logging.DEBUG
#             base_dir = os.path.dirname(__file__)
#             crt_path = os.path.join(base_dir, 'server.crt')
#             key_path = os.path.join(base_dir, 'server.key')
            app.run(host="0.0.0.0", port=5001, debug=True, use_reloader = False, ssl_context=(CERT_FILE, KEY_FILE))
        except Exception as e:
            print "e %s" % e
            pass

    eventlet.spawn(serve)
#     start_new_thread(serve, ())
    pass