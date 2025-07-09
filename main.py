import redis
from dag import dag_flow
from collections import deque, defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor


class MockRedis:
    def __init__(self):
        self.r= redis.Redis(host='localhost', port=6379, db=0)

    def get(self, key):
        return self.r.get(key)

    def set(self, key, value):
        self.r.set(key, value)

    def delete(self, key):
        if key in self.r:
            del self.r[key]

# -------------------- Sample DAG --------------------
sample_sop = dag_flow

# -------------------- Node Executors --------------------
class BaseNodeExecutor:
    def __init__(self, node, context):
        self.node = node
        self.context = context

    def execute(self):
        raise NotImplementedError

class StartNodeExecutor(BaseNodeExecutor):
    def execute(self):
        print(f"🚀 Start Node [{self.node['id']}]")
        return "OK"

class LLMInputNodeExecutor(BaseNodeExecutor):
    def execute(self):
        required_fields = self.node["data"].get("required_fields", [])
        prompt = self.node["data"]["description"]
        missing = [field for field in required_fields if field not in self.context]

        if missing:
            print(f"💬 Prompt to user [{self.node['id']}]: {prompt}")
            return "WAIT"
        else:
            print(f"✅ Required info found [{self.node['id']}]: {required_fields}")
            return "OK"

class ActionNodeExecutor(BaseNodeExecutor):
    def execute(self):
        action_type = self.node["data"].get("action_type")
        node_label = self.node["data"]["label"]
        print(f"🔧 Executing {node_label} [{self.node['id']}]")
        
        if action_type == "check_eligibility":
            print("🧠 Checking eligibility based on provided ID...")
        
        # Simulate some processing time for demonstration
        import time
        time.sleep(0.5)
        return "OK"

class EndNodeExecutor(BaseNodeExecutor):
    def execute(self):
        print(f"🏁 Reached End Node [{self.node['id']}]")
        return "END"

# Registry for pluggable node execution
NODE_EXECUTORS = {
    "Start": StartNodeExecutor,
    "LLM Prompt": LLMInputNodeExecutor,
    "API Tools": ActionNodeExecutor,
    "Integrations": ActionNodeExecutor,
    "End": EndNodeExecutor
}

# -------------------- Enhanced SOP Executor Engine --------------------
class TopologicalSOPExecutor:
    def __init__(self, sop, chat_context, conversation_id, redis_client):
        self.sop = sop
        self.context = chat_context
        self.conversation_id = conversation_id
        self.r = redis_client
        self.state_key = f"sop_exec:{sop['id']}:{conversation_id}"
        self.node_map = {n["id"]: n for n in sop["nodes"]}
        self.build_graph()
        self.completed_nodes = set()
        self.failed_nodes = set()
        self.waiting_nodes = set()
        
    def build_graph(self):
        """Build adjacency lists and in-degree counts for topological sorting"""
        self.outgoing = defaultdict(list)  # node_id -> [target_nodes]
        self.incoming = defaultdict(list)  # node_id -> [source_nodes]
        self.in_degree = defaultdict(int)  # node_id -> count
        
        # Initialize all nodes with 0 in-degree
        for node in self.sop["nodes"]:
            self.in_degree[node["id"]] = 0
            
        # Build the graph from edges
        for edge in self.sop["edges"]:
            source = edge["source"]
            target = edge["target"]
            
            # Skip edges that reference non-existent nodes
            if source in self.node_map and target in self.node_map:
                self.outgoing[source].append(target)
                self.incoming[target].append(source)
                self.in_degree[target] += 1
    
    def get_ready_nodes(self):
        """Get nodes that are ready to execute (all dependencies completed)"""
        ready = []
        for node_id, in_deg in self.in_degree.items():
            if (in_deg == 0 and 
                node_id not in self.completed_nodes and 
                node_id not in self.failed_nodes and
                node_id not in self.waiting_nodes):
                ready.append(node_id)
        return ready
    
    def execute_node(self, node_id):
        """Execute a single node"""
        node = self.node_map[node_id]
        node_type = node["data"]["label"]
        executor_class = NODE_EXECUTORS.get(node_type)
        
        if not executor_class:
            raise Exception(f"No executor found for node type: {node_type}")
        
        executor = executor_class(node, self.context)
        print(f"➡️ Executing Node {node_id} [{node_type}]")
        return executor.execute()
    
    def mark_node_completed(self, node_id):
        """Mark a node as completed and update in-degrees of dependent nodes"""
        self.completed_nodes.add(node_id)
        
        # Reduce in-degree for all dependent nodes
        for dependent_node in self.outgoing[node_id]:
            self.in_degree[dependent_node] -= 1
    
    def execute_parallel_batch(self, node_ids):
        """Execute a batch of nodes in parallel"""
        if not node_ids:
            return []
            
        print(f"🔄 Executing parallel batch: {node_ids}")
        
        # For demonstration, we'll use ThreadPoolExecutor
        # In a real system, you might want to use asyncio or other async frameworks
        with ThreadPoolExecutor(max_workers=len(node_ids)) as executor:
            future_to_node = {
                executor.submit(self.execute_node, node_id): node_id 
                for node_id in node_ids
            }
            
            results = []
            for future in future_to_node:
                node_id = future_to_node[future]
                try:
                    result = future.result()
                    results.append((node_id, result))
                except Exception as exc:
                    print(f"❌ Node {node_id} generated an exception: {exc}")
                    results.append((node_id, "FAILED"))
                    
        return results
    
    def run(self):
        """Run the workflow with topological ordering and parallel execution"""
        print(f"\n🎯 Starting workflow execution: {self.sop['title']}")
        print(f"📋 Total nodes: {len(self.sop['nodes'])}")
        
        total_nodes = len(self.sop['nodes'])
        
        while len(self.completed_nodes) + len(self.failed_nodes) + len(self.waiting_nodes) < total_nodes:
            # Get nodes ready for execution
            ready_nodes = self.get_ready_nodes()
            
            if not ready_nodes:
                if self.waiting_nodes:
                    print("⏸️ All remaining nodes are waiting for user input")
                    print(f"Waiting nodes: {list(self.waiting_nodes)}")
                    break
                else:
                    print("❌ No nodes ready and none waiting - possible cycle or missing dependencies")
                    break
            
            # Execute ready nodes in parallel
            results = self.execute_parallel_batch(ready_nodes)
            
            # Process results
            has_waiting = False
            for node_id, result in results:
                if result == "OK":
                    self.mark_node_completed(node_id)
                    print(f"✅ Node {node_id} completed successfully")
                elif result == "END":
                    self.mark_node_completed(node_id)
                    print(f"🏁 End node {node_id} reached")
                elif result == "WAIT":
                    self.waiting_nodes.add(node_id)
                    has_waiting = True
                    print(f"⏸️ Node {node_id} is waiting for user input")
                else:  # FAILED or any other status
                    self.failed_nodes.add(node_id)
                    print(f"❌ Node {node_id} failed")
            
            if has_waiting:
                print("⏸️ Execution paused due to nodes waiting for user input")
                break
        
        # Print execution summary
        print(f"\n📊 Execution Summary:")
        print(f"✅ Completed: {len(self.completed_nodes)} nodes")
        print(f"⏸️ Waiting: {len(self.waiting_nodes)} nodes")
        print(f"❌ Failed: {len(self.failed_nodes)} nodes")
        
        if len(self.completed_nodes) == total_nodes:
            print("🎉 Workflow completed successfully!")
            self.r.delete(self.state_key)
        
        return {
            "completed": list(self.completed_nodes),
            "waiting": list(self.waiting_nodes),
            "failed": list(self.failed_nodes)
        }

# -------------------- Test Run --------------------
if __name__ == "__main__":
    redis_client = MockRedis()
    conversation_id = "conv-001"

    print("\n=== First Run (Missing ID Number) ===")
    chat_context = {}  # Simulating no input yet
    executor = TopologicalSOPExecutor(sample_sop, chat_context, conversation_id, redis_client)
    result1 = executor.run()

    print("\n=== Second Run (User Provided ID Number) ===")
    chat_context = {"id_number": "12345678"}  # Now user replied
    executor = TopologicalSOPExecutor(sample_sop, chat_context, conversation_id, redis_client)
    result2 = executor.run()
    
    print(f"\nFinal Results:")
    print(f"Run 1: {result1}")
    print(f"Run 2: {result2}")