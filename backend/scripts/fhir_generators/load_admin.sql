SET sql_mode='';

LOAD DATA INFILE '/tmp/facilities.csv' INTO TABLE facility FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\r\n' (id, name, phone, fax, street, city, state, postal_code, country_code, federal_ein, website, email, service_location, billing_location, accepts_assignment, pos_code, attn, facility_npi, tax_id_type, color, primary_business_entity, extra_validation);

LOAD DATA INFILE '/tmp/users.csv' INTO TABLE users FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\r\n' (id, username, password, authorized, active, fname, lname, facility, facility_id, npi, title, specialty, email, taxonomy, main_menu_role, patient_menu_role);
