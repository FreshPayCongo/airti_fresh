from flask import Flask, jsonify
#from paydrc.api import payDrc_api as application
from api import airtime as application
import logging as logger

# Configuration de la gestion des logs et traces
logger.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logger.DEBUG)

if __name__ == '__main__':
    logger.debug("Lancement du middleware pour gerer le airtime")
    application.run(host="0.0.0.0", port=2801, debug=True, use_reloader=True)