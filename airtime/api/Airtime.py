from flask_restful import reqparse
import json
from flask import request, jsonify, Request
import requests
import math
import os, subprocess
from datetime import timedelta, datetime
import xmltodict
from xml.etree import ElementTree
from lxml import etree
""" from paydrc import app
from paydrc.api import payDrc_api
from paydrc.databases.Data import *
from paydrc.config.configurations import * """
from app import *
from api import airtime
from databases.Data import *
from config.configurations import *
import random
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

# Méthode affichant un message lors de l'expiration du token
@jwt.expired_token_loader
def my_expired_token_callback(expired_token):
    token_type = expired_token['type']
    logger.error("Le token {} a expiré".format(token_type))
    return errorMessage('tokenexpires')

@jwt.invalid_token_loader
def my_invalid_token_callback(invalid_token = "Invalid Signature"):
    logger.error("Le token est invalide")
    return errorMessage('tokeninvalid')
@jwt.unauthorized_loader

def my_unauthorized(unauthorized = "unauthorized"):
    logger.error("Le token est manquant")
    return errorMessage('tokenunauthorized')

# Méthode permettant la génération du FP (Identifiant unique pour chaque transaction)
def generatedFreshPayID(year, month, day):
    motifs = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    logger.info("GENERATION DU FPB")
    return 'PDA' + ''.join((random.choice(motifs)) for i in range(6)) + str(year) + ''.join((random.choice(motifs)) for j in range(5)) + str(month)+ ''.join((random.choice(motifs)) for k in range(6)) + str(day)+ ''.join((random.choice(motifs)) for l in range(5))


#Endpoint pour lancer les requetes surt le payDrc v2
@airtime.route("/api/v1", methods=["POST"])
#@jwt_required
def createTransaction():
    #Parser Pour recuperer les arguments (Parametres)
    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument("action", type=str, required=True, help="This field is required to complete a transaction")
    data = parser.parse_args()

    action = data['action'].lower()

    #Verification de l'action a executer
    if action == 'credit':
        #Appel de l'action permettant de faire un credit
        return makeCredit()
    elif action == 'verify':
        #Appel de l'action permettant de verifier l'etat d'une transaction
        return verifyTransaction()
    elif action == 'confirmation':
        #Appel de l'action permettant de confirmer l'envoie du cash
        return validateCash()
    else:
        #Action non reconnue
        return errorMessage('action')

#Methode verifiant l'erreur lieer a la connexion a la base des donnees
def errorConnectBDD(conn):
    if type(conn) == tuple:
        logger.info("Probleme de connexion a la base de donnee")
        return errorMessage('database')

#Methode permettant d'effectuer les operation sur le wallet
def makeTransaction(action, amount, wallet_code, merchant_code, reference, currency, method, customer_number, payDrcId, callback_url):
    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)
    #Requete de selection du wallet
    query = f"SELECT * FROM airtime_wallet WHERE wallet_code = '{wallet_code}'"
    details = executeQueryForGetData(conn, query)

    if len(details) == 0:
        return errorMessage('notfoundwallet')
    #Information du montant actuel du wallet du merchant
    wallet_current_amount = float(details[0][6])
    #Verification de l'action a utilisee
    if action == 'credit':
        amount_to_credit = float(amount)
        #Verification de la balance
        if amount_to_credit > wallet_current_amount :
            #Balance insuffisante
            #Connexion a la base de donnees
            status = 'Failed'
            status_description = 'merchant wallet balance insufficient'
            conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
            errorConnectBDD(conn)
            #Requete d'ajout de la transaction dans la base de donnees
            query = "INSERT INTO airtime_transaction(created_at, updated_at, merchant_code, thirdparty_reference, currency, amount, method, action, customer_details, status, saledrc_reference, callback_url, status_description) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            createdAt = str(datetime.now())
            dataToInsert = (createdAt, createdAt, merchant_code, reference, currency, amount, method, action, customer_number, status, payDrcId, callback_url, status_description)
            #Execution de la requete d'ajout de la transaction
            instertToSwitch = executeQueryForInsertDate(conn, query, dataToInsert)
            #Verification de l'execution de la requete
            return jsonify({
                "Status": "Success",
                "Comment": "Transaction Received Successfully",
                "Reference" : reference,
                "Customer_Number" : customer_number,   
                "Amount" : amount,
                "Currency" : currency,
                "Created_At" : createdAt,
                "Updated_At" : createdAt,
                "Transaction_id" : payDrcId,
                "Transaction_Status" : status,
                "Transaction_Status_Description" : status_description

            }), 200
            #return errorMessage('insufficient')
        #Balance suffisante
        wallet_current_amount = wallet_current_amount -  amount_to_credit

    #Temps de mise a jour
    date_updated = str(datetime.now())
    #Requete de mise a jour du wallet
    query = f"UPDATE airtime_wallet SET updated_at = '{date_updated}', amount = {wallet_current_amount} WHERE wallet_code = '{wallet_code}'"
    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)
    #Execution de la requete
    updateToSwitch = executeQueryForUpdate(conn, query)
    #Verification du resultat de lexecution
    if updateToSwitch == 1:
        #Wallet mise a jour
        logger.info(f"Wallet {wallet_code} updated to {wallet_current_amount}") 
    else:
        #Wallet non mise a jour
        logger.info(f"Wallet {wallet_code} not updated")
    
    return updateToSwitch

#Methode permettant d'effectuer une operation de remise en cas d'echec de la transaction
def returnTransaction(merchant_code, amount):
    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)
    #Requete de selection
    query1 = f"SELECT * FROM airtime_check_auth WHERE merchant_code = '{merchant_code}' and currency = 'USD' and status = 1 and wallet_code like 'wusd%'"
    details1 = executeQueryForGetData(conn, query1)

    #Verification de l'existance d'une ligne dans la base de donnees
    #Prouvant l'existance du marchand
    if len(details1) == 0:
        return errorMessage('notfoundmerchant')

    wallet_code = details1[0][6]
    #Information du montant actuel du wallet du merchant
    wallet_current_amount = float(details1[0][8])

    wallet_current_amount = wallet_current_amount +  amount

    #Temps de mise a jour
    date_updated = str(datetime.now())
    #Requete de mise a jour du wallet
    query = f"UPDATE airtime_wallet SET updated_at = '{date_updated}', amount = {wallet_current_amount} WHERE wallet_code = '{wallet_code}'"
    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)
    #Execution de la requete
    updateToSwitch = executeQueryForUpdate(conn, query)
    #Verification du resultat de lexecution
    if updateToSwitch == 1:
        #Wallet mise a jour
        logger.info(f"Wallet {wallet_code} updated to {wallet_current_amount}") 
    else:
        #Wallet non mise a jour
        logger.info(f"Wallet {wallet_code} not updated")
    
    return updateToSwitch

#Methode permettant de valider le paiement cash
def validateCash():
    #Parser pour recuperer les arguments (parametres)
    parser = reqparse.RequestParser()
    parser.add_argument("action", type=str)
    parser.add_argument("reference", type=str)
    parser.add_argument("callback_url", type=str)
    parser.add_argument("merchant_pass", type=str)

    data = parser.parse_args()
    action = data['action']
    reference = data['reference']
    callback_url = data['callback_url']
    merchant_pass = data['merchant_pass']

    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)
    #Reauete de selection des informations generales pour envoyer des requetes au switch
    query = f"SELECT * FROM airtime_parameters"
    #Execution de la requete
    details = executeQueryForGetData(conn, query)
    #Verification de l'existance des parametres
    if len(details) == 0:
        logger.error("Erreur liee a l'execution de la requete dans la base de donnees")
        return errorMessage('general')
    #Informations liee a l'envoie des requetes au switch
    #Code Middleware - Switch
    switch_code = details[0][1]
    #Secrete Middleware - Switch
    switch_key = details[0][2]
    #Token Middleware - Switch
    switch_token = details[0][3]

    if len(reference) > 30:
        return errorMessage('reference')

    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)
    #Requete de selection
    query1 = f"SELECT * FROM airtime_check_auth WHERE merchant_pass = '{merchant_pass}' and currency = 'USD' and status = 1 and wallet_code like 'wusd%'"
    details1 = executeQueryForGetData(conn, query1)

    #Verification de l'existance d'une ligne dans la base de donnees
    #Prouvant l'existance du marchand
    if len(details1) == 0:
        return errorMessage('notfoundmerchant')
    #Recuperation des informations liee au marchant trouve
    merchant_code = details1[0][2]
    merchant_account = str(details1[0][4])
    
    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)

    query = f"SELECT * FROM airtime_transaction WHERE (thirdparty_reference = '{reference}' or saledrc_reference = '{reference}' or swicth_reference = '{reference}') and status = 'InProcess'"
    details = executeQueryForGetData(conn, query)

    if len(details) == 0:
        return jsonify({
            "Status":"Success",
            "Comment":"Transaction Not Found",
            "Trans_Status":"xxxxxx",
            "Currency":"xxxxxx",
            "Amount":"xxxxxx",
            "Method":"xxxxxx",
            "Customer_Details":"xxxxxx",
            "Reference":f"{reference}",
            "Action":"xxxx",
            "Created_At" : "xxxxx",
            "Updated_At" : "xxxxx",
            "Trans_Status_Description" : "xxxxx",
            "Financial_Institution_id" : "xxxxx"
        }), 200
    
    customer_number = str(details[0][6])
    currency = str(details[0][4])
    merchant_ref = str(details[0][10])
    amount = float(details[0][5])
    vendor = str(details[0][7])

    if vendor == 'mpesa':
        vendor = 'vodacom'
    

    #Donnees a envoyer au Switch
    dataToSend = {
        "action":"payout",
        "credit_channel": f"{vendor}",
        "credit_account": f"{customer_number}", 
        "amount": amount,
        "currency": f"{currency}",
        "merchant_code": f"{switch_code}",
        "key": f"{switch_key}",
        "merchant_ref" : f"{merchant_ref}",
        "callback_url" : ""
    }
    result = sendDepositToSwitch(dataToSend, switch_token, "http://161.35.208.97:2801/api/v1")
    logger.info(result)
    return result


#Methode permettant d'effectuer un credit de compte
def makeCredit():
    #Parser pour recuperer les arguments (parametres)
    parser = reqparse.RequestParser()
    parser.add_argument("amount", type=str)
    parser.add_argument("currency", type=str)
    parser.add_argument("action", type=str)
    parser.add_argument("customer_number", type=str)
    parser.add_argument("reference", type=str)
    parser.add_argument("method", type=str)
    parser.add_argument("callback_url", type=str)
    parser.add_argument("merchant_pass", type=str)
    parser.add_argument("source_customer_number", type=str)
    parser.add_argument("payment_method", type=str)
    parser.add_argument("user_pin", type=str)

    data = parser.parse_args()
    amount = float(data['amount'])
    currency = data['currency']
    action = data['action']
    customer_number = data['customer_number']
    reference = data['reference']
    method = data['method']
    callback_url = data['callback_url']
    merchant_pass = data['merchant_pass']
    source_customer_number = data['source_customer_number']
    payment_method = data['payment_method']
    user_pin = data['user_pin']
    status = "Submitted"
    status_description = ''

    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)
    #Reauete de selection des informations generales pour envoyer des requetes au switch
    query = f"SELECT * FROM airtime_parameters"
    #Execution de la requete
    details = executeQueryForGetData(conn, query)
    #Verification de l'existance des parametres
    if len(details) == 0:
        logger.error("Erreur liee a l'execution de la requete dans la base de donnees")
        return errorMessage('general')

    #Informations liee a l'envoie des requetes au switch
    #Code Middleware - Switch
    switch_code = details[0][1]
    #Secrete Middleware - Switch
    switch_key = details[0][2]
    #Token Middleware - Switch
    switch_token = details[0][3]

    #Verification du la methode de paiement
    if payment_method == 'Cash' or payment_method == 'cash':
        #status = 'InProcess'
        status_description = 'Submitted by cash'
    elif payment_method == 'MOMO' or payment_method == 'momo':
        status_description = 'Pending for Payement Gateway Confirmation'

    #Verification de la limit de paiement automatique
    if amount > 500:
        return errorMessage('limit')
    #Verification de la devise
    if currency != 'USD':
        return errorMessage('devise')
    #Verfification de la refence
    if len(reference) > 30:
        return errorMessage('reference')

    if method != 'mpesa' and method != 'orange' and method != 'airtel':
        return errorMessage('method')

    amount = float(amount)

    #Verification de l'operateur
    if method == 'mpesa':
        vendor = 'vodacom'
        if len(customer_number) == 9:
            if customer_number[0:2] != '81' and customer_number[0:2] != '82':
                return errorMessage('method1')
            customer_number = '243' + str(customer_number[1:])

        if len(customer_number) == 10:
            if customer_number[0] == '0':
                customer_number = '243' + str(customer_number[1:])
            elif customer_number[0:1] != '0':
                return errorMessage('method2')
           
        if len(customer_number) < 9 or len(customer_number) > 12:
            return errorMessage('method3')

        if len(customer_number) == 12:
            if customer_number[0:3] != '243':
                return errorMessage('method2')

            if customer_number[3:5] != '81' and customer_number[3:5] != '82':
                return errorMessage('method1')
    
    if method == 'orange':
        vendor = 'orange'
        if len(customer_number) == 9:
            if customer_number[0:2] != '85' and customer_number[0:2] != '84' and customer_number[0:2] != '89' and customer_number[0:2] != '80':
                return errorMessage('method1')
            customer_number = '0' + str(customer_number[1:])

        if len(customer_number) == 10:
            if customer_number[0] == '0':
                customer_number =  str(customer_number)
            elif customer_number[0:1] != '0':
                return errorMessage('method2')
           
        if len(customer_number) < 9 or len(customer_number) > 12:
            return errorMessage('method3')

        if len(customer_number) == 12:
            if customer_number[0:3] != '243':
                return errorMessage('method2')

            if customer_number[3:5] != '85' and customer_number[3:5] != '84' and customer_number[3:5] != '89' and customer_number[0:2] != '80':
                return errorMessage('method1')
            customer_number = '0' + str(customer_number[3:])
    
    if method == 'airtel':
        vendor = 'airtel'
        if len(customer_number) == 9:
            if customer_number[0:2] != '99' and customer_number[0:2] != '97':
                return errorMessage('method1')
            customer_number = str(customer_number[1:])

        if len(customer_number) == 10:
            if customer_number[0] == '0':
                customer_number =  str(customer_number[1:])
            elif customer_number[0:1] != '0':
                return errorMessage('method2')
           
        if len(customer_number) < 9 or len(customer_number) > 12:
            return errorMessage('method3')

        if len(customer_number) == 12:
            if customer_number[0:3] != '243':
                return errorMessage('method2')

            if customer_number[3:5] != '99' and customer_number[3:5] != '97':
                return errorMessage('method1')
            customer_number = str(customer_number[3:])
    
    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)
    #Requete de selection
    query1 = f"SELECT * FROM airtime_check_auth WHERE merchant_pass = '{merchant_pass}' and currency = 'USD' and status = 1 and wallet_code like 'wusd%'"
    details1 = executeQueryForGetData(conn, query1)

    #Verification de l'existance d'une ligne dans la base de donnees
    #Prouvant l'existance du marchand
    if len(details1) == 0:
        return errorMessage('notfoundmerchant')
    
    #Ajouter le numero de la colonne 
    """ if check_password_hash() != True:
        logger.info("Secrete incorret")
        return jsonify({
            "Message" : "Secrete du merchant incorrect"
        }), 400
     """
    #Recuperation des informations liee au marchant trouve
    merchant_code = details1[0][2]
    merchant_account = str(details1[0][4])
    
    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)

    wallet_code = details1[0][6]

    #Les varaibles permettant de generer les fp du paydrc
    year = str(datetime.now().year)[2:4]
    month = str(datetime.now().month)
    if len(month) == 1:
        month = str("0") + month
    day = str(datetime.now().day)
    if len(day) == 1:
        day = str("0") + day
    #Paydrc fp
    payDrcId = generatedFreshPayID(year=year, month=month, day=day)
    #Operation sur le wallet 
    resul = makeTransaction(action, amount, wallet_code, merchant_code, reference, currency, method, customer_number, payDrcId, callback_url)
    #Verification du resultat
    if type(resul) != int:
        #Erreur survenue liee a la balance ou wallet
        return resul
    elif type(resul) == int:
        #Erreur liee a la base de donnees, requete mal execute
        if resul == 0:
            logger.error("Erreur lors de l'execution de la requete dans la base de donnes")
            return errorMessage('general')
    
    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)
    #Requete d'ajout de la transaction dans la base de donnees
    query = "INSERT INTO airtime_transaction(created_at, updated_at, merchant_code, thirdparty_reference, currency, amount, method, action, customer_details, status, saledrc_reference, callback_url, source_customer_details, payment_method, status_description, user_pin) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    createdAt = str(datetime.now())
    dataToInsert = (createdAt, createdAt, merchant_code, reference, currency, amount, method, action, customer_number, status, payDrcId, callback_url, source_customer_number, payment_method, status_description, user_pin)
    #Execution de la requete d'ajout de la transaction
    instertToSwitch = executeQueryForInsertDate(conn, query, dataToInsert)
    #Verification de l'execution de la requete
    if instertToSwitch == 0:
        logger.error("Erreur liee a l'execution de la requete dans la base de donnees")
        return errorMessage('general')
    
    #Donnees a envoyer au Switch
    dataToSend = {
        "action":"payout",
        "credit_channel": f"{vendor}",
        "credit_account": f"{customer_number}", 
        "amount": amount,
        "currency": f"{currency}",
        "merchant_code": f"{switch_code}",
        "key": f"{switch_key}",
        "merchant_ref" : f"{payDrcId}",
        "callback_url" : ""
    }

    #Verification du moyen de paiement
    if payment_method == 'Cash' or payment_method == 'cash' or payment_method == 'MOMO' or payment_method == 'momo':
        #Envoie de la requete au Switch
        logger.info(sendDepositToSwitch(dataToSend, switch_token, "http://161.35.208.97:2801/api/v1"))
        """
        if vendor == 'vodacom':
            #logger.info(sendDepositToSwitch(dataToSend, switch_token, "http://34.76.48.90:2801/api/v1/payouts"))
            logger.info(sendDepositToSwitch(dataToSend, switch_token, "http://127.0.0.1:2801/api/v1/payouts"))
        elif vendor == 'orange':
            logger.info(sendDepositToSwitch(dataToSend, switch_token, "http://35.233.0.76:2801/api/v1/payouts"))
            writeLog("successful transaction", user, f"{dataToSend}")
        elif vendor == 'airtel':
            logger.info(sendDepositToSwitch(dataToSend, switch_token, "http://104.199.107.2:2801/api/v1/payouts"))
            writeLog("successful transaction", user, f"{dataToSend}")
        """
    return jsonify({
        "Status": "Success",
        "Comment": "Transaction Received Successfully",
        "Reference" : reference,
        "Customer_Number" : customer_number,
        "Amount" : amount,
        "Currency" : currency,
        "Created_At" : createdAt,
        "Updated_At" : createdAt,
        "Transaction_id" : payDrcId,
    }), 200

#Methode permettant d'effectuer un credit de compte
@airtime.route("/api/v1/agent", methods=["POST"])
def makeCreditAgent():
    #Parser pour recuperer les arguments (parametres)
    parser = reqparse.RequestParser()
    parser.add_argument("amount", type=str)
    parser.add_argument("currency", type=str)
    parser.add_argument("action", type=str)
    parser.add_argument("customer_number", type=str)
    parser.add_argument("reference", type=str)
    parser.add_argument("method", type=str)
    parser.add_argument("callback_url", type=str)
    parser.add_argument("merchant_pass", type=str)
    parser.add_argument("source_customer_number", type=str)
    parser.add_argument("payment_method", type=str)
    parser.add_argument("user_pin", type=str)

    data = parser.parse_args()
    amount = float(data['amount'])
    currency = data['currency']
    action = data['action']
    customer_number = data['customer_number']
    reference = data['reference']
    method = data['method']
    callback_url = data['callback_url']
    merchant_pass = data['merchant_pass']
    source_customer_number = data['source_customer_number']
    payment_method = data['payment_method']
    user_pin = data['user_pin']
    status = "Submitted"
    status_description = ''

    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)
    #Reauete de selection des informations generales pour envoyer des requetes au switch
    query = f"SELECT * FROM airtime_parameters"
    #Execution de la requete
    details = executeQueryForGetData(conn, query)
    #Verification de l'existance des parametres
    if len(details) == 0:
        logger.error("Erreur liee a l'execution de la requete dans la base de donnees")
        return errorMessage('general')

    #Informations liee a l'envoie des requetes au switch
    #Code Middleware - Switch
    switch_code = details[0][1]
    #Secrete Middleware - Switch
    switch_key = details[0][2]
    #Token Middleware - Switch
    switch_token = details[0][3]

    #Verification du la methode de paiement
    if payment_method == 'Cash' or payment_method == 'cash':
        #status = 'InProcess'
        status_description = 'Submitted by cash'
    elif payment_method == 'MOMO' or payment_method == 'momo':
        status_description = 'Pending for Payement Gateway Confirmation'

    #Verification de la limit de paiement automatique
    if amount > 500:
        return errorMessage('limit')
    #Verification de la devise
    if currency != 'USD':
        return errorMessage('devise')
    #Verfification de la refence
    if len(reference) > 30:
        return errorMessage('reference')

    if method != 'mpesa' and method != 'orange' and method != 'airtel':
        return errorMessage('method')

    amount = float(amount)

    #Verification de l'operateur
    if method == 'mpesa':
        vendor = 'vodacom'
        if len(customer_number) == 9:
            if customer_number[0:2] != '81' and customer_number[0:2] != '82':
                return errorMessage('method1')
            customer_number = '243' + str(customer_number[1:])

        if len(customer_number) == 10:
            if customer_number[0] == '0':
                customer_number = '243' + str(customer_number[1:])
            elif customer_number[0:1] != '0':
                return errorMessage('method2')
           
        if len(customer_number) < 9 or len(customer_number) > 12:
            return errorMessage('method3')

        if len(customer_number) == 12:
            if customer_number[0:3] != '243':
                return errorMessage('method2')

            if customer_number[3:5] != '81' and customer_number[3:5] != '82':
                return errorMessage('method1')
    
    if method == 'orange':
        vendor = 'orange'
        if len(customer_number) == 9:
            if customer_number[0:2] != '85' and customer_number[0:2] != '84' and customer_number[0:2] != '89' and customer_number[0:2] != '80':
                return errorMessage('method1')
            customer_number = '0' + str(customer_number[1:])

        if len(customer_number) == 10:
            if customer_number[0] == '0':
                customer_number =  str(customer_number)
            elif customer_number[0:1] != '0':
                return errorMessage('method2')
           
        if len(customer_number) < 9 or len(customer_number) > 12:
            return errorMessage('method3')

        if len(customer_number) == 12:
            if customer_number[0:3] != '243':
                return errorMessage('method2')

            if customer_number[3:5] != '85' and customer_number[3:5] != '84' and customer_number[3:5] != '89' and customer_number[0:2] != '80':
                return errorMessage('method1')
            customer_number = '0' + str(customer_number[3:])
    
    if method == 'airtel':
        vendor = 'airtel'
        if len(customer_number) == 9:
            if customer_number[0:2] != '99' and customer_number[0:2] != '97':
                return errorMessage('method1')
            customer_number = str(customer_number[1:])

        if len(customer_number) == 10:
            if customer_number[0] == '0':
                customer_number =  str(customer_number[1:])
            elif customer_number[0:1] != '0':
                return errorMessage('method2')
           
        if len(customer_number) < 9 or len(customer_number) > 12:
            return errorMessage('method3')

        if len(customer_number) == 12:
            if customer_number[0:3] != '243':
                return errorMessage('method2')

            if customer_number[3:5] != '99' and customer_number[3:5] != '97':
                return errorMessage('method1')
            customer_number = str(customer_number[3:])
    
    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)
    #Requete de selection
    query1 = f"SELECT * FROM airtime_check_auth_super_agent WHERE merchant_pass = '{merchant_pass}' and currency = 'USD' and status = 1 and wallet_code like 'wusd%'"
    details1 = executeQueryForGetData(conn, query1)

    #Verification de l'existance d'une ligne dans la base de donnees
    #Prouvant l'existance du marchand
    if len(details1) == 0:
        return errorMessage('notfoundmerchant')
    
    #Ajouter le numero de la colonne 
    """ if check_password_hash() != True:
        logger.info("Secrete incorret")
        return jsonify({
            "Message" : "Secrete du merchant incorrect"
        }), 400
     """
    #Recuperation des informations liee au marchant trouve
    merchant_code = details1[0][3]
    merchant_account = str(details1[0][5])
    
    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)

    wallet_code = details1[0][7]

    #Les varaibles permettant de generer les fp du paydrc
    year = str(datetime.now().year)[2:4]
    month = str(datetime.now().month)
    if len(month) == 1:
        month = str("0") + month
    day = str(datetime.now().day)
    if len(day) == 1:
        day = str("0") + day
    #Paydrc fp
    payDrcId = generatedFreshPayID(year=year, month=month, day=day)
    #Operation sur le wallet 
    resul = makeTransaction(action, amount, wallet_code, merchant_code, reference, currency, method, customer_number, payDrcId, callback_url)
    #Verification du resultat
    if type(resul) != int:
        #Erreur survenue liee a la balance ou wallet
        return resul
    elif type(resul) == int:
        #Erreur liee a la base de donnees, requete mal execute
        if resul == 0:
            logger.error("Erreur lors de l'execution de la requete dans la base de donnes")
            return errorMessage('general')
    
    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)
    #Requete d'ajout de la transaction dans la base de donnees
    query = "INSERT INTO airtime_transaction(created_at, updated_at, merchant_code, thirdparty_reference, currency, amount, method, action, customer_details, status, saledrc_reference, callback_url, source_customer_details, payment_method, status_description, user_pin) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    createdAt = str(datetime.now())
    dataToInsert = (createdAt, createdAt, merchant_code, reference, currency, amount, method, action, customer_number, status, payDrcId, callback_url, source_customer_number, payment_method, status_description, user_pin)
    #Execution de la requete d'ajout de la transaction
    instertToSwitch = executeQueryForInsertDate(conn, query, dataToInsert)
    #Verification de l'execution de la requete
    if instertToSwitch == 0:
        logger.error("Erreur liee a l'execution de la requete dans la base de donnees")
        return errorMessage('general')
    
    #Donnees a envoyer au Switch
    dataToSend = {
        "action":"payout",
        "credit_channel": f"{vendor}",
        "credit_account": f"{customer_number}", 
        "amount": amount,
        "currency": f"{currency}",
        "merchant_code": f"{switch_code}",
        "key": f"{switch_key}",
        "merchant_ref" : f"{payDrcId}",
        "callback_url" : ""
    }

    #Verification du moyen de paiement
    if payment_method == 'Cash' or payment_method == 'cash' or payment_method == 'MOMO' or payment_method == 'momo':
        #Envoie de la requete au Switch
        logger.info(sendDepositToSwitch(dataToSend, switch_token, "http://161.35.208.97:2801/api/v1"))
        """
        if vendor == 'vodacom':
            #logger.info(sendDepositToSwitch(dataToSend, switch_token, "http://34.76.48.90:2801/api/v1/payouts"))
            logger.info(sendDepositToSwitch(dataToSend, switch_token, "http://127.0.0.1:2801/api/v1/payouts"))
        elif vendor == 'orange':
            logger.info(sendDepositToSwitch(dataToSend, switch_token, "http://35.233.0.76:2801/api/v1/payouts"))
            writeLog("successful transaction", user, f"{dataToSend}")
        elif vendor == 'airtel':
            logger.info(sendDepositToSwitch(dataToSend, switch_token, "http://104.199.107.2:2801/api/v1/payouts"))
            writeLog("successful transaction", user, f"{dataToSend}")
        """
    return jsonify({
        "Status": "Success",
        "Comment": "Transaction Received Successfully",
        "Reference" : reference,
        "Customer_Number" : customer_number,
        "Amount" : amount,
        "Currency" : currency,
        "Created_At" : createdAt,
        "Updated_At" : createdAt,
        "Transaction_id" : payDrcId,
    }), 200


#Methode permattant de communiquer avec le switch    
def sendDepositToSwitch(data, token, endpoints):
    logger.info("REQUEST SEND TO SWITCH")
    logger.info(data)
    #Le Endpoint du switch
    endpoint = endpoints
    #Les headers
    headers = {"Content-Type" : "application/json", "Authorization": "Bearer " + token}
    #Envoie de la requete par post
    response = requests.post(url=endpoint, headers=headers, data=json.dumps(data))
    response_dict = response.json()

    status = response_dict['status']
    merchant_ref = response_dict['merchant_ref']
    switch_reference = response_dict['trans_id']
    status_description = response_dict['resultDescription']

    logger.info(f"Incomming callback from switch for {merchant_ref}")
    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)
    #Requete de selection
    query1 = f"SELECT * FROM airtime_transaction WHERE saledrc_reference = '{merchant_ref}'"
    details1 = executeQueryForGetData(conn, query1)

    #Verification de l'existance d'une ligne dans la base de donnees
    #Prouvant l'existance du marchand
    if len(details1) == 0:
        return errorMessage('notfoundtransaction')
    
    customer_number = str(details1[0][6])
    amount = float(details1[0][5])
    currency = str(details1[0][4])
    createdAt = str(details1[0][1])
    update = str(details1[0][2])
    merchant_code = str(details1[0][3])
    #Temps de mise a jour
    date_updated = str(datetime.now())
    #Requete de mise a jour
    query = f"UPDATE airtime_transaction SET updated_at = '{date_updated}', status = '{status}', swicth_reference = '{switch_reference}', status_description = '{status_description}' WHERE saledrc_reference = '{merchant_ref}'"
    #Connexion a la base de donnees
    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    errorConnectBDD(conn)
    #Execution de la requete
    updateToSwitch = executeQueryForUpdate(conn, query)

    merchant_ref = str(details1[0][14])
    logger.info("Callback terminated !!")

    if status == 'Failed':
        returnFounds = returnTransaction(merchant_code, amount)

    
    if updateToSwitch == 1:
        return jsonify({
            "Status": "Success",
            "Comment": "Transaction Received Successfully",
            "Reference" : merchant_ref,
            "Customer_Number" : customer_number,
            "Amount" : amount,
            "Currency" : currency,
            "Created_At" : createdAt,
            "Updated_At" : update,
            "Transaction_id" : merchant_ref,
            "Transaction_Status" : status,
            "Transaction_Status_Description" : status_description
        }), 200


#Methode permettant de faire le verify d'une transaction
def verifyTransaction():
    parser = reqparse.RequestParser(bundle_errors=True)
    parser.add_argument("action", type=str, required=True, help='This field is required to complete a transaction')
    parser.add_argument("reference", type=str, required=True, help='This field is required to complete a transaction')

    data = parser.parse_args()
    action = data['action']
    reference = data['reference']

    conn = connectToDatabase(host=host, user=user, password=password, db=database, port=port)
    query = f"SELECT * FROM airtime_transaction WHERE thirdparty_reference = '{reference}' or saledrc_reference = '{reference}'"
    details = executeQueryForGetData(conn, query)

    if len(details) == 0:
        return jsonify({
            "Status":"Success",
            "Comment":"Transaction Not Found",
            "Trans_Status":"xxxxxx",
            "Currency":"xxxxxx",
            "Amount":"xxxxxx",
            "Method":"xxxxxx",
            "Customer_Details":"xxxxxx",
            "Reference":"xxxxxx",
            "Action":"xxxx",
            "Created_At" : "xxxxx",
            "Updated_At" : "xxxxx",
            "Trans_Status_Description" : "xxxxx",
            "Financial_Institution_id" : "xxxxx"
        }), 200
   
    return jsonify({
        "Status": "Success",
        "Comment": "Transaction Found",
        "Trans_Status" : str(details[0][9]),        
        "Currency" : str(details[0][4]),
        "Amount" : float(details[0][5]),
        "Method" : str(details[0][7]),   
        "Customer_Details" : str(details[0][6]),
        "Reference" : str(details[0][14]),             
        "Transaction_id" : str(details[0][10]),
        "Action" : str(details[0][8]),
        "Created_at" : str(details[0][1]),
        "Updated_at" : str(details[0][2]),
        "Trans_Status_Description" : str(details[0][13]),
        "Financial_Institution_id" : str(details[0][12])
    }), 200
