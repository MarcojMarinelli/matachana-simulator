# matachana_130hpo_sim_v2.py
import random
import time
import uuid
import asyncio
import datetime as dt
import logging
import os
from enum import Enum

from fastapi import FastAPI, Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

# --- Basic Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Matachana 130HPO Simulator v2")

# --- Simulation Configuration (from environment variables with defaults) ---
MIN_WAIT_SECONDS = int(os.getenv("MIN_WAIT_SECONDS", 360)) # 6 minutes
MAX_WAIT_SECONDS = int(os.getenv("MAX_WAIT_SECONDS", 600)) # 10 minutes
ALARM_PROBABILITY = float(os.getenv("ALARM_PROBABILITY", 0.05)) # 5% chance

# --- Prometheus Metrics ---
g_cycle_phase   = Gauge("hpo_cycle_phase", "Current cycle phase as enum")
g_pressure_hpa  = Gauge("hpo_chamber_pressure_hpa", "Chamber pressure")
g_temp_c        = Gauge("hpo_chamber_temperature_c", "Chamber temperature")
g_h2o2_ppm      = Gauge("hpo_h2o2_concentration_ppm", "H2O2 concentration")
g_cycles_today  = Gauge("hpo_cycles_today", "Cycles completed today")
g_alarm_code    = Gauge("hpo_alarm_code", "Active alarm code (0 = none)")

# --- Using Enum for Phases for better readability and safety ---
class CyclePhase(str, Enum):
    IDLE = "IDLE"
    PREP = "PREP"
    VACUUM = "VACUUM"
    INJECTION = "INJECTION"
    DIFFUSION = "DIFFUSION"
    AERATION = "AERATION"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"

# --- Possible Alarms ---
ALARM_CODES = {
    42: "Pressure drop too slow",
    58: "H2O2 concentration too low",
    101: "Chamber temperature out of range"
}

# In-memory state of the device
state = {
    "cycle_id": None,
    "phase": CyclePhase.IDLE,
    "pressure_hpa": 1013.0,
    "temp_c": 25.0,
    "h2o2_ppm": 0.0,
    "start_time": None,
    "end_time": None,
    "alarm_code": 0,
    "alarm_message": "No alarm",
    "cycles_completed_today": 0
}

def lerp(v0: float, v1: float, t: float) -> float:
    """Linear interpolation helper for smoother transitions."""
    return v0 + t * (v1 - v0)

@app.on_event("startup")
async def startup_event():
    """Start the simulation loop on application startup."""
    logger.info("Application startup. Starting cycle simulation task.")
    asyncio.create_task(run_cycles())

@app.get("/status")
def get_status():
    """Endpoint to get the current state of the simulator."""
    return state

@app.get("/metrics")
def get_metrics():
    """Endpoint for Prometheus scraping."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

async def run_cycles():
    """Main loop to continuously run sterilization cycles."""
    while True:
        wait_time = random.randint(MIN_WAIT_SECONDS, MAX_WAIT_SECONDS)
        logger.info(f"Next cycle starting in {wait_time} seconds.")
        await asyncio.sleep(wait_time)

        state.update({
            "cycle_id": str(uuid.uuid4())[:8],
            "phase": CyclePhase.PREP,
            "start_time": dt.datetime.utcnow().isoformat(),
            "end_time": None,
            "alarm_code": 0,
            "alarm_message": "No alarm"
        })
        logger.info(f"Starting new cycle ID: {state['cycle_id']}")
        await walk_cycle()

async def walk_cycle():
    """Simulates the progression through a single sterilization cycle."""
    # (Phase, Duration_secs, Target_Pressure, Target_Temp, Target_H2O2)
    phase_steps = [
        (CyclePhase.PREP,      30,  1013.0, 30.0,   0.0),
        (CyclePhase.VACUUM,    120, 50.0,   45.0,   0.0),
        (CyclePhase.INJECTION, 60,  300.0,  50.0,   200.0),
        (CyclePhase.DIFFUSION, 180, 250.0,  48.0,   80.0),
        (CyclePhase.AERATION,  120, 1013.0, 35.0,   0.0)
    ]
    
    last_pressure = state["pressure_hpa"]
    last_temp = state["temp_c"]
    last_h2o2 = state["h2o2_ppm"]

    for phase, duration_s, p_t, t_t, h_t in phase_steps:
        state["phase"] = phase
        logger.info(f"Cycle {state['cycle_id']}: Entering phase '{phase.value}' for {duration_s}s.")
        
        for i in range(duration_s):
            progress = (i + 1) / duration_s
            state["pressure_hpa"] = lerp(last_pressure, p_t, progress) + random.uniform(-2, 2)
            state["temp_c"] = lerp(last_temp, t_t, progress) + random.uniform(-0.5, 0.5)
            state["h2o2_ppm"] = lerp(last_h2o2, h_t, progress) + random.uniform(-5, 5)
            update_metrics()
            await asyncio.sleep(1)
        
        last_pressure, last_temp, last_h2o2 = p_t, t_t, h_t

        # Check for random alarm event
        if random.random() < ALARM_PROBABILITY:
            alarm_code = random.choice(list(ALARM_CODES.keys()))
            state.update({
                "phase": CyclePhase.CANCELLED,
                "alarm_code": alarm_code,
                "alarm_message": ALARM_CODES[alarm_code],
                "end_time": dt.datetime.utcnow().isoformat()
            })
            update_metrics()
            logger.warning(
                f"Cycle {state['cycle_id']}: Cancelled with alarm {alarm_code} "
                f"({state['alarm_message']}) during '{phase.value}' phase."
            )
            return

    # Cycle completed successfully
    state.update({
        "phase": CyclePhase.COMPLETE,
        "cycles_completed_today": state["cycles_completed_today"] + 1,
        "end_time": dt.datetime.utcnow().isoformat()
    })
    update_metrics()
    logger.info(f"Cycle {state['cycle_id']}: Completed successfully.")

def update_metrics():
    """Update Prometheus gauge values from the current state."""
    phase_list = list(CyclePhase)
    g_cycle_phase.set(phase_list.index(state["phase"]))
    g_pressure_hpa.set(state["pressure_hpa"])
    g_temp_c.set(state["temp_c"])
    g_h2o2_ppm.set(max(0, state["h2o2_ppm"])) # Ensure non-negative
    g_cycles_today.set(state["cycles_completed_today"])
    g_alarm_code.set(state["alarm_code"])


if __name__ == "__main__":
    # Note: Prometheus client's start_http_server creates its own thread.
    # Uvicorn should be run directly, not within an asyncio loop.
    from prometheus_client import start_http_server
    import uvicorn

    logger.info("Starting Prometheus metrics server on port 8001.")
    start_http_server(8001)
    
    logger.info("Starting FastAPI server on port 8000.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
