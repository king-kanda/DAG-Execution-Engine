import redis

# -------------------- Mock Redis --------------------
r = redis.Redis(host='localhost', port=6379, db=0)


class MockRedis:

    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, db=0)

    def get(self, key):
        return self.r.get(key)

    def set(self, key, value):
        self.r.set(key, value)

    def delete(self, key):
        if key in self.r:
            del self.r[key]


# -------------------- Sample DAG --------------------
sample_sop = {
    "title":
    "Nexus Wave Demo WorkFlow",
    "id":
    "loan_sop_v1",
    "nodes": [{
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
            "isCustom": "false"
        },
        "measured": {
            "width": 322,
            "height": 90
        },
        "selected": "false",
        "dragging": "false"
    }, {
        "id": "732f8e26-dbf6-4266-af1b-3edb838e19da",
        "type": "FlowNode",
        "position": {
            "x": 342.09634375274953,
            "y": 155.38698124945012
        },
        "data": {
            "label": "Integrations",
            "description":
            "Connects external services like CRMs, databases, or third-party APIs.",
            "iconName": "Bolt",
            "color": "#34D399",
            "isCustom": "false",
            "connectedAPI": {
                "id": "zoho",
                "name": "Zoho CRM",
                "description": "Complete CRM solution for businesses",
                "category": "CRM",
                "image_url":
                "https://www.logo.wine/a/logo/Zoho/Zoho-Logo.wine.svg",
                "authType": "OAuth2",
                "baseUrl": "https://www.zohoapis.com/crm/v2"
            }
        },
        "measured": {
            "width": 322,
            "height": 106
        },
        "selected": "false",
        "dragging": "false"
    }, {
        "id": "d372edda-8e42-45ac-9c03-d5b01f9dedb8",
        "type": "FlowNode",
        "position": {
            "x": 332.62889062912416,
            "y": 425.08047187417515
        },
        "data": {
            "label": "API Tools",
            "description":
            "Configure external APIs, set AI behavior, and environment settings.",
            "iconName": "Globe",
            "color": "#60A5FA",
            "isCustom": "false",
            "connectedAPI": {
                "id": "ad7e7b82-19c4-4ee5-be2c-404ed5ed208d",
                "name": "Hubspot Custome Messeger",
                "description": "+6\n[poiho",
                "category": "API",
                "icon": {
                    "type": {},
                    "key": 'null',
                    "ref": 'null',
                    "props": {
                        "size": 20
                    },
                    "_owner": 'null',
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
        "selected": "false",
        "dragging": "false"
    }, {
        "id": "dc0471ff-a8b3-4b33-9d09-fac14dc7a231",
        "type": "FlowNode",
        "position": {
            "x": 786.03125,
            "y": 271
        },
        "data": {
            "label": "LLM Prompt",
            "description":
            "Formats and sends prompts to the language model to generate smart replies.",
            "required_fields": ["id_number"],
            "iconName": "Brain",
            "color": "#A78BFA",
            "isCustom": "false",
            "customInstructions": "\n\\]'[;plokjhgfdsgcgxgxgxg"
        },
        "measured": {
            "width": 322,
            "height": 106
        },
        "selected": "false",
        "dragging": "false"
    }, {
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
            "isCustom": "false"
        },
        "measured": {
            "width": 322,
            "height": 90
        },
        "selected": "false",
        "dragging": "false"
    }],
    "edges": [{
        "source": "1",
        "target": "732f8e26-dbf6-4266-af1b-3edb838e19da",
        "id": "xy-edge__1-732f8e26-dbf6-4266-af1b-3edb838e19da"
    }, {
        "source": "1",
        "target": "0da4b9c4-15b1-46e4-8e24-46875799f047",
        "id": "xy-edge__1-0da4b9c4-15b1-46e4-8e24-46875799f047"
    }, {
        "source": "1",
        "target": "d372edda-8e42-45ac-9c03-d5b01f9dedb8",
        "id": "xy-edge__1-d372edda-8e42-45ac-9c03-d5b01f9dedb8"
    }, {
        "source":
        "732f8e26-dbf6-4266-af1b-3edb838e19da",
        "target":
        "dc0471ff-a8b3-4b33-9d09-fac14dc7a231",
        "id":
        "xy-edge__732f8e26-dbf6-4266-af1b-3edb838e19da-dc0471ff-a8b3-4b33-9d09-fac14dc7a231"
    }, {
        "source":
        "d372edda-8e42-45ac-9c03-d5b01f9dedb8",
        "target":
        "dc0471ff-a8b3-4b33-9d09-fac14dc7a231",
        "id":
        "xy-edge__d372edda-8e42-45ac-9c03-d5b01f9dedb8-dc0471ff-a8b3-4b33-9d09-fac14dc7a231"
    }, {
        "source":
        "dc0471ff-a8b3-4b33-9d09-fac14dc7a231",
        "target":
        "c8ffc22a-004d-43c2-9e9c-bba903b7505d",
        "id":
        "xy-edge__dc0471ff-a8b3-4b33-9d09-fac14dc7a231-c8ffc22a-004d-43c2-9e9c-bba903b7505d"
    }]
}


# -------------------- Node Executors --------------------
class BaseNodeExecutor:

    def __init__(self, node, context):
        self.node = node
        self.context = context

    def execute(self):
        raise NotImplementedError


class StartNodeExecutor(BaseNodeExecutor):

    def execute(self):
        print("🚀 Start Node")
        return "OK"


class LLMInputNodeExecutor(BaseNodeExecutor):

    def execute(self):
        required_fields = self.node["data"]["required_fields"]
        prompt = self.node["data"]["description"]
        missing = [
            field for field in required_fields if field not in self.context
        ]

        if missing:
            print(f"💬 Prompt to user: {prompt}")
            return "WAIT"
        else:
            print(f"✅ Required info found: {required_fields}")
            return "OK"


class ActionNodeExecutor(BaseNodeExecutor):

    def execute(self):
        action_type = self.node["data"].get("action_type")
        if action_type == "check_eligibility":
            print("🧠 Checking eligibility based on provided ID...")
            return "OK"
        return "OK"


class EndNodeExecutor(BaseNodeExecutor):

    def execute(self):
        print("🏁 Reached End Node")
        return "END"


# Registry for pluggable node execution
NODE_EXECUTORS = {
    "Start": StartNodeExecutor,
    "LLM Prompt": LLMInputNodeExecutor,  #this will represent llm input node
    "API Tools": ActionNodeExecutor,  #this will represent api tool
    "Integrations": ActionNodeExecutor,  #this will represent integrations
    "End": EndNodeExecutor
}


# -------------------- SOP Executor Engine --------------------
class SOPExecutor:

    def __init__(self, sop, chat_context, conversation_id, redis_client):
        self.sop = sop
        self.context = chat_context
        self.conversation_id = conversation_id
        self.r = redis_client
        self.state_key = f"sop_exec:{sop['id']}:{conversation_id}"
        self.node_map = {n["id"]: n for n in sop["nodes"]}
        self.edge_map = self.build_edge_map(sop["edges"])
        self.current_node_id = self.load_state()

    def build_edge_map(self, edges):
        edge_map = {}
        for e in edges:
            edge_map.setdefault(e["source"], []).append(e["target"])
        return edge_map

    def load_state(self):
        state = self.r.get(self.state_key)
        if state:
            return state.decode('utf-8') if isinstance(state, bytes) else state
        return self.find_start_node()

    def save_state(self, node_id):
        if node_id:
            self.r.set(self.state_key, node_id)

    def find_start_node(self):
        for node in self.sop["nodes"]:
            if node["data"]["label"] == "Start":
                return node["id"]
        raise Exception("Start node not found")

    def get_next_node(self, node_id):
        return self.edge_map.get(node_id, [None])[0]

    def run(self):
        while self.current_node_id:
            node = self.node_map[self.current_node_id]
            result = self.handle_node(node)

            if result == "WAIT":
                print("⏸️ Waiting for user input...")
                return
            elif result == "END":
                print("✅ SOP complete. Cleaning up.")
                self.r.delete(self.state_key)
                return

            self.current_node_id = self.get_next_node(self.current_node_id)
            self.save_state(self.current_node_id)

    def handle_node(self, node):
        node_type = node["data"]["label"]
        executor_class = NODE_EXECUTORS.get(node_type)

        if not executor_class:
            raise Exception(f"No executor found for node type: {node_type}")

        executor = executor_class(node, self.context)
        print(f"➡️ Executing Node {node['id']} [{node_type}]")
        return executor.execute()


# -------------------- Test Run --------------------
if __name__ == "__main__":
    redis_client = MockRedis()
    conversation_id = "conv-001"

    print("\n=== First Run (Missing ID Number) ===")
    chat_context = {}  # Simulating no input yet
    executor = SOPExecutor(sample_sop, chat_context, conversation_id,
                           redis_client)
    executor.run()

    print("\n=== Second Run (User Provided ID Number) ===")
    chat_context = {"id_number": "12345678"}  # Now user replied
    executor = SOPExecutor(sample_sop, chat_context, conversation_id,
                           redis_client)
    executor.run()
