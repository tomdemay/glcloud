#*********************************************************************************************************************
#Author - Nirmallya Mukherjee
#This script connects to a MySQL DB using multiple driver options
#*********************************************************************************************************************
import pymysql
import mysql.connector

hostname = 'flipbasket.c7hkuw409aei.us-east-1.rds.amazonaws.com'
username = 'root'
password = 'password'
database = 'employees'

# Simple routine to run a query on a database and print the results:
def doQuery(conn) :
    cur = conn.cursor()
    cur.execute("SELECT emp_no, birth_date, first_name, last_name, gender, hire_date, password, email_id FROM employees limit 1>    for emp_no, birth_date, first_name, last_name, gender, hire_date, password, email_id in cur.fetchall() :
        print (emp_no, birth_date, first_name, last_name, gender, hire_date, password, email_id)


def pymysqlConnector() :
    print("Using pymysql")
    print("-------------")
    myConnection = pymysql.connect(host=hostname, user=username, passwd=password, db=database)
    doQuery(myConnection)
    myConnection.close()


def mysqlConnector() :
    print("\n\nUsing mysql.connector")
    print("---------------------")
    myConnection = mysql.connector.connect(host=hostname, user=username, passwd=password, db=database)
    doQuery(myConnection)
    myConnection.close()


def createOrder() :
    print("\n\nUsing any of the above connectors, insert a new record in the orders table")
    conn = mysql.connector.connect(host=hostname, user=username, passwd=password, db=database)
    cur = conn.cursor()
    # TBD:You have to write this code and submit as part of the lab

    conn.commit()
    cur.close()
    conn.close()


def main() :
    pymysqlConnector()
    mysqlConnector()
    createOrder()


main()