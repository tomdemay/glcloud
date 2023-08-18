import mysql.connector
import pickle
import redis

#Example elasticache end point can be redis.scsdmx.ng.0001.usw2.cache.amazonaws.com
redis_host = 'rds-lab-redis.iotgwt.clustercfg.use1.cache.amazonaws.com'
hostname = 'flipbasket.c7hkuw409aei.us-east-1.rds.amazonaws.com'

username = 'root'
password = 'password'
database = 'employees'


class Employee:
    def __init__(self, emp_no, first_name, last_name, email_id):
        self.emp_no = emp_no
        self.first_name = first_name
        self.last_name = last_name
        self.email_id = email_id
        self.tostring()
    def tostring(self):
        print(f"Employee ({self.emp_no}): {self.first_name}, {self.last_name} - {self.email_id}")


def getAllEmployees() :
    print ("\n\nUsing mysql.connector")
    print ("---------------------")
    conn = mysql.connector.connect(host=hostname, user=username, passwd=password, db=database)
    cur = conn.cursor()
    cur.execute("SELECT emp_no, first_name, last_name, email_id FROM employees LIMIT 10")
    for emp_no, first_name, last_name, email_id in cur.fetchall() :
        employee_obj = Employee(emp_no, first_name, last_name, email_id)
    cur.close()
    conn.close()



def getEmployee(emp_no):
    print ("\nGetting the employee", emp_no)
    red = redis.StrictRedis(host=redis_host, port=6582, db=0)
    red_obj = red.get(emp_no)
    if red_obj != None:
        print ("Object found in cache, not looking in DB")
        #Deserialize the object coming from Redis
        employee_obj = pickle.loads(red_obj)
        employee_obj.tostring()
    else:
        print ("No key found in redis, going to database to take a look")
        conn = mysql.connector.connect(host=hostname, user=username, passwd=password, db=database)
        cur = conn.cursor()
        query = "SELECT emp_no, first_name, last_name, email_id FROM employees WHERE emp_no = %s"
        cur.execute(query, (emp_no,))
        for emp_no, first_name, last_name, email_id in cur :
            employee_obj = Employee(emp_no, first_name, last_name, email_id)
            #Serialize the object
            ser_obj = pickle.dumps(employee_obj)
            red.set(emp_no, ser_obj)
            print (" Order fetched from DB and pushed to redis")
        cur.close()
        conn.close()

def main() :
    getAllEmployees()
    getEmployee(10001)

main()