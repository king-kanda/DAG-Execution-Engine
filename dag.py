dag_flow ={
  "title": "Nexus Wave Demo WorkFlow",
  "id": "loan_sop_v1",
  "nodes": [
    {
      "id": "1",
      "type": "FlowNode",
      "position": {
        "x": -150,
        "y": 304
      },
      "data": {
        "label": "Start",
        "description": "Entry point of the workflow or user interaction.",
        "iconName": "Zap",
        "color": "#FBBF24",
        "isCustom": False
      },
      "measured": {
        "width": 322,
        "height": 90
      },
      "selected": False,
      "dragging": False
    },
    {
      "id": "732f8e26-dbf6-4266-af1b-3edb838e19da",
      "type": "FlowNode",
      "position": {
        "x": 342.09634375274953,
        "y": 155.38698124945012
      },
      "data": {
        "label": "Integrations",
        "description": "Connects external services like CRMs, databases, or third-party APIs.",
        "iconName": "Bolt",
        "color": "#34D399",
        "isCustom": False,
        "connectedAPI": {
          "id": "zoho",
          "name": "Zoho CRM",
          "description": "Complete CRM solution for businesses",
          "category": "CRM",
          "image_url": "https://www.logo.wine/a/logo/Zoho/Zoho-Logo.wine.svg",
          "authType": "OAuth2",
          "baseUrl": "https://www.zohoapis.com/crm/v2"
        }
      },
      "measured": {
        "width": 322,
        "height": 106
      },
      "selected": False,
      "dragging": False
    },
    {
      "id": "d372edda-8e42-45ac-9c03-d5b01f9dedb8",
      "type": "FlowNode",
      "position": {
        "x": 332.62889062912416,
        "y": 425.08047187417515
      },
      "data": {
        "label": "API Tools",
        "description": "Configure external APIs, set AI behavior, and environment settings.",
        "iconName": "Globe",
        "color": "#60A5FA",
        "isCustom": False,
        "connectedAPI": {
          "id": "ad7e7b82-19c4-4ee5-be2c-404ed5ed208d",
          "name": "Hubspot Custome Messeger",
          "description": "+6\n[poiho",
          "category": "API",
          "icon": {
            "type": {},
            "key": None,
            "ref": None,
            "props": {
              "size": 20
            },
            "_owner": None,
            "_store": {}
          },
          "authType": "Authenticated",
          "baseUrl": "http://localhost:8000/products",
          "httpMethod": "POST",
          "apiStyle": "raw",
          "target": "virtual_agent",
          "rawBodyStructure": "\n][puoigtiufdycghjvkbjugvjboj",
          "outputBodyStructure": "kvhcjg, hiylvchl lguyv",
          "formDataKeys": {},
          "xFormDataKeys": {},
          "queryParams": {},
          "httpHeaders": {}
        }
      },
      "measured": {
        "width": 322,
        "height": 106
      },
      "selected": False,
      "dragging": False
    },
    {
      "id": "dc0471ff-a8b3-4b33-9d09-fac14dc7a231",
      "type": "FlowNode",
      "position": {
        "x": 786.03125,
        "y": 271
      },
      "data": {
        "label": "LLM Prompt",
        "description": "Formats and sends prompts to the language model to generate smart replies.",
        "required_fields": ["id_number"],
        "iconName": "Brain",
        "color": "#A78BFA",
        "isCustom": False,
        "customInstructions": "\n\\]'[;plokjhgfdsgcgxgxgxg"
      },
      "measured": {
        "width": 322,
        "height": 106
      },
      "selected": True,
      "dragging": False
    },
    {
      "id": "c8ffc22a-004d-43c2-9e9c-bba903b7505d",
      "type": "FlowNode",
      "position": {
        "x": 1218.2890625,
        "y": 277
      },
      "data": {
        "label": "End",
        "description": "Final step in the workflow or response cycle.",
        "iconName": "Component",
        "color": "#6B7280",
        "isCustom": False
      },
      "measured": {
        "width": 322,
        "height": 90
      },
      "selected": False,
      "dragging": False
    }
  ],
  "edges": [
    {
      "source": "1",
      "target": "732f8e26-dbf6-4266-af1b-3edb838e19da",
      "id": "xy-edge__1-732f8e26-dbf6-4266-af1b-3edb838e19da"
    },
    {
      "source": "1",
      "target": "d372edda-8e42-45ac-9c03-d5b01f9dedb8",
      "id": "xy-edge__1-d372edda-8e42-45ac-9c03-d5b01f9dedb8"
    },
    {
      "source": "732f8e26-dbf6-4266-af1b-3edb838e19da",
      "target": "dc0471ff-a8b3-4b33-9d09-fac14dc7a231",
      "id": "xy-edge__732f8e26-dbf6-4266-af1b-3edb838e19da-dc0471ff-a8b3-4b33-9d09-fac14dc7a231"
    },
    {
      "source": "d372edda-8e42-45ac-9c03-d5b01f9dedb8",
      "target": "dc0471ff-a8b3-4b33-9d09-fac14dc7a231",
      "id": "xy-edge__d372edda-8e42-45ac-9c03-d5b01f9dedb8-dc0471ff-a8b3-4b33-9d09-fac14dc7a231"
    },
    {
      "source": "dc0471ff-a8b3-4b33-9d09-fac14dc7a231",
      "target": "c8ffc22a-004d-43c2-9e9c-bba903b7505d",
      "id": "xy-edge__dc0471ff-a8b3-4b33-9d09-fac14dc7a231-c8ffc22a-004d-43c2-9e9c-bba903b7505d"
    }
  ]
}