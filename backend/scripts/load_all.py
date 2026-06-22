import os
import subprocess

MYSQL_DIR = "mysql_data"
MONGO_DIR = "mongo_data"

# MySQL Schema
table_schema = """
CREATE TABLE IF NOT EXISTS {table} (
    id VARCHAR(36) PRIMARY KEY,
    identifier VARCHAR(255),
    status VARCHAR(50),
    created_at VARCHAR(100)
);
"""

load_data_sql = """
LOAD DATA INFILE '/var/lib/mysql-files/{table}.csv' INTO TABLE {table} 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\\r\\n' 
IGNORE 1 ROWS (id, identifier, status, created_at);
"""

# 1. Load MySQL Data
mysql_files = [f for f in os.listdir(MYSQL_DIR) if f.endswith('.csv')]
for file in mysql_files:
    table_name = file.replace('.csv', '')
    
    print(f"Loading {table_name} into MySQL...")
    # Copy file to container
    subprocess.run(f"docker cp {os.path.join(MYSQL_DIR, file)} sentinel_mysql:/var/lib/mysql-files/{file}", shell=True, check=True)
    
    # Create table and load
    sql_script = table_schema.format(table=table_name) + load_data_sql.format(table=table_name)
    with open(f"tmp_load_{table_name}.sql", 'w') as f:
        f.write(sql_script)
        
    subprocess.run(f"docker cp tmp_load_{table_name}.sql sentinel_mysql:/tmp/load.sql", shell=True, check=True)
    subprocess.run(f'docker exec -i sentinel_mysql mysql -uroot -prootpassword sentinel < tmp_load_{table_name}.sql', shell=True)
    os.remove(f"tmp_load_{table_name}.sql")

# 2. Load MongoDB Data
# mongo_files = [f for f in os.listdir(MONGO_DIR) if f.endswith('.json')]
# for file in mongo_files:
#     collection_name = file.replace('.json', '')
#     print(f"Loading {collection_name} into MongoDB...")
#     # Copy file to container
#     subprocess.run(f"docker cp {os.path.join(MONGO_DIR, file)} sentinel_mongodb:/tmp/{file}", shell=True, check=True)
#     
#     # Mongoimport
#     cmd = f'docker exec -i sentinel_mongodb mongoimport -u root -p rootpassword --authenticationDatabase admin --db sentinel --collection {collection_name} --type json --file /tmp/{file}'
#     subprocess.run(cmd, shell=True)

print("Data Loading Complete!")
