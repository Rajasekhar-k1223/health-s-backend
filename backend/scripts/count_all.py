import subprocess
import json

mysql_tables = ["account", "chargeitem", "claim", "coverage", "eligibilityrequest", "eligibilityresponse", "explanationofbenefit", "healthcareservice", "invoice", "location", "organization", "practitioner"]

mongo_cols = ["administrableproductdefinition", "allergyintolerance", "appointment", "careplan", "careteam", "condition", "device", "diagnosticreport", "familymemberhistory", "goal", "guidanceresponse", "imagingstudy", "immunization", "library", "measure", "measurereport", "medication", "medicationadministration", "medicationdispense", "medicationrequest", "medicationstatement", "medicinalproductdefinition", "molecularsequence", "observation", "packagedproductdefinition", "patient", "plandefinition", "procedure", "referralrequest", "regulatedauthorization", "riskassessment", "schedule", "servicerequest", "specimen", "task"]

results = []

for table in mysql_tables:
    try:
        cmd = f'docker exec sentinel_mysql mysql -uroot -prootpassword sentinel -sN -e "SELECT COUNT(*) FROM {table};"'
        out = subprocess.check_output(cmd, shell=True).decode().strip()
        results.append({"Database": "MySQL", "Table/Collection": table, "Count": int(out)})
    except Exception as e:
        results.append({"Database": "MySQL", "Table/Collection": table, "Count": "Error"})

for col in mongo_cols:
    try:
        cmd = f'docker exec sentinel_mongodb mongosh sentinel -u root -p rootpassword --authenticationDatabase admin --quiet --eval "db.{col}.countDocuments()"'
        out = subprocess.check_output(cmd, shell=True).decode().strip()
        results.append({"Database": "MongoDB", "Table/Collection": col, "Count": int(out)})
    except Exception as e:
        results.append({"Database": "MongoDB", "Table/Collection": col, "Count": "Error"})

print("| Database | Table / Collection | Exact Row Count |")
print("| :--- | :--- | :--- |")
for r in results:
    print(f"| {r['Database']} | `{r['Table/Collection']}` | {r['Count']} |")
