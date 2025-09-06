#!/usr/bin/env python3
"""
Test script for the history-preserving JSON merge implementation.
This script simulates multiple updates to organization data and shows how history is preserved.
"""

import json
import copy
from datetime import datetime
from typing import Dict, Any

def history_preserving_merge(existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Append new JSON data to history without replacing existing data.
    This function:
    1. Initializes a _history array if it doesn't exist
    2. Adds a timestamped snapshot of both existing state and new data to the history
    3. Returns the combined data structure with complete history preserved
    
    Args:
        existing_data: The existing JSON data structure
        new_data: The new JSON data to append
        
    Returns:
        The combined data structure with history preserved
    """
    # Create result structure
    result = {}
    
    # Initialize history if it doesn't exist
    if "_history" not in result:
        result["_history"] = []
    
    # Add timestamp for this update
    timestamp = datetime.now().isoformat()
    
    # If existing data has history, copy it to result
    if "_history" in existing_data:
        result["_history"] = copy.deepcopy(existing_data["_history"])
    
    # Store existing data as a snapshot if it's not empty (excluding _history)
    existing_data_copy = copy.deepcopy(existing_data)
    if "_history" in existing_data_copy:
        del existing_data_copy["_history"]
    
    if existing_data_copy:  # Only add if there's actual data besides _history
        result["_history"].append({
            "timestamp": timestamp,
            "data": existing_data_copy
        })
    
    # Store new data as the latest snapshot
    result["_history"].append({
        "timestamp": timestamp,
        "data": copy.deepcopy(new_data)
    })
    
    # Copy all non-history fields from existing data
    for key, value in existing_data.items():
        if key != "_history":
            result[key] = copy.deepcopy(value)
    
    # Add all fields from new data (this will overwrite existing fields)
    for key, value in new_data.items():
        result[key] = copy.deepcopy(value)
    
    return result

def deep_merge(existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new dictionary with data from both sources.
    This version doesn't modify the input dictionaries but creates a new result.
    
    Args:
        existing_data: The existing data dictionary
        new_data: The new data dictionary to incorporate
        
    Returns:
        A new dictionary containing data from both sources
    """
    # Create a new result dictionary to avoid modifying inputs
    result = copy.deepcopy(existing_data)
    
    # Process each key in new_data
    for key, value in new_data.items():
        # Skip the _history key as it's handled separately
        if key == "_history":
            continue
            
        if key in result:
            if isinstance(value, dict) and isinstance(result[key], dict):
                # For nested dictionaries, recursively create a new merged dictionary
                result[key] = deep_merge(result[key], value)
            elif isinstance(value, list) and isinstance(result[key], list):
                # For lists, create a new list with all unique items
                combined_list = copy.deepcopy(result[key])
                for item in value:
                    if item != "N/A" and item not in combined_list:
                        combined_list.append(item)
                result[key] = combined_list
            else:
                # For scalar values, use the new value if it's not N/A
                if value != "N/A":
                    result[key] = copy.deepcopy(value)
        else:
            # Add new key-value pair
            result[key] = copy.deepcopy(value)
    
    return result

def main():
    # Load test data
    with open('Docs/test1.json', 'r') as f:
        # The file contains a JSON string that needs to be parsed twice
        test_data = json.loads(json.loads(f.read()))
    
    print("=== Initial Data Structure ===")
    print(json.dumps(test_data, indent=2)[:500] + "...\n")
    
    # Simulate initial organization data
    org_data = {
        "org_name": "Test Organization",
        "created_at": "2025-09-01T10:00:00"
    }
    
    print("=== First Update: Initial Organization Data ===")
    print(json.dumps(org_data, indent=2))
    
    # First update - add patient data
    merged_data = history_preserving_merge(org_data, test_data)
    
    print("\n=== After First Merge ===")
    print("History entries:", len(merged_data.get("_history", [])))
    print("History sample:", json.dumps(merged_data.get("_history", [])[:1], indent=2))
    print("Patient name:", merged_data.get("patient_info", {}).get("name"))
    
    # Second update - update patient info
    update_data = {
        "patient_info": {
            "name": "Ashwin Kumar",
            "age": "32",
            "gender": "Male"
        },
        "insights": {
            "Diagnosis": ["Hypertension", "Type 2 Diabetes"]
        }
    }
    
    print("\n=== Second Update: Additional Patient Data ===")
    print(json.dumps(update_data, indent=2))
    
    # Apply second update
    merged_data = history_preserving_merge(merged_data, update_data)
    
    print("\n=== After Second Merge ===")
    print("History entries:", len(merged_data.get("_history", [])))
    print("Patient info:", json.dumps(merged_data.get("patient_info", {}), indent=2))
    print("Diagnosis:", merged_data.get("insights", {}).get("Diagnosis", []))
    
    # Third update - add treatment plan
    update_data = {
        "insights": {
            "Treatment Plan": [
                "Metformin 500mg twice daily",
                "Lisinopril 10mg once daily",
                "Diet and exercise counseling"
            ]
        }
    }
    
    print("\n=== Third Update: Treatment Plan ===")
    print(json.dumps(update_data, indent=2))
    
    # Apply third update
    merged_data = history_preserving_merge(merged_data, update_data)
    
    print("\n=== After Third Merge ===")
    print("History entries:", len(merged_data.get("_history", [])))
    print("Treatment Plan:", merged_data.get("insights", {}).get("Treatment Plan", []))
    
    # Show full history
    print("\n=== Full History ===")
    for i, entry in enumerate(merged_data.get("_history", [])):
        print(f"Entry {i+1} - {entry.get('timestamp')}")
        print(f"  Data sample: {json.dumps(entry.get('data'))[:100]}...")
    
    print("\n=== Final Merged Data Structure ===")
    # Remove history from the output to keep it readable
    final_data = copy.deepcopy(merged_data)
    if "_history" in final_data:
        del final_data["_history"]
    print(json.dumps(final_data, indent=2)[:500] + "...\n")
    
    print("=== Vector DB Search Implications ===")
    print("With this history-preserving approach, your vector DB can now search across:")
    print("1. Current state of the data (merged result)")
    print("2. Historical snapshots of all updates")
    print("3. Complete evolution of patient records over time")
    print("\nThis enables powerful temporal queries like:")
    print("- 'Show me all patients whose diagnosis changed from X to Y'")
    print("- 'Find treatment plans that were modified after initial consultation'")
    print("- 'Identify patterns in how patient data evolves over time'")

if __name__ == "__main__":
    main()
