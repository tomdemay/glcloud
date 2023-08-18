/**
 * @author Nirmallya Mukherjee
 * 
 * Note: this is a sample code and is provided as part of training without any warranty.
 * You can use this code in any way at your own risk. 
 */

package com.skl.cloud.dynamodb;

import java.util.HashMap;
import java.util.Map;

import com.amazonaws.AmazonClientException;
import com.amazonaws.AmazonServiceException;
import com.amazonaws.auth.profile.ProfileCredentialsProvider;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDB;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDBClientBuilder;
import com.amazonaws.services.dynamodbv2.document.DynamoDB;
import com.amazonaws.services.dynamodbv2.document.Index;
import com.amazonaws.services.dynamodbv2.document.ItemCollection;
import com.amazonaws.services.dynamodbv2.document.ItemUtils;
import com.amazonaws.services.dynamodbv2.document.QueryOutcome;
import com.amazonaws.services.dynamodbv2.document.Table;
import com.amazonaws.services.dynamodbv2.document.spec.QuerySpec;
import com.amazonaws.services.dynamodbv2.document.utils.ValueMap;
import com.amazonaws.services.dynamodbv2.model.AttributeDefinition;
import com.amazonaws.services.dynamodbv2.model.AttributeValue;
import com.amazonaws.services.dynamodbv2.model.ComparisonOperator;
import com.amazonaws.services.dynamodbv2.model.Condition;
import com.amazonaws.services.dynamodbv2.model.CreateTableRequest;
import com.amazonaws.services.dynamodbv2.model.DescribeTableRequest;
import com.amazonaws.services.dynamodbv2.model.GlobalSecondaryIndex;
import com.amazonaws.services.dynamodbv2.model.KeySchemaElement;
import com.amazonaws.services.dynamodbv2.model.KeyType;
import com.amazonaws.services.dynamodbv2.model.Projection;
import com.amazonaws.services.dynamodbv2.model.ProjectionType;
import com.amazonaws.services.dynamodbv2.model.ProvisionedThroughput;
import com.amazonaws.services.dynamodbv2.model.PutItemRequest;
import com.amazonaws.services.dynamodbv2.model.PutItemResult;
import com.amazonaws.services.dynamodbv2.model.ScalarAttributeType;
import com.amazonaws.services.dynamodbv2.model.ScanRequest;
import com.amazonaws.services.dynamodbv2.model.ScanResult;
import com.amazonaws.services.dynamodbv2.model.TableDescription;
import com.amazonaws.services.dynamodbv2.util.TableUtils;


public class Dynamo {

	private static final String TABLE_NAME = "orders";
    private static final String GLOBAL_IDX = "city_idx";
    private static enum TABLE_FIELDS {
    	//Partition and sort keys respectively
    	user_id, order_id, 
    	//Secondary index field and hence mandatory
    	city,
    	//Below are regular attributes and all are optional
    	address, order_details, price, tax
    };

    private static AmazonDynamoDB client;

    
    public static void main(String[] args) throws Exception {
    	try {
			init();
			createTable();
			insertData();
			tableScan();
			
	        //Table and index objects are threadsafe and should not be created in a loop
			Table orders = new DynamoDB(client).getTable(TABLE_NAME);
	        Index ordersIdx = orders.getIndex(GLOBAL_IDX);
			
			partitionFetch(orders);
			indexFetch(ordersIdx);

		//These exceptions are as defined by AWS in their java code template; you can add app specific exceptions later
    	} catch (AmazonServiceException ase) {
            System.out.println("Caught an AmazonServiceException, which means your request made it "
                    + "to AWS, but was rejected with an error response for some reason.");
            System.out.println("Error Message:    " + ase.getMessage());
            System.out.println("HTTP Status Code: " + ase.getStatusCode());
            System.out.println("AWS Error Code:   " + ase.getErrorCode());
            System.out.println("Error Type:       " + ase.getErrorType());
            System.out.println("Request ID:       " + ase.getRequestId());
        } catch (AmazonClientException ace) {
            System.out.println("Caught an AmazonClientException, which means the client encountered "
                    + "a serious internal problem while trying to communicate with AWS, "
                    + "such as not being able to access the network.");
            System.out.println("Error Message: " + ace.getMessage());
        } catch (Exception ex) {
        	System.out.println("An unhandled exception occured. Just listing it for analysis");
        	ex.printStackTrace();
        }
    }
    
    
    private static void insertData() {
    	Map<String, AttributeValue> item = newItem("scotty", "R0000001", "FortBaker", "#1 Engineering drive", 2500000, 95000,
        		"Matter antimatter fusion controller", "2MW Fusion reactor", "Transporter base dial");
        PutItemRequest putItemRequest = new PutItemRequest(TABLE_NAME, item);
        PutItemResult putItemResult = client.putItem(putItemRequest);
        System.out.println("Result status code: " + putItemResult.getSdkHttpMetadata().getHttpStatusCode());

        item = newItem("nirmallya", "L0000001", "Bangalore", "Sarjapura Road", 150000, 30000,
        		"55 inch LG TV", "Amazon echo");
        putItemRequest = new PutItemRequest(TABLE_NAME, item);
        putItemResult = client.putItem(putItemRequest);
        System.out.println("Result status code: " + putItemResult.getSdkHttpMetadata().getHttpStatusCode());

        item = newItem("nirmallya", "L0000002", "Bangalore", "Sarjapura Road", 250000, 45000,
        		"Dell Precision 7000 laptop", "Seagate ext 1TB HDD", "32GB Sandisk pen drive");
        putItemRequest = new PutItemRequest(TABLE_NAME, item);
        putItemResult = client.putItem(putItemRequest);
        System.out.println("Result status code: " + putItemResult.getSdkHttpMetadata().getHttpStatusCode());
    }
    
    
    private static void tableScan() {
        //Scan orders where tax is greater than 85000 (will this be efficient even though it works?)
        HashMap<String, Condition> scanFilter = new HashMap<String, Condition>();
        Condition condition = new Condition()
            .withComparisonOperator(ComparisonOperator.GT.toString())
            .withAttributeValueList(new AttributeValue().withN("40000"));
        scanFilter.put(TABLE_FIELDS.tax.toString(), condition);
        ScanRequest scanRequest = new ScanRequest(TABLE_NAME).withScanFilter(scanFilter);
        ScanResult scanResult = client.scan(scanRequest);

        System.out.println("Table scan result is:");
        scanResult.getItems().forEach(i -> {
        	System.out.println(ItemUtils.toItem(i).toJSONPretty());
        });
    }

    
    private static void partitionFetch(Table orders) {
        //The best way to get data is base on RK and if you include the SK then it will be PK fetch
        QuerySpec querySpec = new QuerySpec()
        		.withKeyConditionExpression("user_id = :uid")
        		.withValueMap(new ValueMap().withString(":uid", "scotty"));
        ItemCollection<QueryOutcome> items = orders.query(querySpec);
        
        System.out.println("RK query result is");
        items.forEach(i -> {
        	System.out.println(i.toJSONPretty());
        });
    }

    
    private static void indexFetch(Index idx) {
        QuerySpec querySpec = new QuerySpec()
        		.withKeyConditionExpression("city = :city")
        		.withValueMap(new ValueMap().withString(":city", "Bangalore"));
        ItemCollection<QueryOutcome> items = idx.query(querySpec);
        
        System.out.println("Index query result is");
        items.forEach(i -> {
        	System.out.println(i.toJSONPretty());
        });
    }

    
    /**
     * The only information needed to create a client are security credentials consisting of the AWS Access Key ID and Secret Access Key.
     * All other configuration, such as the service endpoints, are performed automatically. Client parameters, such as proxies, can be
     * specified in an optional ClientConfiguration object when constructing a client.
     *
     * @see com.amazonaws.auth.BasicAWSCredentials
     * @see com.amazonaws.auth.ProfilesConfigFile
     * @see com.amazonaws.ClientConfiguration
     */
    private static void init() throws Exception {
        /*
         * The ProfileCredentialsProvider will return your [default] credential profile by reading from the credentials file located at
         * (/home/nirmallya/.aws/credentials).
         */
        ProfileCredentialsProvider credentialsProvider = new ProfileCredentialsProvider();
        try {
            credentialsProvider.getCredentials();
        } catch (Exception e) {
            throw new AmazonClientException(
                    "Cannot load the credentials from the credential profiles file. " +
                    "Please make sure that your credentials file is at the correct " +
                    "location (/home/nirmallya/.aws/credentials), and is in valid format.",
                    e);
        }
        client = AmazonDynamoDBClientBuilder.standard().withCredentials(credentialsProvider).withRegion(Regions.US_WEST_2).build();
    }
    
    
    private static void createTable() throws Exception {
        // Create a table with a primary hash key named 'name', which holds a string
        CreateTableRequest createTableRequest = new CreateTableRequest().withTableName(TABLE_NAME)
            //RK and SK definition
        	.withKeySchema(new KeySchemaElement().withAttributeName(TABLE_FIELDS.user_id.toString()).withKeyType(KeyType.HASH))
            .withKeySchema(new KeySchemaElement().withAttributeName(TABLE_FIELDS.order_id.toString()).withKeyType(KeyType.RANGE))
            //RK, SK and other sec idx related mandatory attribute datatype specifications
            .withAttributeDefinitions(new AttributeDefinition().withAttributeName(TABLE_FIELDS.user_id.toString()).withAttributeType(ScalarAttributeType.S))
            .withAttributeDefinitions(new AttributeDefinition().withAttributeName(TABLE_FIELDS.order_id.toString()).withAttributeType(ScalarAttributeType.S))
            .withAttributeDefinitions(new AttributeDefinition().withAttributeName(TABLE_FIELDS.city.toString()).withAttributeType(ScalarAttributeType.S))
            //Global sec idx definition
            .withGlobalSecondaryIndexes(new GlobalSecondaryIndex()
        		.withIndexName(GLOBAL_IDX)
        		//The RK of the idx and notice it is different from the base table RK
        		.withKeySchema(new KeySchemaElement().withAttributeName(TABLE_FIELDS.city.toString()).withKeyType(KeyType.HASH))
        		//What fields apart from from the base table PK to copy over
        		.withProjection(new Projection()
        				.withProjectionType(ProjectionType.INCLUDE)
        				.withNonKeyAttributes(TABLE_FIELDS.price.toString())
        				.withNonKeyAttributes(TABLE_FIELDS.tax.toString())
        				)
        		.withProvisionedThroughput(new ProvisionedThroughput().withReadCapacityUnits(1L).withWriteCapacityUnits(1L))
        		)
            //Planning for the WCU and RCU, defaulting to 1 for cost control
            .withProvisionedThroughput(new ProvisionedThroughput().withReadCapacityUnits(1L).withWriteCapacityUnits(1L));

        //Create table if it does not exist yet
        TableUtils.createTableIfNotExists(client, createTableRequest);
        //wait for the table to move into ACTIVE state
        TableUtils.waitUntilActive(client, TABLE_NAME);

        //Describe the new table
        DescribeTableRequest describeTableRequest = new DescribeTableRequest().withTableName(TABLE_NAME);
        TableDescription tableDescription = client.describeTable(describeTableRequest).getTable();
        System.out.println("Table Description: " + tableDescription);
    }

    
    private static Map<String, AttributeValue> newItem(String userId, String orderId, String city,
    		String address, double price, double tax, String... orderDetails) {
        Map<String, AttributeValue> item = new HashMap<String, AttributeValue>();
        item.put(TABLE_FIELDS.user_id.toString(), new AttributeValue(userId));
        item.put(TABLE_FIELDS.order_id.toString(), new AttributeValue(orderId));
        item.put(TABLE_FIELDS.city.toString(), new AttributeValue(city));
        
        item.put(TABLE_FIELDS.address.toString(), new AttributeValue(address));
        item.put(TABLE_FIELDS.price.toString(), new AttributeValue().withN(Double.toString(price)));
        item.put(TABLE_FIELDS.tax.toString(), new AttributeValue().withN(Double.toString(tax)));
        item.put(TABLE_FIELDS.order_details.toString(), new AttributeValue().withSS(orderDetails));

        return item;
    }

}
