import os
import requests
import datetime
from typing import Optional, Dict, Any

from app.models.patient import Patient
from app.models.device import Device
from app.models.alert import Alert

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL", "http://localhost:8080/fhir")

def _put_resource(resource_type: str, resource_id: str, payload: dict) -> bool:
    try:
        url = f"{FHIR_SERVER_URL}/{resource_type}/{resource_id}"
        response = requests.put(url, json=payload, timeout=5)
        if response.status_code in [200, 201]:
            print(f"✅ Synced {resource_type}/{resource_id} to FHIR.")
            return True
        else:
            print(f"❌ Failed FHIR Sync {resource_type}/{resource_id}. {response.status_code}")
            return False
    except Exception as e:
        print(f"🚨 FHIR Connection Error for {resource_type}/{resource_id}: {str(e)}")
        return False

# ==============================================================================
# ENTERPRISE EXPANSION FHIR MAPPINGS
# ==============================================================================

def sync_organization(org_id: int, name: str):
    payload = {
        "resourceType": "Organization",
        "id": f"org-{org_id}",
        "name": name,
        "active": True
    }
    _put_resource("Organization", payload["id"], payload)

def sync_location(loc_id: int, name: str, org_id: int):
    payload = {
        "resourceType": "Location",
        "id": f"loc-{loc_id}",
        "name": name,
        "status": "active",
        "managingOrganization": {"reference": f"Organization/org-{org_id}"}
    }
    _put_resource("Location", payload["id"], payload)

def sync_schedule(sched_id: int, provider_id: int):
    payload = {
        "resourceType": "Schedule",
        "id": f"sched-{sched_id}",
        "active": True,
        "actor": [{"reference": f"Practitioner/doctor-{provider_id}"}]
    }
    _put_resource("Schedule", payload["id"], payload)

def sync_slot(slot_id: int, sched_id: int, start: str, end: str):
    payload = {
        "resourceType": "Slot",
        "id": f"slot-{slot_id}",
        "schedule": {"reference": f"Schedule/sched-{sched_id}"},
        "status": "free",
        "start": start,
        "end": end
    }
    _put_resource("Slot", payload["id"], payload)

def sync_appointment(appt_id: int, patient_id: int, provider_id: int):
    payload = {
        "resourceType": "Appointment",
        "id": f"appt-{appt_id}",
        "status": "booked",
        "participant": [
            {"actor": {"reference": f"Patient/patient-{patient_id}"}, "status": "accepted"},
            {"actor": {"reference": f"Practitioner/doctor-{provider_id}"}, "status": "accepted"}
        ]
    }
    _put_resource("Appointment", payload["id"], payload)

def sync_care_team(team_id: int, patient_id: int):
    payload = {
        "resourceType": "CareTeam",
        "id": f"team-{team_id}",
        "status": "active",
        "subject": {"reference": f"Patient/patient-{patient_id}"}
    }
    _put_resource("CareTeam", payload["id"], payload)

def sync_task(task_id: int, patient_id: int, description: str):
    payload = {
        "resourceType": "Task",
        "id": f"task-{task_id}",
        "status": "requested",
        "intent": "order",
        "description": description,
        "for": {"reference": f"Patient/patient-{patient_id}"}
    }
    _put_resource("Task", payload["id"], payload)

def sync_communication(comm_id: int, patient_id: int, message: str):
    payload = {
        "resourceType": "Communication",
        "id": f"comm-{comm_id}",
        "status": "completed",
        "subject": {"reference": f"Patient/patient-{patient_id}"},
        "payload": [{"contentString": message}]
    }
    _put_resource("Communication", payload["id"], payload)

def sync_goal(goal_id: int, patient_id: int, description: str):
    payload = {
        "resourceType": "Goal",
        "id": f"goal-{goal_id}",
        "lifecycleStatus": "active",
        "description": {"text": description},
        "subject": {"reference": f"Patient/patient-{patient_id}"}
    }
    _put_resource("Goal", payload["id"], payload)

def sync_risk_assessment(risk_id: int, patient_id: int, prediction: str):
    payload = {
        "resourceType": "RiskAssessment",
        "id": f"risk-{risk_id}",
        "status": "final",
        "subject": {"reference": f"Patient/patient-{patient_id}"},
        "prediction": [{"outcome": {"text": prediction}}]
    }
    _put_resource("RiskAssessment", payload["id"], payload)

def sync_service_request(req_id: int, patient_id: int, service: str):
    payload = {
        "resourceType": "ServiceRequest",
        "id": f"req-{req_id}",
        "status": "active",
        "intent": "order",
        "subject": {"reference": f"Patient/patient-{patient_id}"},
        "code": {"text": service}
    }
    _put_resource("ServiceRequest", payload["id"], payload)

def sync_flag(flag_id: int, patient_id: int, warning: str):
    payload = {
        "resourceType": "Flag",
        "id": f"flag-{flag_id}",
        "status": "active",
        "subject": {"reference": f"Patient/patient-{patient_id}"},
        "code": {"text": warning}
    }
    _put_resource("Flag", payload["id"], payload)

def sync_clinical_impression(imp_id: int, patient_id: int, summary: str):
    payload = {
        "resourceType": "ClinicalImpression",
        "id": f"imp-{imp_id}",
        "status": "completed",
        "subject": {"reference": f"Patient/patient-{patient_id}"},
        "summary": summary
    }
    _put_resource("ClinicalImpression", payload["id"], payload)

def sync_consent(consent_id: int, patient_id: int, org_id: int, status: str, provision_type: str):
    payload = {
        "resourceType": "Consent",
        "id": f"consent-{consent_id}",
        "status": status,
        "scope": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/consentscope", "code": "patient-privacy"}]},
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/consentcategorycodes", "code": "npp"}]}],
        "patient": {"reference": f"Patient/patient-{patient_id}"},
        "dateTime": datetime.datetime.utcnow().isoformat() + "Z",
        "organization": [{"reference": f"Organization/org-{org_id}"}] if org_id else [],
        "provision": {"type": provision_type}
    }
    _put_resource("Consent", payload["id"], payload)

def sync_audit_event(audit_id: int, action: str, user_id: int, outcome: str):
    payload = {
        "resourceType": "AuditEvent",
        "id": f"audit-{audit_id}",
        "type": {"system": "http://terminology.hl7.org/CodeSystem/audit-event-type", "code": "rest"},
        "action": action[:1].upper() if action else "E",
        "recorded": datetime.datetime.utcnow().isoformat() + "Z",
        "outcome": "0" if outcome == "Success" else "4",
        "agent": [{"requestor": True, "who": {"reference": f"Practitioner/doctor-{user_id}"}}],
        "source": {"observer": {"display": "Sentinel HealthOS"}}
    }
    _put_resource("AuditEvent", payload["id"], payload)

def sync_condition(condition_id: int, patient_id: int, code: str, status: str):
    status_map = {"active": "active", "resolved": "resolved"}
    payload = {
        "resourceType": "Condition",
        "id": f"condition-{condition_id}",
        "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": status_map.get(status, "active")}]},
        "code": {"text": code},
        "subject": {"reference": f"Patient/patient-{patient_id}"},
        "recordedDate": datetime.datetime.utcnow().isoformat() + "Z"
    }
    _put_resource("Condition", payload["id"], payload)

def sync_diagnostic_report(report_id: int, patient_id: int, test_name: str, result_value: str, conclusion: str):
    payload = {
        "resourceType": "DiagnosticReport",
        "id": f"report-{report_id}",
        "status": "final",
        "code": {"text": test_name},
        "subject": {"reference": f"Patient/patient-{patient_id}"},
        "issued": datetime.datetime.utcnow().isoformat() + "Z",
        "conclusion": conclusion,
        "presentedForm": [{"contentType": "text/plain", "data": "TUlTS0VORzEwMTEx"}] # Mock base64
    }
    _put_resource("DiagnosticReport", payload["id"], payload)

def sync_coverage(coverage_id: int, patient_id: int, status: str, payor: str, subscriber_id: str):
    payload = {
        "resourceType": "Coverage",
        "id": f"coverage-{coverage_id}",
        "status": status,
        "subscriberId": subscriber_id,
        "beneficiary": {"reference": f"Patient/patient-{patient_id}"},
        "payor": [{"reference": f"Organization/{payor}"}]
    }
    _put_resource("Coverage", payload["id"], payload)

def sync_explanation_of_benefit(eob_id: int, claim_id: int, patient_id: int, provider_id: int, outcome: str, total_cost: float, total_benefit: float):
    payload = {
        "resourceType": "ExplanationOfBenefit",
        "id": f"eob-{eob_id}",
        "status": "active",
        "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/claim-type", "code": "institutional"}]},
        "use": "claim",
        "patient": {"reference": f"Patient/patient-{patient_id}"},
        "created": datetime.datetime.utcnow().isoformat() + "Z",
        "provider": {"reference": f"Practitioner/doctor-{provider_id}"},
        "insurer": {"reference": "Organization/org-default"},
        "outcome": outcome,
        "claim": {"reference": f"Claim/claim-{claim_id}"},
        "total": [
            {"category": {"coding": [{"code": "submitted"}]}, "amount": {"value": total_cost, "currency": "USD"}},
            {"category": {"coding": [{"code": "benefit"}]}, "amount": {"value": total_benefit, "currency": "USD"}}
        ]
    }
    _put_resource("ExplanationOfBenefit", payload["id"], payload)

def sync_measure_report(report_id: int, patient_id: int, score: int, priority: str):
    payload = {
        "resourceType": "MeasureReport",
        "id": f"measure-{report_id}",
        "status": "complete",
        "type": "individual",
        "measure": "http://sentinel-health.os/measure/risk-scoring",
        "subject": {"reference": f"Patient/patient-{patient_id}"},
        "date": datetime.datetime.utcnow().isoformat() + "Z",
        "group": [
            {
                "measureScore": {"value": score},
                "code": {"text": f"Priority: {priority}"}
            }
        ]
    }
    _put_resource("MeasureReport", payload["id"], payload)

    _put_resource("MeasureReport", payload["id"], payload)

def sync_immunization(imm_id: int, patient_id: int, vaccine_code: str, vaccine_name: str, status: str):
    payload = {
        "resourceType": "Immunization",
        "id": f"imm-{imm_id}",
        "status": status,
        "vaccineCode": {"coding": [{"code": vaccine_code, "display": vaccine_name}]},
        "patient": {"reference": f"Patient/patient-{patient_id}"},
        "occurrenceDateTime": datetime.datetime.utcnow().isoformat() + "Z",
        "primarySource": True
    }
    _put_resource("Immunization", payload["id"], payload)

def sync_family_history(fmh_id: int, patient_id: int, relationship_code: str, condition_name: str):
    payload = {
        "resourceType": "FamilyMemberHistory",
        "id": f"fmh-{fmh_id}",
        "status": "completed",
        "patient": {"reference": f"Patient/patient-{patient_id}"},
        "date": datetime.datetime.utcnow().isoformat() + "Z",
        "relationship": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode", "code": relationship_code}]},
        "condition": [{"code": {"coding": [{"display": condition_name}]}}]
    }
    _put_resource("FamilyMemberHistory", payload["id"], payload)

def sync_procedure(proc_id: int, patient_id: int, proc_code: str, proc_name: str, status: str):
    payload = {
        "resourceType": "Procedure",
        "id": f"proc-{proc_id}",
        "status": status,
        "code": {"coding": [{"code": proc_code, "display": proc_name}]},
        "subject": {"reference": f"Patient/patient-{patient_id}"},
        "performedDateTime": datetime.datetime.utcnow().isoformat() + "Z"
    }
    _put_resource("Procedure", payload["id"], payload)

    _put_resource("Procedure", payload["id"], payload)

def sync_medication_administration(med_admin_id: int, patient_id: int, medication_name: str, status: str, dosage: str):
    payload = {
        "resourceType": "MedicationAdministration",
        "id": f"medadmin-{med_admin_id}",
        "status": status,
        "medicationCodeableConcept": {"coding": [{"display": medication_name}]},
        "subject": {"reference": f"Patient/patient-{patient_id}"},
        "effectiveDateTime": datetime.datetime.utcnow().isoformat() + "Z",
        "dosage": {"text": dosage}
    }
    _put_resource("MedicationAdministration", payload["id"], payload)

def sync_medication_dispense(med_dispense_id: int, patient_id: int, medication_name: str, status: str, quantity: str, days_supply: int):
    payload = {
        "resourceType": "MedicationDispense",
        "id": f"meddispense-{med_dispense_id}",
        "status": status,
        "medicationCodeableConcept": {"coding": [{"display": medication_name}]},
        "subject": {"reference": f"Patient/patient-{patient_id}"},
        "quantity": {"value": float(quantity.split()[0]) if quantity and quantity.split()[0].isdigit() else 1},
        "daysSupply": {"value": days_supply},
        "whenHandedOver": datetime.datetime.utcnow().isoformat() + "Z"
    }
    _put_resource("MedicationDispense", payload["id"], payload)

    _put_resource("MedicationDispense", payload["id"], payload)

def sync_questionnaire_response(qr_id: int, patient_id: int, questionnaire_name: str, status: str, answers: dict):
    payload = {
        "resourceType": "QuestionnaireResponse",
        "id": f"qr-{qr_id}",
        "status": status,
        "subject": {"reference": f"Patient/patient-{patient_id}"},
        "authored": datetime.datetime.utcnow().isoformat() + "Z",
        "questionnaire": f"Questionnaire/{questionnaire_name}",
        "item": [{"linkId": str(k), "answer": [{"valueString": str(v)}]} for k, v in answers.items()]
    }
    _put_resource("QuestionnaireResponse", payload["id"], payload)

def sync_document_reference(doc_id: int, patient_id: int, document_type: str, status: str, filename: str):
    payload = {
        "resourceType": "DocumentReference",
        "id": f"doc-{doc_id}",
        "status": "current" if status == "processing" or status == "completed" else "entered-in-error",
        "docStatus": "final",
        "type": {"coding": [{"display": document_type or "Medical Document"}]},
        "subject": {"reference": f"Patient/patient-{patient_id}"},
        "date": datetime.datetime.utcnow().isoformat() + "Z",
        "content": [{"attachment": {"title": filename}}]
    }
    _put_resource("DocumentReference", payload["id"], payload)

    _put_resource("DocumentReference", payload["id"], payload)

def sync_plan_definition(pd_id: int, patient_id: int, title: str, description: str, status: str):
    payload = {
        "resourceType": "PlanDefinition",
        "id": f"pd-{pd_id}",
        "url": f"http://sentinel-health.os/PlanDefinition/pd-{pd_id}",
        "status": status,
        "title": title,
        "description": description,
        "subjectCodeableConcept": {"coding": [{"code": f"Patient/patient-{patient_id}"}]}
    }
    _put_resource("PlanDefinition", payload["id"], payload)

# ==============================================================================
# EXISTING FHIR MAPPINGS
# ==============================================================================

def sync_practitioner(doctor_id: int):
    practitioner_payload = {
        "resourceType": "Practitioner",
        "id": f"doctor-{doctor_id}",
        "identifier": [{"system": "http://sentinel-health.os/practitioner-id", "value": str(doctor_id)}],
        "active": True,
        "name": [{"use": "official", "text": f"Doctor {doctor_id}"}]
    }
    _put_resource("Practitioner", f"doctor-{doctor_id}", practitioner_payload)

def map_to_fhir_patient(patient: Patient) -> dict:
    birth_date = patient.dob.isoformat() if patient.dob else f"{datetime.datetime.now().year - patient.age}-01-01"
    
    fhir_patient = {
        "resourceType": "Patient",
        "id": f"patient-{patient.id}",
        "identifier": [{"system": "http://sentinel-health.os/patient-id", "value": str(patient.id)}],
        "name": [{"use": "official", "family": patient.last_name, "given": [patient.first_name]}],
        "gender": patient.gender.lower() if patient.gender and patient.gender.lower() in ["male", "female", "other", "unknown"] else "unknown",
        "birthDate": birth_date,
        "active": True
    }
    
    if patient.mrn:
        fhir_patient["identifier"].append({
            "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]},
            "system": "http://sentinel-health.os/mrn",
            "value": patient.mrn
        })
        
    if patient.contact_number:
        fhir_patient["telecom"] = [{"system": "phone", "value": patient.contact_number}]
        
    if patient.address:
        fhir_patient["address"] = [{"text": patient.address}]
        
    if patient.primary_doctor_id:
        fhir_patient["generalPractitioner"] = [{"reference": f"Practitioner/doctor-{patient.primary_doctor_id}"}]

    return fhir_patient

def sync_patient_to_fhir(patient: Patient):
    if patient.primary_doctor_id:
        sync_practitioner(patient.primary_doctor_id)
    payload = map_to_fhir_patient(patient)
    _put_resource("Patient", payload["id"], payload)

def sync_device_to_fhir(device: Device):
    payload = {
        "resourceType": "Device",
        "id": f"device-{device.id}",
        "identifier": [{"system": "http://sentinel-health.os/device-id", "value": device.device_id}],
        "status": "active" if device.status == "active" else "inactive",
        "manufacturer": "Sentinel Compatible",
        "modelNumber": device.model or "Unknown",
        "serialNumber": device.serial_number or "Unknown",
        "type": {"text": device.device_type}
    }
    if device.patient_id:
        payload["patient"] = {"reference": f"Patient/patient-{device.patient_id}"}
        
    _put_resource("Device", payload["id"], payload)

def sync_observation_to_fhir(device_id: str, patient_id: int, metric: str, value: float, unit: str):
    loinc_map = {
        "HR": ("8867-4", "Heart rate"),
        "SPO2": ("2708-6", "Oxygen saturation in Arterial blood"),
        "TEMP": ("8310-5", "Body temperature"),
        "RESP": ("9279-1", "Respiratory rate")
    }
    
    code_info = loinc_map.get(metric, ("unknown", metric))
    obs_id = f"obs-{patient_id}-{metric}-{int(datetime.datetime.utcnow().timestamp())}"
    
    payload = {
        "resourceType": "Observation",
        "id": obs_id,
        "status": "final",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
        "code": {"coding": [{"system": "http://loinc.org", "code": code_info[0], "display": code_info[1]}]},
        "subject": {"reference": f"Patient/patient-{patient_id}"},
        "device": {"reference": f"Device/{device_id}"},
        "effectiveDateTime": datetime.datetime.utcnow().isoformat() + "Z",
        "valueQuantity": {"value": value, "unit": unit}
    }
    _put_resource("Observation", obs_id, payload)

def sync_alert_to_fhir(alert: Alert):
    status = "mitigated" if alert.is_resolved else "preliminary"
    
    payload = {
        "resourceType": "DetectedIssue",
        "id": f"alert-{alert.id}",
        "status": status,
        "code": {"text": f"Anomaly: {alert.alert_type} ({alert.metric})"},
        "severity": alert.severity,
        "patient": {"reference": f"Patient/patient-{alert.patient_id}"},
        "identifiedDateTime": alert.timestamp.isoformat() if alert.timestamp else datetime.datetime.utcnow().isoformat() + "Z",
        "detail": alert.message
    }
    
    if alert.ai_insight:
        payload["mitigation"] = [{"action": {"text": "AI Risk Assessment"}, "note": [{"text": alert.ai_insight}]}]
        
    if alert.resolved_at:
        payload["mitigation"].append({"action": {"text": "Clinical Resolution"}, "date": alert.resolved_at.isoformat() + "Z"})
        
    _put_resource("DetectedIssue", payload["id"], payload)

from app.models.document import Document

def sync_document_to_fhir(doc: Document):
    payload = {
        "resourceType": "DocumentReference",
        "id": f"doc-{doc.id}",
        "status": "current",
        "docStatus": "final",
        "type": {"text": doc.document_type or "Clinical Note"},
        "subject": {"reference": f"Patient/patient-{doc.patient_id}"},
        "date": doc.uploaded_at.isoformat() + "Z" if doc.uploaded_at else datetime.datetime.utcnow().isoformat() + "Z",
        "description": f"AI Summarized Document: {doc.filename}",
        "content": [
            {
                "attachment": {
                    "contentType": "text/plain",
                    "title": doc.filename,
                    "data": "U2ltdWxhdGVkQmFzZTY0RGF0YUZvclBERg=="
                }
            }
        ]
    }
    if doc.ai_summary:
        import html
        safe_summary = html.escape(doc.ai_summary).replace("\n", "<br/>")
        payload["text"] = {
            "status": "generated",
            "div": f'<div xmlns="http://www.w3.org/1999/xhtml">{safe_summary}</div>'
        }

    _put_resource("DocumentReference", payload["id"], payload)

from app.models.telehealth import TelehealthSession
from app.models.clinical_note import ClinicalNote

def sync_encounter_to_fhir(session: TelehealthSession):
    status_map = {"scheduled": "planned", "active": "in-progress", "completed": "finished", "cancelled": "cancelled"}
    
    payload = {
        "resourceType": "Encounter",
        "id": f"encounter-{session.id}",
        "status": status_map.get(session.status, "unknown"),
        "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "VR", "display": "virtual"},
        "subject": {"reference": f"Patient/patient-{session.patient_id}"},
        "participant": [{"individual": {"reference": f"Practitioner/doctor-{session.doctor_id}"}}],
        "period": {
            "start": session.scheduled_time.isoformat() + "Z" if session.scheduled_time else datetime.datetime.utcnow().isoformat() + "Z"
        }
    }
    _put_resource("Encounter", payload["id"], payload)

def sync_clinical_note_to_fhir(note: ClinicalNote):
    payload = {
        "resourceType": "DocumentReference",
        "id": f"clinicalnote-{note.id}",
        "status": "current",
        "docStatus": "final" if note.signed else "preliminary",
        "type": {"text": f"AI Generated {note.note_type} Note"},
        "subject": {"reference": f"Patient/patient-{note.patient_id}"},
        "author": [{"reference": f"Practitioner/doctor-{note.doctor_id}"}],
        "date": note.created_at.isoformat() + "Z" if note.created_at else datetime.datetime.utcnow().isoformat() + "Z",
        "description": "Telehealth Visit Summary",
        "context": {"encounter": [{"reference": f"Encounter/encounter-{note.session_id}"}]},
        "text": {
            "status": "generated",
            "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{note.content}</div>"
        }
    }
    _put_resource("DocumentReference", payload["id"], payload)
