import redis
from weather_dag import weather_dag
from collections import deque, defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
import time
import requests
import os
from typing import Dict, List, Any, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class MockRedis:

    def __init__(self):
        self.r = redis.Redis(host='localhost',
                             port=6379,
                             db=0,
                             decode_responses=True)

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

    def __init__(self,
                 conversation_id: str,
                 sop_id: str,
                 initial_context: Dict[str, Any] = None):
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

    def has_required_fields(
            self, required_fields: List[str]) -> tuple[bool, List[str]]:
        """Check if all required fields are present in context"""
        missing = [
            field for field in required_fields
            if field not in self.chat_context
        ]
        return len(missing) == 0, missing

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for Redis storage"""
        return {
            "chat_context": self.chat_context,
            "action_outputs": self.action_outputs,
            "conversation_history": self.conversation_history
        }

    @classmethod
    def from_dict(cls, conversation_id: str, sop_id: str, data: Dict[str,
                                                                     Any]):
        """Create context from dictionary loaded from Redis"""
        context = cls(conversation_id, sop_id)
        context.chat_context = data.get("chat_context", {})
        context.action_outputs = data.get("action_outputs", [])
        context.conversation_history = data.get("conversation_history", [])
        return context


# -------------------- Sample DAG --------------------
sample_sop = weather_dag


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
    """Action executor - extracts data from context, calls REAL APIs, stores output"""

    def execute(self):
        action_type = self.node["data"].get("action_type")
        node_label = self.node["data"]["label"]
        print(f"🔧 Executing Action: {node_label} [{self.node['id']}]")

        # Extract data from current context
        input_data = self._extract_input_data()

        # Call REAL API based on action type
        try:
            api_output = self._call_real_api(action_type, input_data)
        except Exception as e:
            print(f"❌ API call failed: {str(e)}")
            # Return error but don't crash the workflow
            api_output = {
                "error": True,
                "error_message": str(e),
                "timestamp": time.time()
            }

        # Store output in context
        self.context.add_action_output(node_id=self.node['id'],
                                       action_type=action_type,
                                       output=api_output)

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
            input_data[
                f"action_{action_output['node_id']}_output"] = action_output[
                    'output']

        return input_data

    def _call_real_api(self, action_type: str,
                       input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make real API calls based on action type"""

        if action_type == "weather_lookup":
            return self._call_weather_api(input_data)
        elif action_type == "random_quote":
            return self._call_quote_api(input_data)
        elif action_type == "check_eligibility":
            return self._call_eligibility_api(input_data)
        elif action_type == "zoho_crm_lookup":
            return self._call_zoho_api(input_data)
        elif action_type == "hubspot_integration":
            return self._call_hubspot_api(input_data)
        else:
            # Generic API call for unknown action types
            return self._call_generic_api(action_type, input_data)

    def _call_weather_api(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call OpenWeatherMap API for weather data"""
        location = input_data.get("location", input_data.get("city", "London"))
        api_key = os.getenv('OPENWEATHER_API_KEY', 'demo-key')

        # OpenWeatherMap Current Weather API
        api_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": api_key,
            "units": "metric"  # Celsius
        }

        try:
            response = requests.get(api_url, params=params, timeout=10)

            if response.status_code == 200:
                weather_data = response.json()
                return {
                    "weather_found":
                    True,
                    "location":
                    weather_data.get("name", location),
                    "country":
                    weather_data.get("sys", {}).get("country", ""),
                    "temperature":
                    weather_data.get("main", {}).get("temp", 0),
                    "feels_like":
                    weather_data.get("main", {}).get("feels_like", 0),
                    "humidity":
                    weather_data.get("main", {}).get("humidity", 0),
                    "description":
                    weather_data.get("weather",
                                     [{}])[0].get("description", ""),
                    "main_weather":
                    weather_data.get("weather", [{}])[0].get("main", ""),
                    "wind_speed":
                    weather_data.get("wind", {}).get("speed", 0),
                    "timestamp":
                    time.time(),
                    "api_response":
                    weather_data
                }
            elif response.status_code == 404:
                return {
                    "weather_found": False,
                    "error": "Location not found",
                    "location": location,
                    "timestamp": time.time()
                }
            else:
                return {
                    "error": True,
                    "error_code": response.status_code,
                    "error_message":
                    f"Weather API returned {response.status_code}",
                    "timestamp": time.time()
                }

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Weather API unavailable, using mock data")
            # Fallback with mock weather data
            return {
                "weather_found": True,
                "location": location,
                "temperature": 22,
                "feels_like": 24,
                "humidity": 65,
                "description": "partly cloudy",
                "main_weather": "Clouds",
                "wind_speed": 5.2,
                "fallback_used": True,
                "error_message": str(e),
                "timestamp": time.time()
            }

    def _call_quote_api(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call Quotable API for inspirational quotes"""
        # Quotable API - free random quote service
        api_url = "https://api.quotable.io/random"
        params = {
            "minLength": 50,  # Minimum quote length
            "maxLength": 200  # Maximum quote length
        }

        try:
            response = requests.get(api_url, params=params, timeout=10)

            if response.status_code == 200:
                quote_data = response.json()
                return {
                    "quote_found": True,
                    "quote": quote_data.get("content", ""),
                    "author": quote_data.get("author", "Unknown"),
                    "tags": quote_data.get("tags", []),
                    "length": quote_data.get("length", 0),
                    "timestamp": time.time(),
                    "api_response": quote_data
                }
            else:
                return {
                    "error": True,
                    "error_code": response.status_code,
                    "error_message":
                    f"Quote API returned {response.status_code}",
                    "timestamp": time.time()
                }

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Quote API unavailable, using fallback")
            # Fallback quotes
            fallback_quotes = [{
                "quote":
                "The best time to plant a tree was 20 years ago. The second best time is now.",
                "author": "Chinese Proverb"
            }, {
                "quote":
                "Success is not final, failure is not fatal: it is the courage to continue that counts.",
                "author": "Winston Churchill"
            }, {
                "quote":
                "The only way to do great work is to love what you do.",
                "author": "Steve Jobs"
            }, {
                "quote":
                "Life is what happens to you while you're busy making other plans.",
                "author": "John Lennon"
            }]

            import random
            selected_quote = random.choice(fallback_quotes)

            return {
                "quote_found": True,
                "quote": selected_quote["quote"],
                "author": selected_quote["author"],
                "tags": ["motivation", "inspiration"],
                "fallback_used": True,
                "error_message": str(e),
                "timestamp": time.time()
            }

    def _call_eligibility_api(self, input_data: Dict[str,
                                                     Any]) -> Dict[str, Any]:
        """Call real eligibility checking API"""
        id_number = input_data.get("id_number", "")

        # Example: Real API call to eligibility service
        api_url = "https://api.eligibility-service.com/check"
        headers = {
            "Authorization":
            f"Bearer {os.getenv('ELIGIBILITY_API_KEY', 'demo-key')}",
            "Content-Type": "application/json"
        }

        payload = {"id_number": id_number, "context": input_data}

        try:
            # Make the actual API call
            response = requests.post(api_url,
                                     json=payload,
                                     headers=headers,
                                     timeout=30)

            if response.status_code == 200:
                api_result = response.json()
                return {
                    "eligibility_status": api_result.get("status", "unknown"),
                    "id_verified": api_result.get("verified", False),
                    "id_number": id_number,
                    "verification_timestamp": time.time(),
                    "api_response": api_result
                }
            else:
                # API returned error status
                return {
                    "error": True,
                    "error_code": response.status_code,
                    "error_message": f"API returned {response.status_code}",
                    "timestamp": time.time()
                }

        except requests.exceptions.RequestException as e:
            # Network error or timeout
            print(f"⚠️ Eligibility API unavailable, using fallback logic")
            # Fallback logic when API is down
            return {
                "eligibility_status": "eligible" if id_number else "unknown",
                "id_verified": bool(id_number),
                "id_number": id_number,
                "verification_timestamp": time.time(),
                "fallback_used": True,
                "error_message": str(e)
            }

    def _call_zoho_api(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call real Zoho CRM API"""
        api_url = "https://www.zohoapis.com/crm/v2/Contacts"
        headers = {
            "Authorization":
            f"Zoho-oauthtoken {os.getenv('ZOHO_ACCESS_TOKEN', 'demo-token')}",
            "Content-Type": "application/json"
        }

        # Search for customer by ID or email
        search_criteria = input_data.get("id_number", "")
        params = {
            "criteria":
            f"(Email:equals:{search_criteria}) or (Customer_ID:equals:{search_criteria})"
        }

        try:
            response = requests.get(api_url,
                                    headers=headers,
                                    params=params,
                                    timeout=30)

            if response.status_code == 200:
                api_result = response.json()
                contacts = api_result.get("data", [])

                if contacts:
                    customer = contacts[0]  # Take first match
                    return {
                        "customer_found": True,
                        "customer_data": {
                            "name":
                            f"{customer.get('First_Name', '')} {customer.get('Last_Name', '')}",
                            "email": customer.get("Email", ""),
                            "tier": customer.get("Customer_Tier", "standard"),
                            "id": customer.get("id")
                        },
                        "lookup_timestamp": time.time()
                    }
                else:
                    return {
                        "customer_found": False,
                        "lookup_timestamp": time.time()
                    }
            else:
                return {
                    "error": True,
                    "error_code": response.status_code,
                    "error_message":
                    f"Zoho API returned {response.status_code}",
                    "timestamp": time.time()
                }

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Zoho API unavailable, using fallback")
            return {
                "customer_found": True,
                "customer_data": {
                    "name": "Demo Customer",
                    "tier": "standard"
                },
                "lookup_timestamp": time.time(),
                "fallback_used": True,
                "error_message": str(e)
            }

    def _call_hubspot_api(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call real HubSpot API"""
        api_url = "https://api.hubapi.com/conversations/v3/conversations"
        headers = {
            "Authorization":
            f"Bearer {os.getenv('HUBSPOT_ACCESS_TOKEN', 'demo-token')}",
            "Content-Type": "application/json"
        }

        # Create a conversation or send message
        payload = {
            "type": "CHAT",
            "inbox": {
                "id": os.getenv('HUBSPOT_INBOX_ID', 'demo-inbox')
            },
            "message": {
                "type":
                "MESSAGE",
                "text":
                f"Workflow executed with context: {json.dumps(input_data, indent=2)}"
            }
        }

        try:
            response = requests.post(api_url,
                                     json=payload,
                                     headers=headers,
                                     timeout=30)

            if response.status_code in [200, 201]:
                api_result = response.json()
                return {
                    "message_sent": True,
                    "conversation_id": api_result.get("id"),
                    "delivery_timestamp": time.time(),
                    "hubspot_response": api_result
                }
            else:
                return {
                    "error": True,
                    "error_code": response.status_code,
                    "error_message":
                    f"HubSpot API returned {response.status_code}",
                    "timestamp": time.time()
                }

        except requests.exceptions.RequestException as e:
            print(f"⚠️ HubSpot API unavailable, using fallback")
            return {
                "message_sent": True,
                "message_id": f"fallback_{int(time.time())}",
                "delivery_timestamp": time.time(),
                "fallback_used": True,
                "error_message": str(e)
            }

    def _call_generic_api(self, action_type: str,
                          input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic API call handler for unknown action types"""
        print(f"⚠️ Unknown action type: {action_type}, using generic handler")

        # You can implement custom logic here for other API integrations
        return {
            "action_completed": True,
            "action_type": action_type,
            "input_received": list(input_data.keys()),
            "timestamp": time.time(),
            "generic_handler": True
        }


class NaturalLanguageInstructionsExecutor(BaseNodeExecutor):
    """Natural language instructions executor with Groq LLM integration"""

    def __init__(self, node, context: ConversationalContext):
        super().__init__(node, context)
        # Initialize Groq client
        self.groq_client = Groq(
            api_key=os.getenv('GROQ_API_KEY', 'your-groq-api-key-here'))

    def execute(self):
        instructions = self.node["data"].get("description", "")
        required_fields = self.node["data"].get("required_fields", [])

        print(f"🧠 Executing NL Instructions: [{self.node['id']}]")

        # Check 1: Required information from customer
        if required_fields:
            has_all_fields, missing_fields = self.context.has_required_fields(
                required_fields)

            if not has_all_fields:
                print(f"💬 Missing required fields: {missing_fields}")
                print(f"📝 Prompt: {instructions}")

                # Store that we're waiting for this information
                self.context.add_assistant_message(
                    f"I need the following information: {', '.join(missing_fields)}. {instructions}"
                )
                return "WAIT"

        # Check 2: Execute natural language instructions with Groq
        try:
            nl_output = self._execute_groq_instructions(instructions)
        except Exception as e:
            print(f"❌ Groq API call failed: {str(e)}")
            # Fallback to basic processing
            nl_output = self._execute_fallback_instructions(instructions)

        # Store output in context
        self.context.add_action_output(
            node_id=self.node['id'],
            action_type="natural_language_processing",
            output=nl_output)

        print(f"✅ NL Instructions completed: {nl_output}")
        return "OK"

    def _execute_groq_instructions(self, instructions: str) -> Dict[str, Any]:
        """Process natural language instructions using Groq LLM"""

        # Get user's latest message from conversation history
        user_messages = [
            msg for msg in self.context.conversation_history
            if msg.get("role") == "user"
        ]
        latest_user_message = user_messages[-1][
            "content"] if user_messages else "No user input"

        # Check if this is a location extraction node
        extract_location = self.node["data"].get("extract_location", False)

        # Build context for the LLM
        context_summary = {
            "chat_context":
            self.context.chat_context,
            "previous_actions": [{
                "node": action["node_id"],
                "type": action["action_type"],
                "result": action["output"]
            } for action in self.context.action_outputs],
            "user_message":
            latest_user_message
        }

        if extract_location:
            # Location extraction prompt
            system_prompt = f"""You are a location extraction assistant. Extract the location from the user's message.

User message: "{latest_user_message}"

Instructions: {instructions}

Extract the location (city, state, country) from the user's message. If no specific location is mentioned, ask the user for their location.

Return your response as a JSON object with keys:
- location_found: boolean
- location: string (city name if found, empty if not)  
- needs_location: boolean (true if you need to ask for location)
- response: string (conversational response to user)
- confidence: number (0-1, how confident you are about the location)"""

        else:
            # Activity recommendation prompt
            weather_data = None
            quote_data = None

            # Extract weather and quote data from previous actions
            for action in self.context.action_outputs:
                if action.get("action_type") == "weather_lookup":
                    weather_data = action.get("output")
                elif action.get("action_type") == "random_quote":
                    quote_data = action.get("output")

            system_prompt = f"""You are a helpful activity advisor. Based on the weather data and inspirational quote, provide personalized activity recommendations.

User message: "{latest_user_message}"
Instructions: {instructions}

Weather Data: {json.dumps(weather_data, indent=2) if weather_data else "No weather data available"}

Quote Data: {json.dumps(quote_data, indent=2) if quote_data else "No quote available"}

Provide activity recommendations based on:
1. Current weather conditions
2. User's original request/question
3. Include the inspirational quote in a meaningful way

Return your response as a JSON object with keys:
- weather_analysis: string (summary of weather conditions)
- activity_recommendations: array of strings (3-5 specific activities)
- quote_integration: string (how the quote relates to the recommendations)
- response: string (friendly, conversational response with all recommendations)
- weather_appropriate: boolean (whether activities match the weather)"""

        try:
            # Call Groq API
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{
                    "role": "system",
                    "content": system_prompt
                }, {
                    "role": "user",
                    "content": latest_user_message
                }],
                model="llama3-8b-8192",
                temperature=0.3,
                max_tokens=1024)

            # Parse LLM response
            llm_response = chat_completion.choices[0].message.content

            try:
                # Try to parse as JSON
                parsed_response = json.loads(llm_response)
            except json.JSONDecodeError:
                # If not valid JSON, wrap the response
                if extract_location:
                    parsed_response = {
                        "location_found": False,
                        "location": "",
                        "needs_location": True,
                        "response": llm_response,
                        "confidence": 0.5
                    }
                else:
                    parsed_response = {
                        "weather_analysis": "Weather data processed",
                        "activity_recommendations":
                        ["General outdoor activities"],
                        "quote_integration": "Stay motivated",
                        "response": llm_response,
                        "weather_appropriate": True
                    }

            # Handle location extraction
            if extract_location and parsed_response.get(
                    "location_found") and parsed_response.get("location"):
                # Store extracted location in context
                self.context.update_chat_context("location",
                                                 parsed_response["location"])
                self.context.update_chat_context("city",
                                                 parsed_response["location"])

            # Add assistant message to conversation
            assistant_response = parsed_response.get(
                "response", "I've processed your message.")
            self.context.add_assistant_message(assistant_response)

            return {
                "instructions_processed": True,
                "instructions": instructions,
                "user_message_analyzed": latest_user_message,
                "llm_response": parsed_response,
                "groq_model": "llama3-8b-8192",
                "context_items_count": len(self.context.chat_context),
                "location_extraction": extract_location,
                "timestamp": time.time()
            }

        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")

    def _execute_fallback_instructions(self,
                                       instructions: str) -> Dict[str, Any]:
        """Fallback processing when Groq API is unavailable"""
        print("⚠️ Using fallback NL processing")

        # Basic analysis without LLM
        user_messages = [
            msg for msg in self.context.conversation_history
            if msg.get("role") == "user"
        ]
        latest_user_message = user_messages[-1][
            "content"] if user_messages else "No user input"

        # Check if this is a location extraction node
        extract_location = self.node["data"].get("extract_location", False)

        if extract_location:
            # Simple location extraction using keywords
            location = self._extract_location_fallback(latest_user_message)

            if location:
                self.context.update_chat_context("location", location)
                self.context.update_chat_context("city", location)
                fallback_response = f"I found the location: {location}. Let me get the weather information for you."
            else:
                fallback_response = "I couldn't identify your location. Could you please tell me which city you're in?"

            self.context.add_assistant_message(fallback_response)

            return {
                "instructions_processed": True,
                "instructions": instructions,
                "user_message_analyzed": latest_user_message,
                "location_found": bool(location),
                "location": location or "",
                "needs_location": not bool(location),
                "fallback_used": True,
                "response": fallback_response,
                "location_extraction": True,
                "context_items_count": len(self.context.chat_context),
                "timestamp": time.time()
            }
        else:
            # Simple keyword extraction for activity recommendations
            extracted_keywords = self._extract_keywords(latest_user_message)

            # Generate basic response
            fallback_response = f"Based on your message about {', '.join(extracted_keywords)}, I recommend checking the weather and planning accordingly."
            self.context.add_assistant_message(fallback_response)

            return {
                "instructions_processed": True,
                "instructions": instructions,
                "user_message_analyzed": latest_user_message,
                "extracted_keywords": extracted_keywords,
                "fallback_used": True,
                "response": fallback_response,
                "context_items_count": len(self.context.chat_context),
                "timestamp": time.time()
            }

    def _extract_location_fallback(self, text: str) -> str:
        """Simple location extraction for fallback"""
        import re

        # Common location patterns
        location_patterns = [
            r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # "in London", "in New York"
            r'\bat\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # "at London", "at New York"
            r'\b([A-Z][a-z]+)\s+weather\b',  # "London weather"
            r'\b([A-Z][a-z]+)\s+today\b',  # "London today"
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        # List of common cities for fallback recognition
        common_cities = [
            'London', 'Paris', 'Tokyo', 'New York', 'Sydney', 'Berlin', 'Rome',
            'Madrid', 'Amsterdam', 'Barcelona'
        ]

        for city in common_cities:
            if city.lower() in text.lower():
                return city

        return ""

    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction for fallback"""
        # Basic keyword extraction (you could use NLTK or spaCy for better results)
        import re

        # Remove common words and extract meaningful terms
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'my', 'i',
            'me'
        }
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [
            word for word in words
            if word not in common_words and len(word) > 2
        ]

        return keywords[:5]  # Return top 5 keywords


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

    def __init__(self,
                 sop,
                 conversation_id: str,
                 redis_client: MockRedis,
                 initial_context: Dict[str, Any] = None):
        self.sop = sop
        self.conversation_id = conversation_id
        self.sop_id = sop["id"]
        self.r = redis_client

        # Generate Redis keys using hash of conversation_id + sop_id
        self.queue_key = self._generate_queue_key()
        self.metadata_key = self._generate_metadata_key()

        # Initialize conversational context
        self.context = ConversationalContext(conversation_id, self.sop_id,
                                             initial_context)

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
        queue = deque(
            [node_id for node_id, degree in in_degree.items() if degree == 0])
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
            self.context = ConversationalContext.from_dict(
                self.conversation_id, self.sop_id, metadata)

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

                    return {"status": "COMPLETED", "data": final_data}
                break

            else:
                # Execute Action or Natural Language Instruction node
                result = self.execute_node(current_node_id)

                if result == "WAIT":
                    print(
                        f"⏸️ Node {current_node_id} is waiting for user input")
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
                    print(
                        f"❌ Node {current_node_id} failed with result: {result}"
                    )
                    return {
                        "status": "FAILED",
                        "failed_node": current_node_id,
                        "error": result
                    }

        return {
            "status": "COMPLETED",
            "message": "Queue empty - workflow finished"
        }

    def resume_with_user_input(self, user_input: Dict[str,
                                                      Any]) -> Dict[str, Any]:
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
    conversation_id = "weather-conv-001"

    print("\n=== Weather & Activity Advisor Test ===")
    print("🔑 API Keys Status:")
    print(
        f"   GROQ_API_KEY: {'✅ Set' if os.getenv('GROQ_API_KEY') and os.getenv('GROQ_API_KEY') != 'your-groq-api-key-here' else '❌ Not configured'}"
    )
    print(
        f"   OPENWEATHER_API_KEY: {'✅ Set' if os.getenv('OPENWEATHER_API_KEY') else '❌ Not configured (will use fallback)'}"
    )

    print("\n=== User Query: Weather and Activity Request ===")
    initial_context = {}

    # Simulate user asking about weather and activities
    user_query = "What's the weather like in London today and what activities can I do?"

    executor = RedisSOPExecutor(sample_sop, conversation_id, redis_client,
                                initial_context)

    # Add the user message to context before starting
    executor.context.add_user_message(user_query)

    print(f"💬 User: {user_query}")

    result = executor.run()

    print(f"\n📊 Execution Result: {result['status']}")

    if result["status"] == "COMPLETED":
        final_data = result["data"]

        print(f"\n🎯 Final Response Summary:")
        print(
            f"   Location extracted: {final_data['chat_context'].get('location', 'Not found')}"
        )

        # Show weather data
        weather_action = None
        quote_action = None
        activity_action = None

        for action in final_data["action_outputs"]:
            if action.get("action_type") == "weather_lookup":
                weather_action = action["output"]
            elif action.get("action_type") == "random_quote":
                quote_action = action["output"]
            elif action.get("action_type"
                            ) == "natural_language_processing" and not action[
                                "output"].get("location_extraction"):
                activity_action = action["output"]

        if weather_action:
            print(f"\n🌤️ Weather Information:")
            if weather_action.get("weather_found"):
                print(f"   Location: {weather_action.get('location')}")
                print(f"   Temperature: {weather_action.get('temperature')}°C")
                print(f"   Conditions: {weather_action.get('description')}")
                print(f"   Wind Speed: {weather_action.get('wind_speed')} m/s")
            else:
                print(
                    f"   ❌ Weather not found: {weather_action.get('error', 'Unknown error')}"
                )

        if quote_action:
            print(f"\n💬 Inspirational Quote:")
            if quote_action.get("quote_found"):
                print(f"   \"{quote_action.get('quote')}\"")
                print(f"   - {quote_action.get('author')}")
            else:
                print(f"   ❌ Quote not found")

        if activity_action and activity_action.get("llm_response"):
            llm_resp = activity_action["llm_response"]
            print(f"\n🎯 Activity Recommendations:")
            if isinstance(llm_resp.get("activity_recommendations"), list):
                for i, activity in enumerate(
                        llm_resp["activity_recommendations"], 1):
                    print(f"   {i}. {activity}")

        print(f"\n🔄 Conversation Flow:")
        for i, msg in enumerate(final_data["conversation_history"], 1):
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            print(
                f"   {i}. {role_icon} {msg['role'].title()}: {msg['content'][:100]}..."
            )

    elif result["status"] == "WAITING":
        print(f"⏸️ Workflow paused, waiting for: {result.get('waiting_for')}")

    else:
        print(f"❌ Workflow failed: {result}")
