from pyspark.sql import SparkSession
from pyspark.sql.functions import col, upper, when

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("CSV Processing") \
    .getOrCreate()

# Read CSV file
input_path = "input_data.csv"
df = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv(input_path)

# Display schema and first few rows
print("Schema:")
df.printSchema()
print("\nFirst 5 rows:")
df.show(5)

# Example processing: filter, transform, and aggregate
processed_df = df.filter(col("age") > 18) \
    .withColumn("name_upper", upper(col("name"))) \
    .withColumn("age_group", 
                when(col("age") < 30, "Young")
                .when(col("age") < 50, "Middle")
                .otherwise("Senior"))

# Show processed data
print("\nProcessed data:")
processed_df.show()

# Write output to CSV
output_path = "output_data"
processed_df.coalesce(1) \
    .write \
    .mode("overwrite") \
    .option("header", "true") \
    .csv(output_path)

print(f"Data successfully written to {output_path}")

# Stop Spark session
spark.stop()
