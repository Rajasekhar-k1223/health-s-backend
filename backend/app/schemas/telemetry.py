from pydantic import BaseModel, Field
from typing import List, Union, Any, Optional
from datetime import datetime
from enum import Enum

class MetricType(str, Enum):
    ECG = "ECG"
    HR = "HR"
    SPO2 = "SPO2"
    TEMP = "TEMP"
    RESP = "RESP"
    MOTION = "MOTION"

class TelemetryMetric(BaseModel):
    type: MetricType
    value: Union[float, int, List[float]]  # Float for scalar (HR), List for waveform (ECG)
    unit: str

class TelemetryIngest(BaseModel):
    device_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metrics: List[TelemetryMetric]

# MongoDB Document Schema representation
class TelemetryDataDoc(BaseModel):
    device_id: str
    patient_id: Optional[int] = None
    timestamp: datetime
    type: MetricType
    value: Union[float, int, List[float]]
    unit: str
