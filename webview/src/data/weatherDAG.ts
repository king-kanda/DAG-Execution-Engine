export const weatherDAG = {
  "title": "Weather & Activity Advisor",
  "id": "weather_activity_v1",
  "nodes": [
    {
      "id": "start",
      "type": "FlowNode",
      "position": {"x": 100, "y": 100},
      "data": {
        "label": "Start",
        "description": "Entry point for weather inquiry",
        "iconName": "Zap",
        "color": "#FBBF24",
        "isCustom": false
      }
    },
    {
      "id": "location-extract",
      "type": "FlowNode", 
      "position": {"x": 100, "y": 250},
      "data": {
        "label": "LLM Prompt",
        "description": "Extract location from user query using LLM",
        "iconName": "Brain",
        "color": "#A78BFA", 
        "isCustom": false,
        "required_fields": [],
        "extract_location": true
      }
    },
    {
      "id": "weather-api",
      "type": "FlowNode",
      "position": {"x": -50, "y": 400},
      "data": {
        "label": "API Tools",
        "description": "Fetch current weather data",
        "iconName": "Cloud",
        "color": "#60A5FA",
        "isCustom": false,
        "action_type": "weather_lookup",
        "api_name": "OpenWeatherMap"
      }
    },
    {
      "id": "quote-api", 
      "type": "FlowNode",
      "position": {"x": 250, "y": 400},
      "data": {
        "label": "Integrations",
        "description": "Get inspirational quote",
        "iconName": "Quote", 
        "color": "#34D399",
        "isCustom": false,
        "action_type": "random_quote",
        "api_name": "Quotable"
      }
    },
    {
      "id": "activity-advisor",
      "type": "FlowNode",
      "position": {"x": 100, "y": 550}, 
      "data": {
        "label": "LLM Prompt",
        "description": "Analyze weather and provide activity recommendations",
        "iconName": "Brain",
        "color": "#A78BFA",
        "isCustom": false,
        "required_fields": []
      }
    },
    {
      "id": "end",
      "type": "FlowNode", 
      "position": {"x": 100, "y": 700},
      "data": {
        "label": "End",
        "description": "Return final response to user",
        "iconName": "Component",
        "color": "#6B7280",
        "isCustom": false
      }
    }
  ],
  "edges": [
    {
      "source": "start",
      "target": "location-extract",
      "id": "edge-start-location"
    },
    {
      "source": "location-extract", 
      "target": "weather-api",
      "id": "edge-location-weather"
    },
    {
      "source": "location-extract",
      "target": "quote-api", 
      "id": "edge-location-quote"
    },
    {
      "source": "weather-api",
      "target": "activity-advisor",
      "id": "edge-weather-advisor"
    },
    {
      "source": "quote-api",
      "target": "activity-advisor",
      "id": "edge-quote-advisor"  
    },
    {
      "source": "activity-advisor",
      "target": "end",
      "id": "edge-advisor-end"
    }
  ]
}
