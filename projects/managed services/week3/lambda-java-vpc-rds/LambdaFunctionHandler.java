/**
 * @author Nirmallya Mukherjee
 * 
 * Note: this is a sample code and is provided as part of training without any warranty.
 * You can use this code in any way at your own risk. 
 */

package com.skl.lambda.rds;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Map;

import org.json.JSONArray;
import org.json.JSONObject;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;

/**
 * Create this project in Eclipse using the plugin and selecting "New AWS Lambda Java Project"
 * and in the event dropdown select "Custom"
 * 
 * Layers can be setup using the instructions here
 *    https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html
 *    See the appbase directory for the structure and contents
 *
 * AWSLambdaVPCAccessExecutionRole policy must be attached to the lambda-multirole to access
 * resources that are attached to the VPC such as an RDS instance
 *    https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html
 * 
 * Memory should be 512MB and timeout should be 30s
 * 
 * At the time of creating the function select the default VPC and all the subnets and 
 * select the default security group. Multiple ENI will be created (see EC2 management console),
 * so do not hit the lambda immediately. Wait for about 2 minutes.
 * 
 * Setup the following JSON as the test case
 *   {"table": "employees","order_by": "birth_date"}
 * 
 * Create the RDS instance as follows -
 *   MySQL, 8.0.LATEST, Free Tier, DBInstance=flipbasket, credentials=root/password
 *   Instance size=T2u, No Storage Autoscaling, Connectivity-DefVPC,
 *   Additional conn-VPC SG- create new "rds-sg"
 *   No backups, no monitoring, no minor version upgrade
 *   Create the DB
 *   Once DB is ready modify the rds-sg cidr=0.0.0.0/0
 * Once the instance is created, connect to it from an EC2 instance after installing the MySQL client
 * and create the schema using employees.sql
 * 
 * Once it all starts to work see the number of connections in RDS console as one in monitoring tab.
 * Do not make any more invocations; wait for about 25mins and see the connections drop to 0
 * 
 * Note-> Upload the function and then go to the console->"Export function"->"Download AWS SAM File"!
 *        Now use this SAM to run and test locally! You do not have to author the SAM from scratch.
 *        Just ensure that the test cases are updated otherwise the default test case will fail.
 *        Do not upload with the SAM file, otherwise the lambda may not fire and error out by saying
 *        that LambdaFunctionHandler is missing!
 */

public class LambdaFunctionHandler implements RequestHandler<Object, String> {

    //The following variables will be initialized using the lambda env vars
	private static final String URL = System.getenv("CONNECT_IP_DNS");
	private static final String DB = System.getenv("DB_NAME");
	private static final String UID = System.getenv("USER_ID");
	private static final String PWD = System.getenv("PWD");

	//These vars are outside the scope of the request handler and hence can be reused between invocations
	//Closure happens when the container running the function is evicted. Instead of a single DB connection,
	//a pool implementation should be done
	private static Connection conn = null;
	
	
	@Override
    public String handleRequest(Object input, Context context) {
		initialize();
		
		//To output logs from your function code, you can use methods on java.lang.System
		//or any logging module that writes to stdout or stderr; don't want to log passwords :)
		//Logger is another way to log to cloudwatch
        context.getLogger().log("Input: " + input + " type is Map " + (input instanceof Map) + "\n");
		String tableName = (String)((Map<?, ?>)input).get("table");
		String orderBy = (String)((Map<?, ?>)input).get("order_by");
		System.out.format("Going to work on table %s and the sort column is %s\n", tableName, orderBy);

		try {
			System.out.print("Creating statement... ");
			Statement stmt = conn.createStatement();
			System.out.println("Done");
			
			System.out.print("Running the query... ");
			ResultSet rs = stmt.executeQuery("select * from " + tableName + " order by " + orderBy + " limit 10");
			System.out.println("Done");

			JSONArray jsonArray = getJsonFromResultset(rs);
			jsonArray.put(new JSONObject().put("status", 200));
			System.out.println(jsonArray.toString(2));	//Pretty print the json with indent of 2
	        return jsonArray.toString();

		} catch (SQLException e) {
			e.printStackTrace();
		} catch (Exception ex) {
			ex.printStackTrace();
		}
		
		return new JSONArray().put(new JSONObject().put("status", 500)).toString();
    }
	
	
	private JSONArray getJsonFromResultset(ResultSet rs) throws SQLException {
		int totalColumns = rs.getMetaData().getColumnCount();
		JSONArray jsonArray = new JSONArray();
		while(rs.next()) {
			JSONObject row = new JSONObject();
			for(int i=0; i<totalColumns; i++) {
				row.put(rs.getMetaData().getColumnLabel(i+1).toLowerCase(), rs.getObject(i+1));
			}
			jsonArray.put(row);
		}
		return jsonArray;
	}

	
	private void initialize() {
		if(conn!=null) return;
		
		try {
			System.out.print("Loading driver... ");
			Class.forName("com.mysql.jdbc.Driver");
			System.out.println("Done");

			String connectString = "jdbc:mysql://" + (URL==null?"127.0.0.1":URL) + ":3306/" + (DB==null?"flipbasket":DB);
			System.out.println("Using connect string as " + connectString);
			System.out.print("Connecting to the database... ");
			conn = DriverManager.getConnection(connectString, UID==null?"root":UID, PWD==null?"password":PWD);
			System.out.println("Done");
		} catch (ClassNotFoundException | SQLException e) {
			e.printStackTrace();
		}
	}

}
