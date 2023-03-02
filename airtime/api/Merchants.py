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

# Objet de gestion des tokens
jwt = JWTManager(airtime)
#Methode pour generer les codes et id
def generatedID():
    motifs = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789?/|][{=+-_)(*&^%$#@!~;:.,><)}"
    return 'ai' + ''.join((random.choice(motifs)) for i in range(5)) +  ''.join((random.choice(motifs)) for j in range(3)) +  ''.join((random.choice(motifs)) for k in range(3)) + ''.join((random.choice(motifs)) for l in range(4)) + 'tiB'

#Methode pour generer les codes et id
def generatedIDforXML():
    motifs = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#/"
    return 'jz' + ''.join((random.choice(motifs)) for i in range(5)) +  ''.join((random.choice(motifs)) for j in range(3)) +  ''.join((random.choice(motifs)) for k in range(3)) + ''.join((random.choice(motifs)) for l in range(4)) + 'b'

#Methode pour generer les PIN des utilisateur pour chaque merchant
def generatedPIN():
    motifs = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return 'I' + ''.join((random.choice(motifs)) for i in range(5))  + 'P'


#Methode pour generer les codes
def generatedMerchantCode():
    motifs = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return 'm' + ''.join((random.choice(motifs)) for i in range(3)) +  ''.join((random.choice(motifs)) for j in range(3)) +  ''.join((random.choice(motifs)) for k in range(3)) + ''.join((random.choice(motifs)) for l in range(3))

@airtime.route("/api/v1/agent/secrete", methods=["POST"])
def geneNewSecrete():
    parser = reqparse.RequestParser()
    parser.add_argument("merchant_id", type=str)

    data = parser.parse_args()
    #Info Merchant
    merchant_id = data['merchant_id']
    return jsonify({
        "Test" : "OK"
    }), 200

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500

    #Verification de l'existance de l'institution_code
    query = f"SELECT * FROM airtime_merchant WHERE merchant_id = '{merchant_id}'"
    details = executeQueryForGetData(conn, query)
    ta = len(details)

    if ta == 0:
        writeLog("verify institution_code", user, "Comment : Processed, Not Found")
        return jsonify(
            resultCode=0,
            resultCodeDescription="Processed",
            resultData={}
        )
    merchant_secrete_to_show = generatedIDforXML()
    merchant_secrete = generate_password_hash(merchant_secrete_to_show)

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500
    date_updated = str(datetime.now())
    query = f"UPDATE airtime_merchant SET updated_at = '{date_updated}', merchant_secrete = '{merchant_secrete}' WHERE merchant_id = '{merchant_id}'"
    updateToSwitch = executeQueryForUpdate(conn, query)

    return jsonify(
        resultCode=0,
        resultCodeDescription="Processed",
        resultData={
            "updated_at" : date_updated,
            "merchant_id" : merchant_id,
            "merchant_secrete" : merchant_secrete_to_show
        }
    ), 200

#Creation du merchant avec toutes ses informations
@airtime.route("/api/v1/agent/create", methods=["POST"])
def createMerchant():
    errorList = {}
    error = ()
    parser = reqparse.RequestParser()
    parser.add_argument("merchant_name", type = str)
    parser.add_argument("merchant_email", type = str)
    parser.add_argument("merchant_phone", type = str)
    parser.add_argument("merchant_code", type = str)
    parser.add_argument("merchant_user_firstname", type=str)
    parser.add_argument("merchant_user_lastname", type=str)
    parser.add_argument("merchant_user_password", type=str)
    parser.add_argument("merchant_comission", type = str)
    parser.add_argument("merchant_recruter", type = str)

    data = parser.parse_args()
    #Info Merchant
    merchant_name = data['merchant_name']
    merchant_email = data['merchant_email']
    merchant_phone = data['merchant_phone']
    merchant_code = data['merchant_code']
    merchant_user_firstname = data['merchant_user_firstname']
    merchant_user_lastname = data['merchant_user_lastname']
    merchant_user_password = data['merchant_user_password']
    merchant_recruter = data['merchant_recruter']
    merchant_user_pin = generatedPIN()

    #Info merchant generated
    merchant_id = generatedID()
    merchant_secrete_to_show = generatedIDforXML()
    merchant_secrete = generate_password_hash(merchant_secrete_to_show)
    merchant_pass = generatedIDforXML()
    merchant_status = 1

    #Info Account
    account_id = generatedIDforXML()[:8]
    account_status = 1

    #Info Comission
    merchant_comission = float(data['merchant_comission'])

    #Info Wallet
    wallet_usd = 'wusd' + generatedIDforXML()[:5]
    amount = float(0)

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500

    query = f"SELECT * FROM airtime_super_agent WHERE superAgent_code = '{merchant_recruter}'"

    details = executeQueryForGetData(conn, query)

    if len(details) <= 0:
        logger.warning(f"{merchant_recruter} recruter n'existe pas dans le systeme")
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed",
            "resultCodeError" : 2,
            "resultData" : {
                "merchant_code": merchant_recruter,
                "resultCodeErrorDescription" : "Le code du super agent n'existe pas dans le système"
            }
        }), 404

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500

    #Verification de la non existance du merchant_code dans le systeme
    query = f"SELECT * FROM airtime_merchant WHERE merchant_code = '{merchant_code}'"
    details = executeQueryForGetData(conn, query)
    ta = len(details)

    if ta > 0:
        logger.warning(f"{merchant_code} merchant de existe déjà dans le système")
        #writeLog("verify merchant_code", user, "Comment : Not Processed because merchant_code already exists")
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed",
            "resultCodeError" : 2,
            "resultData" : {
                "merchant_code": merchant_code,
                "resultCodeErrorDescription" : "Le code du merchant est déjà attribuer a un autre merchant dans le système"
            }
            }), 400

    #Fin de la Verification de la non existance du merchant_code dans le systeme

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500

    #Ajout du merchant dans le systeme
    createdAt = str(datetime.now())
    query = "INSERT INTO airtime_merchant(created_at, updated_at, merchant_code, merchant_secrete, merchant_id, merchant_name, merchant_email, merchant_phone, merchant_pass, superAgent_code) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    dataToInsert = (createdAt, createdAt, merchant_code, merchant_secrete, merchant_id, merchant_name, merchant_email, merchant_phone, merchant_pass, merchant_recruter)
    instertToMerchant = executeQueryForInsertDate(conn, query, dataToInsert)

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500

    queryCommission = "INSERT INTO airtime_comission(created_at,updated_at,merchant_code,comission) VALUES(%s, %s, %s, %s)"
    dataToInsertComission = (createdAt, createdAt, merchant_code, merchant_comission)
    instertToComission = executeQueryForInsertDate(conn, queryCommission, dataToInsertComission)

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500


    queryAccount = "INSERT INTO airtime_account(created_at, updated_at, account_id, merchant_code, `status`) VALUES(%s, %s, %s, %s, %s)"
    dataToInsertAccount = (createdAt, createdAt, account_id, merchant_code, account_status)
    instertToAccount = executeQueryForInsertDate(conn, queryAccount, dataToInsertAccount)

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500

    queryWallet = "INSERT INTO airtime_wallet(created_at, updated_at, wallet_code, account_id, currency, amount) VALUES(%s, %s, %s, %s, %s, %s)"
    dataToInsertWalletUsd = (createdAt, createdAt, wallet_usd, account_id, 'USD', amount)
    instertToWalletUsd = executeQueryForInsertDate(conn, queryWallet, dataToInsertWalletUsd)

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500

    queryUser = "INSERT INTO airtime_user(created_at, updated_at, firstname, lastname, password, niveau, status, institution_name, user_pin, fonction) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    dataToInsertUser = (createdAt, createdAt, merchant_user_firstname, merchant_user_lastname, merchant_user_password, "2", "1", merchant_code, merchant_user_pin, 'Agent')
    instertToUser = executeQueryForInsertDate(conn, queryUser, dataToInsertUser)

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500
    
    return jsonify({
        "Status" : "Success",
        "merchant_name" : merchant_name,
	    "merchant_email" : merchant_email,
	    "merchant_phone" : merchant_phone,
	    "merchant_code" : merchant_code,
	    "merchant_comission" : merchant_comission,
        "merchant_id" : merchant_id,
        "merchant_secret" : merchant_secrete_to_show,
        "account_id" : account_id,
        "wallet_usd" : wallet_usd,
        "merchant_pass" : merchant_pass,
        "merchant_user_admin_pin" : merchant_user_pin
    }), 200

    #Fin de l'Ajout du merchant dans le systeme

#Creation du merchant avec toutes ses informations
@airtime.route("/api/v1/superagent/create", methods=["POST"])
def createSuperAgent():
    errorList = {}
    error = ()
    parser = reqparse.RequestParser()
    parser.add_argument("superAgent_name", type = str)
    parser.add_argument("superAgent_email", type = str)
    parser.add_argument("superAgent_phone", type = str)
    parser.add_argument("superAgent_code", type = str)
    parser.add_argument("superAgent_user_firstname", type=str)
    parser.add_argument("superAgent_user_lastname", type=str)
    parser.add_argument("superAgent_user_password", type=str)

    data = parser.parse_args()
    #Info super Agent
    superAgent_name = data['superAgent_name']
    superAgent_email = data['superAgent_email']
    superAgent_phone = data['superAgent_phone']
    superAgent_code = data['superAgent_code']
    superAgent_user_firstname = data['superAgent_user_firstname']
    superAgent_user_lastname = data['superAgent_user_lastname']
    superAgent_user_password = data['superAgent_user_password']
    superAgent_user_pin = generatedPIN()

    #Info merchant generated
    superAgent_id = generatedID()
    superAgent_secrete_to_show = generatedIDforXML()
    superAgent_secrete = generate_password_hash(superAgent_secrete_to_show)
    superAgent_pass = generatedIDforXML()
    superAgent_status = 1

    #Info Account
    account_id = generatedIDforXML()[:8]
    account_status = 1


    #Info Wallet
    wallet_usd = 'wusd' + generatedIDforXML()[:5]
    amount = float(0)

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500

    #Verification de la non existance du superAgent_code dans le systeme
    query = f"SELECT * FROM airtime_super_agent WHERE superAgent_code = '{superAgent_code}'"
    details = executeQueryForGetData(conn, query)
    ta = len(details)

    if ta > 0:
        logger.warning(f"{superAgent_code} merchant de existe déjà dans le système")
        #writeLog("verify merchant_code", user, "Comment : Not Processed because merchant_code already exists")
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed",
            "resultCodeError" : 2,
            "resultData" : {
                "merchant_code": superAgent_code,
                "resultCodeErrorDescription" : "Le code du merchant est déjà attribuer a un autre merchant dans le système"
            }
            }), 400

    #Fin de la Verification de la non existance du merchant_code dans le systeme

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500

    #Ajout du merchant dans le systeme
    createdAt = str(datetime.now())
    query = "INSERT INTO airtime_super_agent(created_at, updated_at, superAgent_code, superAgent_secrete, superAgent_id, superAgent_name, superAgent_email, superAgent_phone, superAgent_pass) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    dataToInsert = (createdAt, createdAt, superAgent_code, superAgent_secrete, superAgent_id, superAgent_name, superAgent_email, superAgent_phone, superAgent_pass)
    instertToMerchant = executeQueryForInsertDate(conn, query, dataToInsert)

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500


    queryAccount = "INSERT INTO airtime_superagent_account(created_at, updated_at, account_id, superAgent_code, `status`) VALUES(%s, %s, %s, %s, %s)"
    dataToInsertAccount = (createdAt, createdAt, account_id, superAgent_code, account_status)
    instertToAccount = executeQueryForInsertDate(conn, queryAccount, dataToInsertAccount)

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500

    queryWallet = "INSERT INTO airtime_wallet(created_at, updated_at, wallet_code, account_id, currency, amount) VALUES(%s, %s, %s, %s, %s, %s)"
    dataToInsertWalletUsd = (createdAt, createdAt, wallet_usd, account_id, 'USD', amount)
    instertToWalletUsd = executeQueryForInsertDate(conn, queryWallet, dataToInsertWalletUsd)

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500

    queryUser = "INSERT INTO airtime_user(created_at, updated_at, firstname, lastname, password, niveau, status, institution_name, user_pin, fonction) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    dataToInsertUser = (createdAt, createdAt, superAgent_user_firstname, superAgent_user_lastname, superAgent_user_password, "1", "1", superAgent_code, superAgent_user_pin, 'Super Agent')
    instertToUser = executeQueryForInsertDate(conn, queryUser, dataToInsertUser)

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)

    if type(conn) == tuple:
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "Not Processed, database connexion failed !",
            "resultCodeError" : 2,
            "resultData" : {}
        }), 500
    
    return jsonify({
        "Status" : "Success",
        "super_agent_name" : superAgent_name,
	    "super_agent_email" : superAgent_email,
	    "super_agent_phone" : superAgent_phone,
	    "super_agent_code" : superAgent_code,
        "super_agent_id" : superAgent_id,
        "super_agent_secret" : superAgent_secrete_to_show,
        "account_id" : account_id,
        "wallet_usd" : wallet_usd,
        "super_agent_pass" : superAgent_pass,
        "super_agent_user_admin_pin" : superAgent_user_pin,
        "user_grant" : "Super Agent"
    }), 200

    #Fin de l'Ajout du merchant dans le systeme


@airtime.route("/api/v1/agent/verify", methods=["POST"])
def verifyMerchant():
    logger.info("VERIFICATION DE L'UNICITE DU MERCHANT_REF")
    parser = reqparse.RequestParser()
    parser.add_argument("merchant_code", type=str, help='Entrer le code de l\'institution')

    data = parser.parse_args() 
    merchant_code = data['merchant_code']

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    query = f"SELECT * FROM airtime_merchant WHERE merchant_code = '{merchant_code}'"
    details = executeQueryForGetData(conn, query)

    if len(details) == 0:
        return jsonify(
            resultCode=0,
            resultCodeDescription="Processed",
            resultData={}

        )

    return jsonify(
        resultCode=0,
        resultCodeDescription="Processed",
        resultData={
            "created_at" : str(details[0][1]),
            "updated_at" : str(details[0][2]),
            "merchant_id" : str(details[0][5]),
            "merchant_name" : str(details[0][6]),
            "merchant_code" : str(details[0][3]),
            "merchant_email" : str(details[0][7]),
            "merchant_phone" : str(details[0][8])
        }
    )

@airtime.route("/api/v1/merchant/user/create", methods = ["POST"])
def createUser():
    parser = reqparse.RequestParser()
    parser.add_argument("merchant_code", type=str)
    parser.add_argument("merchant_user_firstname", type=str)
    parser.add_argument("merchant_user_lastname", type=str)
    parser.add_argument("merchant_user_password", type=str)
    parser.add_argument("merchant_user_level", type=str)

    data = parser.parse_args() 

    merchant_code = data['merchant_code']
    merchant_user_firstname = data['merchant_user_firstname']
    merchant_user_lastname = data['merchant_user_lastname']
    merchant_user_password = data['merchant_user_password']
    merchant_user_level = data['merchant_user_level']
    merchant_user_pin = generatedPIN()

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    query = f"SELECT * FROM airtime_merchant WHERE merchant_code = '{merchant_code}'"
    details = executeQueryForGetData(conn, query)

    if len(details) == 0:
        return jsonify(
            resultCode=0,
            resultCodeDescription="Processed",
            resultData={}
        )
    
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    query = f"SELECT * FROM airtime_user WHERE firstname = '{merchant_user_firstname}' and lastname = '{merchant_user_lastname}'"
    details = executeQueryForGetData(conn, query)

    if len(details) > 0:
        return jsonify(
            resultCode=4,
            resultCodeDescription="Processed, user already exist",
            resultData={}
        )

    createdAt = str(datetime.now())
    queryUser = "INSERT INTO airtime_user(created_at, updated_at, firstname, lastname, password, niveau, status, institution_name, user_pin) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    dataToInsertUser = (createdAt, createdAt, merchant_user_firstname, merchant_user_lastname, merchant_user_password, merchant_user_level, "1", merchant_code, merchant_user_pin)
    instertToUser = executeQueryForInsertDate(conn, queryUser, dataToInsertUser)

    return jsonify({
        "Status" : "Success",
	    "merchant_code" : merchant_code,
        "merchant_user_firstname" : merchant_user_firstname,
        "merchant_user_lastname" : merchant_user_lastname,
        "merchant_user_level" : merchant_user_level,
        "merchant_user_password" : merchant_user_password,
        "merchant_user_pin" : merchant_user_pin
    }), 200
