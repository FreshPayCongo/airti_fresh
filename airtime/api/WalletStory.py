from flask_restful import reqparse
from flask import request, jsonify, Request
import requests
import random
from datetime import timedelta, datetime
from app import *
from api import airtime
from databases.Data import *
from config.configurations import *
import pymysql
import logging as logger
from flask_jwt_extended import (jwt_required, create_access_token, JWTManager)
from werkzeug.security import generate_password_hash, check_password_hash

# Configuration de la gestion des logs et traces
logger.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logger.DEBUG)

# Configuration de la gateway pour gérer les Keys pour les tokens
airtime.config['JWT_SECRET_KEY'] = 'joelbiolakayembepelou!$#%&*-+'  

@airtime.route("/api/v1/wallet/story/verify", methods=["POST"])
def verifyWalletStory():
    logger.info("VERIFICATION DE L'UNICITE DU MERCHANT_REF")
    parser = reqparse.RequestParser()
    parser.add_argument("wallet_code", type=str)
    parser.add_argument("user_updated", type=str)

    data = parser.parse_args() 
    wallet_code = data['wallet_code']

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    query = f"SELECT * FROM airtime_wallet_story WHERE wallet_code = '{wallet_code}'"
    details = executeQueryForGetData(conn, query)
    detailsTo = []

    for element in details:
        detailsTo.append({
            "amount" : element[3],
            "updated_at" : element[1],
            "method" : element[5],
            "currency" : element[4]
        })

    if len(details) == 0:
        return jsonify(
            resultCode=0,
            resultCodeDescription="Processed",
            resultData={}

        )
   
    writeLog("Verify historique wallet", user, "Comment : Processed with resultData")
    return jsonify({
        "resultCode" : "0",
        "resultCodeDescription" : "Processed",
        "wallet_code" : wallet_code,
        "historique" : detailsTo
    })
