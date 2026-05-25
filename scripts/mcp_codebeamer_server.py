import os
import json
import logging
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

# Setup logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp-codebeamer")

# Initialize FastMCP Server
mcp = FastMCP("codebeamer")

# Mock database file for local testing when no Codebeamer server is configured
MOCK_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Database",
    "codebeamer_mock.json",
)


def ensure_mock_db():
    """Initializes the mock database if it doesn't exist."""
    db_dir = os.path.dirname(MOCK_DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    if not os.path.exists(MOCK_DB_PATH):
        # Default mock requirements tracker database for ASPICE
        default_db = {
            "trackers": [
                {
                    "id": 1001,
                    "name": "System Requirements Specification (SYS.2)",
                    "type": "Requirements",
                },
                {
                    "id": 1002,
                    "name": "System Architectural Design (SYS.3)",
                    "type": "Architecture",
                },
                {
                    "id": 1003,
                    "name": "System Integration & Verification (SYS.4)",
                    "type": "Testing",
                },
            ],
            "items": [
                {
                    "id": 5001,
                    "trackerId": 1001,
                    "name": "SYS_REQ_001: Vehicle Speed Estimation",
                    "description": "The control system shall estimate the vehicle speed with an accuracy of +/- 0.5 km/h.",
                    "status": "Draft",
                    "component": "SpeedEstimator",
                    "aspice_ref": "SYS.2.BP1",
                },
                {
                    "id": 5002,
                    "trackerId": 1001,
                    "name": "SYS_REQ_002: Steering Angle Sensor Input",
                    "description": "The control system shall read and filter steering angle raw sensor input at 100Hz.",
                    "status": "In Progress",
                    "component": "SteeringControl",
                    "aspice_ref": "SYS.2.BP2",
                },
                {
                    "id": 5003,
                    "trackerId": 1002,
                    "name": "SYS_ARC_001: Sensor Abstraction Layer Component",
                    "description": "Defines the architecture and interfaces for raw sensor abstraction components.",
                    "status": "Draft",
                    "component": "SensorAbstraction",
                    "aspice_ref": "SYS.3.BP1",
                },
            ],
        }
        with open(MOCK_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(default_db, f, indent=2)


ensure_mock_db()


def load_mock_db() -> Dict[str, Any]:
    ensure_mock_db()
    with open(MOCK_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_mock_db(data: Dict[str, Any]):
    with open(MOCK_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@mcp.tool()
def list_trackers() -> str:
    """List all trackers in Codebeamer (e.g. Requirements, Architecture, Testing)."""
    logger.info("Listing Codebeamer trackers")
    # For now, we use the mock database.
    # A real implementation would hit: GET {CODEBEAMER_URL}/api/v3/trackers
    db = load_mock_db()
    return json.dumps(db["trackers"], indent=2)


@mcp.tool()
def get_tracker_items(tracker_id: int) -> str:
    """Get all items/requirements in a specific tracker by ID."""
    logger.info(f"Retrieving items for tracker ID: {tracker_id}")
    # Real implementation: GET {CODEBEAMER_URL}/api/v3/trackers/{tracker_id}/items
    db = load_mock_db()
    items = [item for item in db["items"] if item["trackerId"] == tracker_id]
    return json.dumps(items, indent=2)


@mcp.tool()
def get_item_details(item_id: int) -> str:
    """Get detailed information for a specific tracker item/requirement by ID."""
    logger.info(f"Retrieving details for item ID: {item_id}")
    db = load_mock_db()
    for item in db["items"]:
        if item["id"] == item_id:
            return json.dumps(item, indent=2)
    return json.dumps({"error": f"Item {item_id} not found"}, indent=2)


@mcp.tool()
def update_item_status(item_id: int, status: str) -> str:
    """Update the status of a requirements item in Codebeamer (e.g., Draft, Review, Approved)."""
    logger.info(f"Updating item {item_id} status to: {status}")
    db = load_mock_db()
    for item in db["items"]:
        if item["id"] == item_id:
            item["status"] = status
            save_mock_db(db)
            return json.dumps({"success": True, "item": item}, indent=2)
    return json.dumps(
        {"success": False, "error": f"Item {item_id} not found"}, indent=2
    )


@mcp.tool()
def create_item(
    tracker_id: int, name: str, description: str, component: str, aspice_ref: str
) -> str:
    """Create a new requirement tracker item in Codebeamer according to ASPICE."""
    logger.info(f"Creating new item in tracker {tracker_id}: {name}")
    db = load_mock_db()

    # Generate new ID
    new_id = max([item["id"] for item in db["items"]]) + 1 if db["items"] else 5001

    new_item = {
        "id": new_id,
        "trackerId": tracker_id,
        "name": name,
        "description": description,
        "status": "Draft",
        "component": component,
        "aspice_ref": aspice_ref,
    }

    db["items"].append(new_item)
    save_mock_db(db)
    return json.dumps({"success": True, "item": new_item}, indent=2)


if __name__ == "__main__":
    # Start the FastMCP server (standard stdio)
    mcp.run()
