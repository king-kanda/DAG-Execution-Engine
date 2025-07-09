import redis
from dag import dag_flow
from collections import deque, defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
import time
from typing import Dict, List, Any, Optional


class MockRedis:
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    def get(self, key):
        return self.r.get(key)

    def set(self, key, value):
        self.r.set(key, value)

    def delete(self, key):
        self.r.delete(key)
    
    def lpush(self, key, *values):
        return self.r.lpush(key, *values)
    
    def rpush(self, key, *values):
        return self.r.rpush(key, *values)
    
    def lpop(self, key):
        return self.r.lpop(key)
    
    def llen(self, key):
        return self.r.llen(key)
    
    def hset(self, name, key, value):
        return self.r.hset(name, key, value)
    
    def hget(self, name, key):
        return self.r.hget(name, key)
    
    def hgetall(self, name):
        return self.r.hgetall(name)

# -------------------- Context Management --------------------
class ConversationalContext:
    """Manages the conversational context and metadata for SOP execution"""
    
    def __init__(self, conversation_id: str, sop_id: str, initial_context: Dict[str, Any] = None):
        self.conversation_id = conversation_id
        self.sop_id = sop_id
        self.chat_context = initial_context or {}
        self.action_outputs = []
        self.conversation_history = []
        
    def add_user_message(self, message: str):
        """Add user message to conversation history"""
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": time.time()
        })
        
    def add_assistant_message(self, message: str):
        """Add assistant message to conversation history"""
        self.conversation_history.append({
            "role": "assistant", 
            "content": message,
            "timestamp": time.time()
        })
        
    def add_action_output(self, node_id: str, action_type: str, output: Any):
        """Add action output to context"""
        self.action_outputs.append({
            "node_id": node_id,
            "action_type": action_type,
            "output": output,
            "timestamp": time.time()
        })
        
    def update_chat_context(self, key: str, value: Any):
        """Update chat context with new information"""
        self.chat_context[key] = value
        
    def get_context_value(self, key: str) -> Any:
        """Get value from chat context"""
        return self.chat_context.get(key)
        
    def has_required_fields(self, required_fields: List[str]) -> tuple[bool, List[str]]:
        """Check if all required fields are present in context"""
        missing = [field for field in required_fields if field not in self.chat_context]
        return len(missing) == 0, missing
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for Redis storage"""
        return {
            "chat_context": self.chat_context,
            "action_outputs": self.action_outputs,
            "conversation_history": self.conversation_history
        }
        
    @classmethod
    def from_dict(cls, conversation_id: str, sop_id: str, data: Dict[str, Any]):
        """Create context from dictionary loaded from Redis"""
        context = cls(conversation_id, sop_id)
        context.chat_context = data.get("chat_context", {})
        context.action_outputs = data.get("action_outputs", [])
        context.conversation_history = data.get("conversation_history", [])
        return context

# -------------------- Sample DAG --------------------
sample_sop = dag_flow

# -------------------- Node Executors --------------------
# -------------------- Node Executors --------------------
class BaseNodeExecutor:
    def __init__(self, node, context: ConversationalContext):
        self.node = node
        self.context = context

    def execute(self):
        raise NotImplementedError

class StartNodeExecutor(BaseNodeExecutor):
    def execute(self):
        print(f"🚀 Start Node [{self.node['id']}]")
        return "OK"

class ActionExecutor(BaseNodeExecutor):
    """Action executor - extracts data from context, calls API, stores output"""
    
    def execute(self):
        action_type = self.node["data"].get("action_type")
        node_label = self.node["data"]["label"]
        print(f"🔧 Executing Action: {node_label} [{self.node['id']}]")
        
        # Extract data from current context
        input_data = self._extract_input_data()
        
        # Simulate API call based on action type
        api_output = self._call_api(action_type, input_data)
        
        # Store output in context
        self.context.add_action_output(
            node_id=self.node['id'],
            action_type=action_type,
            output=api_output
        )
        
        print(f"✅ Action completed: {api_output}")
        return "OK"
    
    def _extract_input_data(self) -> Dict[str, Any]:
        """Extract required data from chat context and previous action outputs"""
        input_data = {}
        
        # Get data from chat context
        for key, value in self.context.chat_context.items():
            input_data[key] = value
            
        # Get data from previous action outputs
        for action_output in self.context.action_outputs:
            input_data[f"action_{action_output['node_id']}_output"] = action_output['output']
            
        return input_data
    
    def _call_api(self, action_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate API call based on action type"""
        # Simulate processing time
        import time
        time.sleep(0.5)
        
        if action_type == "check_eligibility":
            id_number = input_data.get("id_number", "unknown")
            return {
                "eligibility_status": "eligible",
                "id_verified": True,
                "id_number": id_number,
                "verification_timestamp": time.time()
            }
        elif action_type == "zoho_crm_lookup":
            return {
                "customer_found": True,
                "customer_data": {"name": "John Doe", "tier": "premium"},
                "lookup_timestamp": time.time()
            }
        elif action_type == "hubspot_integration":
            return {
                "message_sent": True,
                "message_id": "msg_12345",
                "delivery_timestamp": time.time()
            }
        else:
            return {
                "action_completed": True,
                "timestamp": time.time()
            }

class NaturalLanguageInstructionsExecutor(BaseNodeExecutor):
    """Natural language instructions executor with requirement checking"""
    
    def execute(self):
        instructions = self.node["data"].get("description", "")
        required_fields = self.node["data"].get("required_fields", [])
        
        print(f"🧠 Executing NL Instructions: [{self.node['id']}]")
        
        # Check 1: Required information from customer
        if required_fields:
            has_all_fields, missing_fields = self.context.has_required_fields(required_fields)
            
            if not has_all_fields:
                print(f"💬 Missing required fields: {missing_fields}")
                print(f"📝 Prompt: {instructions}")
                
                # Store that we're waiting for this information
                self.context.add_assistant_message(f"I need the following information: {', '.join(missing_fields)}. {instructions}")
                return "WAIT"
        
        # Check 2: Execute natural language instructions
        nl_output = self._execute_instructions(instructions)
        
        # Store output in context
        self.context.add_action_output(
            node_id=self.node['id'],
            action_type="natural_language_processing",
            output=nl_output
        )
        
        print(f"✅ NL Instructions completed: {nl_output}")
        return "OK"
    
    def _execute_instructions(self, instructions: str) -> Dict[str, Any]:
        """Process natural language instructions"""
        # Simulate NL processing
        import time
        time.sleep(0.3)
        
        return {
            "instructions_processed": True,
            "instructions": instructions,
            "context_summary": f"Processed instructions with {len(self.context.chat_context)} context items",
            "timestamp": time.time()
        }

class EndNodeExecutor(BaseNodeExecutor):
    def execute(self):
        print(f"🏁 Reached End Node [{self.node['id']}]")
        
        # Compile final response data for Virtual Agent
        final_data = {
            "execution_completed": True,
            "chat_context": self.context.chat_context,
            "action_outputs": self.context.action_outputs,
            "conversation_history": self.context.conversation_history,
            "completion_timestamp": time.time()
        }
        
        return {"status": "END", "data": final_data}

# Registry for pluggable node execution
NODE_EXECUTORS = {
    "Start": StartNodeExecutor,
    "LLM Prompt": NaturalLanguageInstructionsExecutor,
    "API Tools": ActionExecutor,
    "Integrations": ActionExecutor,
    "End": EndNodeExecutor
}

# -------------------- Redis-Based SOP Executor Engine --------------------
class RedisSOPExecutor:
    def __init__(self, sop, conversation_id: str, redis_client: MockRedis, initial_context: Dict[str, Any] = None):
        self.sop = sop
        self.conversation_id = conversation_id
        self.sop_id = sop["id"]
        self.r = redis_client
        
        # Generate Redis keys using hash of conversation_id + sop_id
        self.queue_key = self._generate_queue_key()
        self.metadata_key = self._generate_metadata_key()
        
        # Initialize conversational context
        self.context = ConversationalContext(conversation_id, self.sop_id, initial_context)
        
        # Create node map for quick lookup
        self.node_map = {n["id"]: n for n in sop["nodes"]}
        
    def _generate_queue_key(self) -> str:
        """Generate Redis queue key using hash of conversation_id + sop_id"""
        combined = f"{self.conversation_id}_{self.sop_id}"
        hash_obj = hashlib.md5(combined.encode())
        return f"sop_queue:{hash_obj.hexdigest()}"
    
    def _generate_metadata_key(self) -> str:
        """Generate Redis metadata key using hash of conversation_id + sop_id + '_metadata'"""
        combined = f"{self.conversation_id}_{self.sop_id}_metadata"
        hash_obj = hashlib.md5(combined.encode())
        return f"sop_metadata:{hash_obj.hexdigest()}"
    
    def _build_topological_order(self) -> List[str]:
        """Build topological order of nodes for queue initialization"""
        # Build graph
        outgoing = defaultdict(list)
        in_degree = defaultdict(int)
        
        # Initialize all nodes with 0 in-degree
        for node in self.sop["nodes"]:
            in_degree[node["id"]] = 0
            
        # Build the graph from edges
        for edge in self.sop["edges"]:
            source = edge["source"]
            target = edge["target"]
            
            # Skip edges that reference non-existent nodes
            if source in self.node_map and target in self.node_map:
                outgoing[source].append(target)
                in_degree[target] += 1
        
        # Topological sort using Kahn's algorithm
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        topo_order = []
        
        while queue:
            current = queue.popleft()
            topo_order.append(current)
            
            # Reduce in-degree for dependent nodes
            for neighbor in outgoing[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return topo_order
    
    def initialize_redis_queue(self):
        """Initialize Redis queue with nodes in topological order"""
        print(f"🔄 Initializing Redis queue: {self.queue_key}")
        
        # Clear existing queue
        self.r.delete(self.queue_key)
        
        # Get topological order
        topo_order = self._build_topological_order()
        print(f"📋 Topological order: {topo_order}")
        
        # Push nodes to queue in topological order (right push)
        for node_id in topo_order:
            self.r.rpush(self.queue_key, node_id)
        
        print(f"✅ Queue initialized with {len(topo_order)} nodes")
    
    def initialize_redis_metadata(self):
        """Initialize Redis metadata with chat context and action outputs"""
        print(f"🔄 Initializing Redis metadata: {self.metadata_key}")
        
        # Clear existing metadata
        self.r.delete(self.metadata_key)
        
        # Store initial context as JSON
        metadata = self.context.to_dict()
        self.r.hset(self.metadata_key, "data", json.dumps(metadata))
        
        print(f"✅ Metadata initialized")
    
    def load_context_from_redis(self):
        """Load conversational context from Redis metadata"""
        metadata_json = self.r.hget(self.metadata_key, "data")
        if metadata_json:
            metadata = json.loads(metadata_json)
            self.context = ConversationalContext.from_dict(self.conversation_id, self.sop_id, metadata)
    
    def save_context_to_redis(self):
        """Save conversational context to Redis metadata"""
        metadata = self.context.to_dict()
        self.r.hset(self.metadata_key, "data", json.dumps(metadata))
    
    def execute_node(self, node_id: str) -> str:
        """Execute a single node and return status"""
        node = self.node_map[node_id]
        node_type = node["data"]["label"]
        
        print(f"➡️ Executing Node {node_id} [{node_type}]")
        
        # Get appropriate executor
        executor_class = NODE_EXECUTORS.get(node_type)
        if not executor_class:
            raise Exception(f"No executor found for node type: {node_type}")
        
        # Execute node
        executor = executor_class(node, self.context)
        result = executor.execute()
        
        # Save updated context to Redis after each execution
        self.save_context_to_redis()
        
        return result
    
    def run(self) -> Dict[str, Any]:
        """Run the SOP workflow using Redis queue"""
        print(f"\n🎯 Starting Redis-based SOP execution")
        print(f"📋 SOP: {self.sop['title']}")
        print(f"� Queue: {self.queue_key}")
        print(f"🔑 Metadata: {self.metadata_key}")
        
        # Initialize Redis structures
        self.initialize_redis_queue()
        self.initialize_redis_metadata()
        
        # Main execution loop
        while self.r.llen(self.queue_key) > 0:
            # Left pop the queue to get next node
            current_node_id = self.r.lpop(self.queue_key)
            
            if not current_node_id:
                break
                
            print(f"\n🎬 Processing node: {current_node_id}")
            current_node = self.node_map[current_node_id]
            node_type = current_node["data"]["label"]
            
            # Handle different node types
            if node_type == "Start":
                print(f"🚀 Start node - no-op, continuing...")
                continue
                
            elif node_type == "End":
                print(f"🏁 End node reached - completing workflow")
                result = self.execute_node(current_node_id)
                if isinstance(result, dict) and result.get("status") == "END":
                    final_data = result.get("data", {})
                    print(f"🎉 Workflow completed successfully!")
                    
                    # Clean up Redis
                    self.r.delete(self.queue_key)
                    self.r.delete(self.metadata_key)
                    
                    return {
                        "status": "COMPLETED",
                        "data": final_data
                    }
                break
                
            else:
                # Execute Action or Natural Language Instruction node
                result = self.execute_node(current_node_id)
                
                if result == "WAIT":
                    print(f"⏸️ Node {current_node_id} is waiting for user input")
                    # Put the node back at the front of the queue
                    self.r.lpush(self.queue_key, current_node_id)
                    return {
                        "status": "WAITING",
                        "waiting_for": "user_input",
                        "node_id": current_node_id,
                        "context": self.context.to_dict()
                    }
                elif result == "OK":
                    print(f"✅ Node {current_node_id} completed successfully")
                    continue
                else:
                    print(f"❌ Node {current_node_id} failed with result: {result}")
                    return {
                        "status": "FAILED",
                        "failed_node": current_node_id,
                        "error": result
                    }
        
        return {
            "status": "COMPLETED",
            "message": "Queue empty - workflow finished"
        }
    
    def resume_with_user_input(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Resume execution after receiving user input"""
        print(f"🔄 Resuming execution with user input: {user_input}")
        
        # Load current context from Redis
        self.load_context_from_redis()
        
        # Update context with user input
        for key, value in user_input.items():
            self.context.update_chat_context(key, value)
            
        # Add user message to conversation history
        if "message" in user_input:
            self.context.add_user_message(user_input["message"])
        
        # Save updated context
        self.save_context_to_redis()
        
        # Continue execution
        return self.run()

# -------------------- Test Run --------------------
if __name__ == "__main__":
    redis_client = MockRedis()
    conversation_id = "conv-001"

    print("\n=== First Run (Missing ID Number) ===")
    initial_context = {}  # Simulating no input yet
    executor = RedisSOPExecutor(sample_sop, conversation_id, redis_client, initial_context)
    result1 = executor.run()
    print(f"Result 1: {result1}")

    if result1["status"] == "WAITING":
        print("\n=== Resuming with User Input ===")
        user_input = {
            "id_number": "12345678",
            "message": "My ID number is 12345678"
        }
        result2 = executor.resume_with_user_input(user_input)
        print(f"Result 2: {result2}")
    
    print(f"\nFinal Results:")
    print(f"Run 1: {result1}")
    if 'result2' in locals():
        print(f"Run 2: {result2}")