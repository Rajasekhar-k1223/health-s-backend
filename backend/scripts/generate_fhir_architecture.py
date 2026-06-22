import json
import csv
import os
import random
from datetime import datetime, timedelta
import uuid

# Define exact counts as requested
COUNTS = {
    # MySQL
    "Practitioner": 100,
    "Organization": 20,
    "Location": 50,
    "HealthcareService": 50,
    "Account": 10000,
    "Claim": 10000,
    "Invoice": 8000,
    "ChargeItem": 50000,
    "Coverage": 1000,
    "EligibilityRequest": 5000,
    "EligibilityResponse": 5000,
    "ExplanationOfBenefit": 10000,
    
    # MongoDB
    "Patient": 1000,
    "CareTeam": 5000,
    "Device": 2000,
    "Condition": 20000,
    "AllergyIntolerance": 5000,
    "Procedure": 15000,
    "CarePlan": 5000,
    "Goal": 10000,
    "FamilyMemberHistory": 8000,
    "RiskAssessment": 2500,
    "Observation": 150000,
    "DiagnosticReport": 10000,
    "Specimen": 12000,
    "ImagingStudy": 5000,
    "MolecularSequence": 1000,
    "Medication": 2000,
    "MedicationRequest": 30000,
    "MedicationDispense": 25000,
    "MedicationAdministration": 20000,
    "MedicationStatement": 15000,
    "Immunization": 12000,
    "Appointment": 15000,
    "Schedule": 500,
    "Task": 30000,
    "ServiceRequest": 10000,
    "ReferralRequest": 5000,
    "PlanDefinition": 100,
    "Library": 50,
    "GuidanceResponse": 2000,
    "Measure": 20,
    "MeasureReport": 5000,
    "MedicinalProductDefinition": 1000,
    "PackagedProductDefinition": 500,
    "AdministrableProductDefinition": 500,
    "RegulatedAuthorization": 200,
}

MYSQL_DIR = "mysql_data"
MONGO_DIR = "mongo_data"

os.makedirs(MYSQL_DIR, exist_ok=True)
os.makedirs(MONGO_DIR, exist_ok=True)

def generate_mysql_csv(resource_name, count, columns):
    filename = os.path.join(MYSQL_DIR, f"{resource_name.lower()}.csv")
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for i in range(1, count + 1):
            row = [str(uuid.uuid4()) if "id" in c.lower() else f"Mock {c} {i}" for c in columns]
            writer.writerow(row)
    print(f"Generated {count} MySQL records for {resource_name}")

def generate_mongo_json(resource_name, count):
    filename = os.path.join(MONGO_DIR, f"{resource_name.lower()}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        for i in range(1, count + 1):
            doc = {
                "resourceType": resource_name,
                "id": str(uuid.uuid4()),
                "status": "active",
                "identifier": [{"system": "http://sentinel.health/id", "value": f"{resource_name}-{i}"}],
                "meta": {"lastUpdated": datetime.utcnow().isoformat() + "Z"}
            }
            f.write(json.dumps(doc) + "\n")
    print(f"Generated {count} MongoDB FHIR records for {resource_name}")

if __name__ == "__main__":
    print("Generating FHIR Dataset Architecture...")
    
    # 1. MySQL Data (Relational)
    mysql_resources = ["Practitioner", "Organization", "Location", "HealthcareService", "Account", "Claim", "Invoice", "ChargeItem", "Coverage", "EligibilityRequest", "EligibilityResponse", "ExplanationOfBenefit"]
    for res in mysql_resources:
        if res in COUNTS:
            generate_mysql_csv(res, COUNTS[res], ["id", "identifier", "status", "created_at"])
            
    # 2. MongoDB Data (Document / FHIR JSON)
    mongo_resources = [res for res in COUNTS.keys() if res not in mysql_resources]
    for res in mongo_resources:
        generate_mongo_json(res, COUNTS[res])

    print("\nGeneration Complete! Data is ready for ingestion into MySQL and MongoDB.")
