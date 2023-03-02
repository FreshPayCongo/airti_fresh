from flask import jsonify

env = 'production'

if env == 'development':
    host = '142.93.114.29'
    port = 25060
    user = 'doadmin'
    database = 'defaultdb'
    password = 'AVNS_00maw16Ps51dp7xAbHL'
elif env == 'production':
    host = '142.93.114.29'
    port = 25060
    user = 'doadmin'
    database = 'defaultdb'
    password = 'AVNS_00maw16Ps51dp7xAbHL'

def errorMessage(typeOfError):
    if typeOfError == 'database':
        return jsonify({
            "resultCode": 0,
            "resultCodeDescription" : "request successfully executed",
            "resultCodeError" : 409,
            "resultCodeErrorDescription" : "connectivity problem with the database...",
            "resultData" : {}
        }), 409
    elif typeOfError == 'action':
        return jsonify({
            "Status":"Error",
            "Comment":"Invalid Transaction Channel. Please Refer To Documentation",
            "resultCode": 1,
            "resultCodeDescription" : "request not executed...",
            "resultCodeError" : 408,
            "resultCodeErrorDescription" : "action not recognized by the system..."
        }), 408
    elif typeOfError == 'method':
        return jsonify({
            "Status":"Error",
            "Comment":"Invalid Transaction operator. Please Refer To Documentation",
            "resultCode": 1,
            "resultCodeDescription" : "request not executed...",
            "resultCodeError" : 408,
            "resultCodeErrorDescription" : "method not recognized by the system..."
        }), 408
    elif typeOfError == 'devise':
        return jsonify({
            "Status":"Error",
            "Comment":"Invalid Currency Value. Can Only Be USD",
            "resultCode": 1,
            "resultCodeDescription" : "request not executed...",
            "resultCodeError" : 407,
            "resultCodeErrorDescription" : "incorrect or unrecognized currency..."
        }), 407
    elif typeOfError == 'reference':
        return jsonify({
            "Status":"Error",
            "Comment":"the third party reference must have a maximum of 20 characters and minimum of 6 characters",            
            "resultCode": 1,
            "resultCodeDescription" : "request not executed...",
            "resultCodeError" : 406,
            "resultCodeErrorDescription" : "the third party reference must have a maximum of 20 characters and minimum of 6 characters..."
        }), 406
    elif typeOfError == 'method1':
        return jsonify({
            "Status":"Error",
            "Comment":"the network indicator does not match",             
            "resultCode": 1,
            "resultCodeDescription" : "request not executed...",
            "resultCodeError" : 405,
            "resultCodeErrorDescription" : "the network indicator does not match..."
        }), 405
    elif typeOfError == 'method2':
        return jsonify({
            "Status":"Error",
            "Comment":"country flag is not allowed",              
            "resultCode": 1,
            "resultCodeDescription" : "request not executed...",
            "resultCodeError" : 405,
            "resultCodeErrorDescription" : "country flag is not allowed..."
        }), 405
    elif typeOfError == 'method3':
        return jsonify({
            "Status":"Error",
            "Comment":"Customer number is incorrect, be sure to start with 243",              
            "resultCode": 1,
            "resultCodeDescription" : "request not executed...",
            "resultCodeError" : 405,
            "resultCodeErrorDescription" : "Customer number is incorrect, be sure to start with 243..."
        }), 405
    elif typeOfError == 'notfoundmerchant':
        return jsonify({
            "Status":"Error",
            "Comment":"your merchant identifier not recognized in the system",              
            "resultCode": 1,
            "resultCodeDescription" : "request not executed...",
            "resultCodeError" : 404,
            "resultCodeErrorDescription" : "your merchant identifier not recognized in the system...",
            "resultData" : {}
        }), 404
    elif typeOfError == 'notfounduser':
        return jsonify({
            "Status":"Error",
            "Comment":"user information was not found in the system or either the user does not have the required level of authorization to perform this request",  
            "resultCode": 0,
            "resultCodeDescription" : "request successfully executed...",
            "resultCodeError" : 404,
            "resultCodeErrorDescription" : "user information was not found in the system or either the user does not have the required level of authorization to perform this request..."
        }), 404
    elif typeOfError == 'notfoundwallet':
        return jsonify({
            "Status":"Error",
            "Comment":"the wallet identifier is not recognized in the system",  
            "resultCode": 0,
            "resultCodeDescription" : "request successfully executed...",
            "resultCodeError" : 404,
            "resultCodeErrorDescription" : "the wallet identifier is not recognized in the system..."
        }), 404
    elif typeOfError == 'notfoundtransaction':
        return jsonify({
            "Status":"Error",
            "Comment":"the transaction identifier is not recognized in the system",  
            "resultCode": 0,
            "resultCodeDescription" : "request successfully executed...",
            "resultCodeError" : 404,
            "resultCodeErrorDescription" : "the transaction identifier is not recognized in the system..."
        }), 404
    elif typeOfError == 'insufficient':
        return jsonify({
            "resultCode": 0,
            "resultCodeDescription" : "request successfully executed...",
            "resultCodeError" : 402,
            "resultCodeErrorDescription" : "your balance is insufficient to make this payment...",
            "resultData" : {}
        }), 402
    elif typeOfError == 'limit':
        return jsonify({
            "resultCode": 1,
            "resultCodeDescription" : "request not executed...",
            "resultCodeError" : 401,
            "resultCodeErrorDescription" : "you cannot make a payment of this amount...",
            "resultData" : {}
        }), 401
    elif typeOfError == 'general':
        return jsonify({
            "Status":"Error",
            "Comment":"an error occurred during the execution of the request",  
            "resultCode": 0,
            "resultCodeDescription" : "request successfully executed...",
            "resultCodeError" : 400,
            "resultCodeErrorDescription" : "an error occurred during the execution of the request..."
        }), 400
    elif typeOfError == 'tokenexpires':
        return jsonify({
            "Status":"Error",
            "Comment":"your token has expired",  
            "resultCode": 1,
            "resultCodeDescription" : "request not executed...",
            "resultCodeError" : 401,
            "resultCodeErrorDescription" : "your token has expired..."
        }), 401
    elif typeOfError == 'tokeninvalid':
        return jsonify({
            "Status":"Error",
            "Comment":"your token is invalid",  
            "resultCode": 1,
            "resultCodeDescription" : "request not executed...",
            "resultCodeError" : 422,
            "resultCodeErrorDescription" : "your token is invalid..."
        }), 422
    elif typeOfError == 'tokenunauthorized':
        return jsonify({
            "Status":"Error",
            "Comment":"you forgot the token, please specify the token",  
            "resultCode": 1,
            "resultCodeDescription" : "request not executed...",
            "resultCodeError" : 401,
            "resultCodeErrorDescription" : "you forgot the token, please specify the token..."
        }), 401