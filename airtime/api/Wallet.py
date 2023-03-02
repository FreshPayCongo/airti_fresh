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
#Methode verifiant l'erreur lieer a la connexion a la base des donnees
def errorConnectBDD(conn):
    if type(conn) == tuple:
        logger.info("Probleme de connexion a la base de donnee")
        return errorMessage('database')

@airtime.route("/api/v1/agent/wallet/topup", methods=["POST"])
def topUpWallet():
    parser = reqparse.RequestParser()
    parser.add_argument("amount", type=float)
    parser.add_argument("wallet_code", type=str)
    parser.add_argument("super_agent_pass", type=str)
    parser.add_argument("method", type=str)

    data = parser.parse_args()

    amount = float(data['amount'])
    wallet_code = data['wallet_code']
    super_agent_pass = data['super_agent_pass']
    method = data['method']

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)

    query1 = f"SELECT * FROM airtime_check_auth_super_agent WHERE merchant_pass = '{super_agent_pass}'"
    details1 = executeQueryForGetData(conn, query1)

    #Verification de l'existance d'une ligne dans la base de donnees
    #Prouvant l'existance du marchand
    if len(details1) == 0:
        return errorMessage('notfoundmerchant')

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    query = f"SELECT * FROM airtime_wallet WHERE wallet_code = '{wallet_code}'"
    details = executeQueryForGetData(conn, query)
    ta = len(details)

    if ta == 0:
        logger.warning(f"{wallet_code} wallet n'existe pas dans le système")
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed",
            "resultCodeError" : 2,
            "method" : method,
            "amount": amount,
            "wallet_code" : wallet_code,
            "resultCodeErrorDescription" : "Le wallet code est déjà attribuer a un autre wallet dans le système"
        }), 400
    
    wallet_current_amount = float(details1[0][8])
    comission = float(details1[0][9])
    amount_to_to_up = wallet_current_amount +  (float(amount) + float((float(amount) * comission)/100))
    date_updated = str(datetime.now())
    query = f"UPDATE airtime_wallet SET updated_at = '{date_updated}', amount = {amount_to_to_up} WHERE wallet_code = '{wallet_code}'"
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    updateToSwitch = executeQueryForUpdate(conn, query)

    if updateToSwitch == 1:
        walletStory(wallet_code, float(amount), method)
        logger.info(f"{wallet_code} top up du wallet effectuee avec success")
        return jsonify({
            "resultCode" : "0",
            "resultCodeDescription" : "Processed",
            "resultDescription" : "top up du wallet effectuee avec succes",
            "updated_at" : date_updated,
            "amount" : amount_to_to_up,
            "wallet_code" : wallet_code,
            "method" : method
        }), 200


@airtime.route("/api/v1/superagent/wallet/topup", methods=["POST"])
def topUpWalletSuperAgent():
    parser = reqparse.RequestParser()
    parser.add_argument("amount", type=float)
    parser.add_argument("wallet_code", type=str)
    parser.add_argument("method", type=str)

    data = parser.parse_args()

    amount = float(data['amount'])
    wallet_code = data['wallet_code']
    method = data['method']

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    query = f"SELECT * FROM airtime_wallet WHERE wallet_code = '{wallet_code}'"
    details = executeQueryForGetData(conn, query)
    ta = len(details)

    if ta == 0:
        logger.warning(f"{wallet_code} wallet n'existe pas dans le système")
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed",
            "resultCodeError" : 2,
            "method" : method,
            "amount": amount,
            "wallet_code" : wallet_code,
            "resultCodeErrorDescription" : "Le wallet code est déjà attribuer a un autre wallet dans le système"
        }), 400
    
    wallet_current_amount = float(details[0][6])
    amount_to_to_up = wallet_current_amount +  float(amount)
    date_updated = str(datetime.now())
    query = f"UPDATE airtime_wallet SET updated_at = '{date_updated}', amount = {amount_to_to_up} WHERE wallet_code = '{wallet_code}'"
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    updateToSwitch = executeQueryForUpdate(conn, query)

    if updateToSwitch == 1:
        walletStory(wallet_code, float(amount), method)
        logger.info(f"{wallet_code} top up du wallet effectuee avec success")
        return jsonify({
            "resultCode" : "0",
            "resultCodeDescription" : "Processed",
            "resultDescription" : "top up du wallet effectuee avec succes",
            "updated_at" : date_updated,
            "amount" : amount_to_to_up,
            "wallet_code" : wallet_code,
            "method" : method
        }), 200


def walletStory(wallet_code, amount, method):
    logger.info(f"{wallet_code} creation du wallet historiser")
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    query = "INSERT INTO airtime_wallet_story(updated_at, amount, wallet_code, currency, method) VALUES(%s, %s, %s, %s, %s)"
    createdAt = str(datetime.now())
    dataToInsert = (createdAt, amount, wallet_code, 'USD', method)
    instertToSwitch = executeQueryForInsertDate(conn, query, dataToInsert)
    return 1

@airtime.route("/api/v1/wallet/verify", methods=["GET", "POST"])
def verifyWallet():
    logger.info("VERIFICATION DE L'UNICITE DU MERCHANT_REF")
    parser = reqparse.RequestParser()
    parser.add_argument("wallet_code", type=str)
    parser.add_argument("merchant_pass", type=str)

    data = parser.parse_args() 
    wallet_code = data['wallet_code']
    merchant_pass = data['merchant_pass']

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)

    query1 = f"SELECT * FROM airtime_check_auth WHERE merchant_pass = '{merchant_pass}'"
    details1 = executeQueryForGetData(conn, query1)

    #Verification de l'existance d'une ligne dans la base de donnees
    #Prouvant l'existance du marchand
    if len(details1) == 0:
        return errorMessage('notfoundmerchant')

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    query = f"SELECT * FROM airtime_wallet WHERE wallet_code = '{wallet_code}'"
    details = executeQueryForGetData(conn, query)
    ta = len(details)

    if ta == 0:
        logger.warning(f"{wallet_code} wallet n'existe pas dans le système")
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed",
            "resultCodeError" : 2,
            "wallet_code" : wallet_code,
            "resultCodeErrorDescription" : "Le wallet code est déjà attribuer a un autre wallet dans le système"
        }), 400

    return jsonify(
        resultCode=0,
        resultCodeDescription="Processed",
        resultData={
            "currency" : str(details[0][5]),
            "created_at" : str(details[0][1]),
            "updated_at" : str(details[0][2]),
            "wallet_code" : str(details[0][3]),
            "amount" : float(details[0][6]),
            "account_code" : str(details[0][4])
        }
    )
