# Real API Integration Demo
# To test with real APIs, update your .env file with actual keys

from main import RedisSOPExecutor, MockRedis
from dag import dag_flow
import json


def demo_with_real_apis():
    """
    Demo showing how the system works with real API keys
    """
    print("🚀 Real API Integration Demo")
    print("=" * 50)

    # Initialize
    redis_client = MockRedis()
    conversation_id = "demo-conversation"

    # First run - missing info
    executor = RedisSOPExecutor(dag_flow, conversation_id, redis_client, {})
    result1 = executor.run()

    print(f"📋 First Run Status: {result1['status']}")

    if result1["status"] == "WAITING":
        # Resume with user input for comprehensive analysis
        user_input = {
            "id_number":
            "ABC123456",
            "email":
            "john.doe@example.com",
            "message":
            "Hi there! I'm John Doe and I need to check my account eligibility for premium services. My ID is ABC123456 and I've been a customer for 2 years. Can you help me upgrade my account?"
        }

        print(f"\n💬 User Input: {user_input['message']}")

        # Resume execution
        result2 = executor.resume_with_user_input(user_input)

        print(f"\n📋 Final Status: {result2['status']}")

        if result2["status"] == "COMPLETED":
            final_data = result2["data"]

            print(f"\n📊 Execution Results:")
            print(
                f"   Chat Context: {list(final_data['chat_context'].keys())}")
            print(f"   Action Outputs: {len(final_data['action_outputs'])}")
            print(
                f"   Conversation History: {len(final_data['conversation_history'])} messages"
            )

            # Show what would happen with real APIs
            print(f"\n🔧 With Real APIs, this workflow would:")
            print(f"   1. ✅ Start Node: Initialize workflow")
            print(
                f"   2. 🔗 Integrations Node: Call Zoho CRM to lookup customer ABC123456"
            )
            print(f"   3. 🌐 API Tools Node: Call HubSpot to log interaction")
            print(
                f"   4. 🧠 LLM Prompt Node: Analyze user message with Groq LLM")
            print(
                f"   5. 🏁 End Node: Return comprehensive response to Virtual Agent"
            )

            # Show example of what real API responses would look like
            print(f"\n📡 Example Real API Responses:")

            print(f"\n   Zoho CRM Response:")
            print(f"   {{")
            print(f"     'customer_found': true,")
            print(f"     'customer_data': {{")
            print(f"       'name': 'John Doe',")
            print(f"       'tier': 'standard',")
            print(f"       'years_active': 2,")
            print(f"       'eligible_for_upgrade': true")
            print(f"     }}")
            print(f"   }}")

            print(f"\n   Groq LLM Analysis:")
            print(f"   {{")
            print(
                f"     'understanding': 'Customer John Doe wants to upgrade to premium',"
            )
            print(f"     'extracted_info': {{")
            print(f"       'customer_id': 'ABC123456',")
            print(f"       'intent': 'account_upgrade',")
            print(f"       'tenure': '2 years'")
            print(f"     }},")
            print(
                f"     'next_actions': ['check_eligibility', 'process_upgrade'],"
            )
            print(
                f"     'response': 'Based on your 2-year tenure, you are eligible for premium upgrade!'"
            )
            print(f"   }}")


if __name__ == "__main__":
    demo_with_real_apis()
