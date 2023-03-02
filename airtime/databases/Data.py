import pymysql
import logging as logger

# Configuration de la gestion des logs et traces
logger.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logger.DEBUG)

# Méthode permetant de se connecter à la base de données
# Retourne un objet de connexion Ouvert
def connectToDatabase(host, user, password, db, port):
    mysql = pymysql.connect(host = host, user = user, password = password, db = db, port = 25060,ssl={
        'ssl': {
            'ca': 'ca-cert.pem',
            #'key': 'client-cert.pem',
            #'cert': 'client-key.pem'
        }
    })
    logger.info("CONNEXION A LA BASE DE DONNES ETABLIE")
    return mysql
    try:
        string = ""
        #mysql = pymysql.connect(host = host, user = user, password = password, db = db, port = 3306)
        #logger.info("CONNEXION A LA BASE DE DONNES ETABLIE")
        #return mysql
    except:
        logger.error("ERREUR LORS DE LA CONNEXION A LA BASE DE DONNEES")
        

# Méthode permettant d'exécuter une requête avec retour de données (SELECT)
# Retourne une collection d'enregistrement ou une collection vide ou une chaine lors d'une exception
def executeQueryForGetData(context, query):
    try:
        cur =  context.cursor()
        result = cur.execute(query)

        if result > 0:
            details = cur.fetchall()
            context.close()
            logger.info("{} REQUETE EXECUTER AVEC SUCCES ET RETOUR DE RESULTAT".format(query))
            return details
        else:
            logger.info("{} REQUETE EXECUTER AVEC SUCCES MAIS PAS DE RESULTAT".format(query))
            return []
    except:
        logger.error("{} Erreur survenue lors de l'execution de la requete !!!".format(query))
        return "Erreur survenue lors de l'execution de la requete !!!"

# Méthode permettant d'exécuter une requête sans retour de données (DELETE, UPDATE, INSERT, ETC.)
# Retour 1 quand la requête s'est bien executer et 0 lors d'une exception        
def executeQueryForInsertDate(context, query, data):
    cur =  context.cursor()
    cur.execute(query, data)
    context.commit()
    cur.close()
    context.close()
    logger.info("{} REQUETE EXECUTER AVEC SUCCES".format(query))
    return 1
    try:
        rr = []
    except :
        logger.error("{} Erreur survenue lors de l'execution de la requete !!!".format(query))
        return 0


def executeQueryForUpdate(context, query):
    try:
        cur =  context.cursor()
        cur.execute(query)
        context.commit()
        cur.close()
        context.close()
        logger.info("{} REQUETE EXECUTER AVEC SUCCES".format(query))
        return 1
    except :
        logger.error("{} Erreur survenue lors de l'execution de la requete !!!".format(query))
        return 0

