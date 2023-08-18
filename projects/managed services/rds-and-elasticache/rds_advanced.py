import mysql.connector
import pickle
import redis

#Example elasticache end point can be redis.scsdmx.ng.0001.usw2.cache.amazonaws.com
redis_host = 'my-test-redis.iotgwt.ng.0001.use1.cache.amazonaws.com'
hostname = 'my-test-rds.c7hkuw409aei.us-east-1.rds.amazonaws.com'

username = 'root'
password = 'password'
database = 'employees'


class Employee:
    def __init__(self, id, first_name, last_name, email):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.tostring()
    def tostring(self):
        print(f"Employee ({self.id}): {self.first_name}, {self.last_name} - {self.email}")


def getAllEmployees() :
    print ("\n\nUsing mysql.connector")
    print ("---------------------")
    conn = mysql.connector.connect(host=hostname, user=username, passwd=password, db=database)
    cur = conn.cursor()
    cur.execute("SELECT id, first_name, last_name, email FROM employees")
    for id, first_name, last_name, email in cur.fetchall() :
        employee_obj = Employee(id, first_name, last_name, email)
    cur.close()
    conn.close()



def getEmployee(id):
    print ("\nGetting the employee", id)
    red = redis.StrictRedis(host=redis_host, port=6379, db=0)
    red_obj = red.get(id)
    if red_obj != None:
        print ("Object found in cache, not looking in DB")
        #Deserialize the object coming from Redis
        employee_obj = pickle.loads(red_obj)
        employee_obj.tostring()
    else:
        print ("No key found in redis, going to database to take a look")
        conn = mysql.connector.connect(host=hostname, user=username, passwd=password, db=database)
        cur = conn.cursor()
        query = "SELECT id, first_name, last_name, email FROM employees WHERE id = %s"
        cur.execute(query, (id,))
        for id, first_name, last_name, email in cur :
            employee_obj = Employee(id, first_name, last_name, email)
            #Serialize the object
            ser_obj = pickle.dumps(employee_obj)
            red.set(id, ser_obj)
            print (" Order fetched from DB and pushed to redis")
        cur.close()
        conn.close()

def main() :
    getAllEmployees()
    getEmployee(1)

main()