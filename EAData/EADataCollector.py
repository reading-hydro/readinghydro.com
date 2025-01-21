#! /usr/bin/python3

import syslog
import datetime
import json
import boto3
import psycopg2
from urllib import request



# we are useing AWS Secrets Manager to hold API keys, and mqtt account password This retrieves a secret


def get_secret(MySecretString):

    secret_name = "RdgHydroServerSecrets"
    region_name = "eu-west-2"

    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    get_secret_value_response = client.get_secret_value(SecretId=secret_name)

    all_secret = json.loads(get_secret_value_response['SecretString'])
    secret = all_secret.get(MySecretString)
    return secret




def main():

    syslog.syslog("Starting update of EA data tables")

    DbHost = get_secret("DB_HOST")
    DbPort = int(get_secret("DB_PORT"))
    DbUser = get_secret("DB_USER")
    DbPassword = get_secret("DB_PASSWORD")
    DbName = get_secret("DB_NAME")

    try:
        db = psycopg2.connect(dbname=DbName, user=DbUser, password=DbPassword, host=DbHost, port=DbPort)
    except Exception as e:
        print("Database error on connection: ",e)
        syslog.syslog("Database connection error")

# get the datetime of the last database entry
    
    cursor = db.cursor()
    cursor.execute("SELECT time FROM public.eadata ORDER BY entrytime DESC")
    row = cursor.fetchone()[0]
    LastEntry = row.entrytime

# get the flow data from the Enviroment Agency since last entry
    myds3 = LastEntry.strftime('%Y-%m-%d')
    myds4 = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    EAapiURL = "https://environment.data.gov.uk/flood-monitoring/id/measures/2200TH-flow--Mean-15_min-m3_s/readings?startdate=" + myds3 + "&enddate=" + myds4 + "&_sorted&_limit=3000"
    try: 
        jsondata = request.urlopen(url=EAapiURL,timeout=20)
    except:
        print("Error getting EA data")
        syslog.syslog("Error getting EA data")
# enter the data into the database only if is after the LsatEntry (new data)

    data = json.loads(jsondata.read())
    items = data.get('items')
    for row in items:
        if row.get('datetime') > LastEntry:
#            cursor.execute("INSERT INTO public.eadata (entrytime, flow) VALUES (%s, %s)", (row.get('dateTime'), row.get('value')))
            print(row.get('dateTime'), row.get('value'))
# commit and close the database
    
    db.commit()
    cursor.close()
    db.close()

if __name__ == '__main__':
    main()