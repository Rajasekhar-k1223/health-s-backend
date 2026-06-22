import csv
import random

NUM_FACILITIES = 50_000
NUM_USERS = 450_000

print(f"Generating {NUM_FACILITIES} Facility (Organization/Location) records...")

with open('facilities.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    for i in range(1, NUM_FACILITIES + 1):
        if i % 100000 == 0: print(f"Generated {i} facilities...")
        # id, name, phone, fax, street, city, state, postal_code, country_code, federal_ein, website, email, service_location, billing_location, accepts_assignment, pos_code, attn, facility_npi, tax_id_type, color, primary_business_entity, extra_validation
        row = [
            i, f"Health Center {i}", "555-0199", "555-0200", f"{i} Health Way", "Metropolis", "NY", "10001", "US",
            f"EIN{i}", f"http://health{i}.example.com", f"info@health{i}.example.com", 1, 1, 1, 11, "",
            f"NPI{i}", "", "", 1, 1
        ]
        writer.writerow(row)

print(f"Generating {NUM_USERS} Users (Practitioner) records...")

with open('users.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    for i in range(1, NUM_USERS + 1):
        if i % 100000 == 0: print(f"Generated {i} users...")
        # id, username, password, authorized, active, fname, lname, facility, facility_id, npi, title, specialty, email, taxonomy, main_menu_role, patient_menu_role
        # Default password hash for 'pass' in OpenEMR is often used, but we'll leave it empty for bulk synthetic data.
        facility_id = random.randint(1, NUM_FACILITIES)
        row = [
            i, f"dr_smith_{i}", "", 1, 1, "John", f"Smith{i}", f"Health Center {facility_id}", facility_id, 
            f"NPIU{i}", "MD", "General Practice", f"drsmith{i}@example.com", "207Q00000X", "standard", "standard"
        ]
        writer.writerow(row)

print("Admin FHIR-mapped data generated.")
