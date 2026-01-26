import os
import json
from datetime import datetime
from django.utils import timezone
from django.db.models import Q, Min, Max
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from bikes.models import Bike
from bookings.models import Booking

# Configure Gemini API
api_key = os.environ.get("GEMINI_API_KEY")
print(f"DEBUG: GEMINI_API_KEY loaded: {bool(api_key)}")
genai.configure(api_key=api_key)

# ==================== FUNCTION IMPLEMENTATIONS ====================

def check_availability(start_date_str: str, end_date_str: str, bike_type: str = None):
    """
    Check for available bikes within a given date range.
    
    Args:
        start_date_str (str): Start date in 'YYYY-MM-DD' format.
        end_date_str (str): End date in 'YYYY-MM-DD' format.
        bike_type (str, optional): Type of bike to filter by (e.g., 'scooter', 'motorcycle').
    
    Returns:
        dict: A dictionary containing a list of available bikes or a message.
    """
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        if start_date < timezone.now().date():
             return {"error": "Start date cannot be in the past."}

        if end_date <= start_date:
            return {"error": "End date must be after start date."}

        # Find bikes that are NOT booked during this period
        overlapping_bookings = Booking.objects.filter(
            status='confirmed',
            payment_status='paid'
        ).filter(
            Q(start_date__lt=end_date) & Q(end_date__gt=start_date)
        )
        
        booked_bike_ids = overlapping_bookings.values_list('bike_id', flat=True)
        
        available_bikes = Bike.objects.exclude(id__in=booked_bike_ids).filter(
            availability_status=True,
            is_approved=True
        )
        
        if bike_type:
            available_bikes = available_bikes.filter(type__icontains=bike_type)
            
        results = []
        for bike in available_bikes:
            results.append({
                "id": bike.id,
                "name": bike.name,
                "type": bike.type,
                "brand": bike.brand,
                "price_per_day": str(bike.price_per_day),
                "mileage": str(bike.mileage) if bike.mileage else "N/A"
            })
            
        if not results:
            return {"message": "No bikes available for the selected dates."}
            
        return {"available_bikes": results}

    except ValueError:
        return {"error": "Invalid date format. Please use YYYY-MM-DD."}
    except Exception as e:
        return {"error": str(e)}


def get_bike_listings(bike_type: str = None, max_price: float = None):
    """
    Get list of available bikes with optional filters.
    
    Args:
        bike_type (str, optional): Filter by type (scooter, motorcycle, electric).
        max_price (float, optional): Maximum price per day filter.
    
    Returns:
        dict: List of bikes with details.
    """
    try:
        bikes = Bike.objects.filter(is_approved=True, availability_status=True)
        
        if bike_type:
            bikes = bikes.filter(type__icontains=bike_type)
        if max_price:
            bikes = bikes.filter(price_per_day__lte=max_price)
        
        results = []
        for bike in bikes[:20]:  # Limit to 20 bikes to avoid overwhelming response
            results.append({
                "id": bike.id,
                "name": bike.name,
                "type": bike.type,
                "brand": bike.brand,
                "price_per_day": str(bike.price_per_day),
                "mileage": str(bike.mileage) if bike.mileage else "N/A",
                "model_year": bike.model_year,
                "rating": str(bike.average_rating) if bike.average_rating else "No ratings yet"
            })
        
        if not results:
            return {"message": "No bikes found matching your criteria."}
        
        return {"bikes": results, "total_count": len(results)}
    
    except Exception as e:
        return {"error": str(e)}


def get_price_ranges():
    """
    Get pricing information and discount structure.
    
    Returns:
        dict: Price ranges by bike type and discount information.
    """
    try:
        # Get price statistics by bike type
        price_info = {}
        
        for bike_type, bike_type_display in Bike.BIKE_TYPES:
            bikes = Bike.objects.filter(type=bike_type, is_approved=True)
            if bikes.exists():
                stats = bikes.aggregate(
                    min_price=Min('price_per_day'),
                    max_price=Max('price_per_day')
                )
                price_info[bike_type_display] = {
                    "min_price": str(stats['min_price']),
                    "max_price": str(stats['max_price'])
                }
        
        discount_structure = {
            "7-13 days": "5% discount",
            "14-20 days": "10% discount",
            "21-27 days": "15% discount",
            "28+ days": "20% discount"
        }
        
        return {
            "price_ranges": price_info,
            "discounts": discount_structure,
            "note": "Prices are per day. Discounts are automatically applied based on rental duration."
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_bike_details(bike_identifier: str):
    """
    Get detailed information about a specific bike.
    
    Args:
        bike_identifier (str): Bike ID or name.
    
    Returns:
        dict: Complete bike specifications and features.
    """
    try:
        # Try to find bike by ID first, then by name
        bike = None
        if bike_identifier.isdigit():
            bike = Bike.objects.filter(id=int(bike_identifier), is_approved=True).first()
        
        if not bike:
            bike = Bike.objects.filter(name__icontains=bike_identifier, is_approved=True).first()
        
        if not bike:
            return {"error": "Bike not found."}
        
        details = {
            "id": bike.id,
            "name": bike.name,
            "type": bike.type,
            "brand": bike.brand,
            "model_year": bike.model_year,
            "price_per_day": str(bike.price_per_day),
            "description": bike.description or "No description available",
            "mileage": str(bike.mileage) if bike.mileage else "N/A",
            "rating": str(bike.average_rating) if bike.average_rating else "No ratings yet",
            "specifications": {
                "engine_type": bike.engine_type or "N/A",
                "displacement": bike.displacement or "N/A",
                "max_power": bike.max_power or "N/A",
                "torque": bike.torque or "N/A",
                "transmission": bike.transmission or "N/A",
                "brakes": bike.brakes or "N/A",
                "fuel_capacity": str(bike.fuel_capacity) + " L" if bike.fuel_capacity else "N/A",
                "dimensions": bike.dimensions or "N/A"
            }
        }
        
        return details
    
    except Exception as e:
        return {"error": str(e)}


def get_payment_methods():
    """
    Get information about available payment methods and options.
    
    Returns:
        dict: Payment methods and options information.
    """
    return {
        "payment_methods": [
            {
                "name": "eSewa",
                "description": "Popular digital wallet in Nepal for instant online payments",
                "type": "online"
            },
            {
                "name": "PayPal",
                "description": "International payment gateway for secure online transactions",
                "type": "online"
            },
            {
                "name": "Cash on Delivery",
                "description": "Pay in cash when you pick up the bike",
                "type": "offline"
            }
        ],
        "payment_options": [
            {
                "option": "Full Payment Online",
                "description": "Pay the complete rental amount online before pickup"
            },
            {
                "option": "Partial Payment Online",
                "description": "Pay a portion online and the rest on delivery"
            },
            {
                "option": "Cash on Delivery",
                "description": "Pay the full amount in cash when picking up the bike"
            }
        ],
        "note": "Online payments are processed securely. You'll receive a confirmation once payment is successful."
    }


def get_required_documents():
    """
    Get information about documents required to rent a bike.
    
    Returns:
        dict: List of required documents and additional information.
    """
    return {
        "required_documents": [
            {
                "document": "Valid Government ID",
                "description": "Citizenship card, passport, or driving license",
                "mandatory": True
            },
            {
                "document": "Valid Driving License",
                "description": "Appropriate license for the bike category you're renting",
                "mandatory": True
            },
            {
                "document": "Blank Cheque or Cash Deposit",
                "description": "Blank cheque or cash deposit of 5000 rupees",
                "mandatory": True
            },
            {
                "document": "Contact Information",
                "description": "Valid phone number and email address",
                "mandatory": True
            },
            {
                "document": "Emergency Contact",
                "description": "Name and phone number of an emergency contact person",
                "mandatory": True
            }
        ],
        "additional_info": [
            "All documents must be valid and not expired",
            "You may need to show original documents during bike pickup",
            "For international tourists, passport and international driving permit are required"
        ]
    }


def get_host_info():
    """
    Get information about becoming a bike host on EasyMoto.
    
    Returns:
        dict: Steps and requirements to become a host.
    """
    return {
        "how_to_become_host": [
            {
                "step": 1,
                "title": "Create an Account",
                "description": "Sign up on EasyMoto platform with your details"
            },
            {
                "step": 2,
                "title": "List Your Bike",
                "description": "Add your bike details including photos, specifications, and pricing"
            },
            {
                "step": 3,
                "title": "Verification",
                "description": "Submit required documents for verification (bike registration, insurance, etc.)"
            },
            {
                "step": 4,
                "title": "Admin Approval",
                "description": "Wait for admin to review and approve your bike listing"
            },
            {
                "step": 5,
                "title": "Start Earning",
                "description": "Once approved, your bike will be visible to renters and you can start earning"
            }
        ],
        "requirements": [
            "Valid bike registration documents",
            "Comprehensive insurance coverage",
            "Bike must be in good working condition",
            "Clear photos of the bike from multiple angles",
            "Accurate description and specifications"
        ],
        "benefits": [
            "Earn passive income from your idle bike",
            "Set your own pricing and availability",
            "EasyMoto handles payment processing securely",
            "Insurance coverage during rental period",
            "24/7 customer support"
        ]
    }


def get_easymoto_info():
    """
    Get general information about EasyMoto service.
    
    Returns:
        dict: Company information and how the service works.
    """
    return {
        "about": "EasyMoto is a peer-to-peer bike rental platform that connects bike owners with people who need bikes for short-term rentals. We make it easy and affordable to rent bikes for daily commutes, weekend trips, or special occasions.",
        "how_it_works": {
            "for_renters": [
                "Browse available bikes on our platform",
                "Select your preferred bike and rental dates",
                "Complete the booking with secure online payment",
                "Pick up the bike at the specified location",
                "Enjoy your ride and return the bike on time"
            ],
            "for_hosts": [
                "List your bike with photos and details",
                "Set your own pricing and availability",
                "Get bookings from verified renters",
                "Earn money from your idle bike",
                "Receive payments securely through the platform"
            ]
        },
        "features": [
            "Wide variety of bikes (scooters, motorcycles, electric bikes)",
            "Flexible rental periods with attractive discounts",
            "Secure payment options (eSewa, PayPal, Cash)",
            "Verified users and bikes for safety",
            "24/7 customer support",
            "Easy booking and cancellation process"
        ],
        "mission": "To provide affordable and convenient bike rental solutions while helping bike owners monetize their assets.",
        "contact": "For support or inquiries, please contact us through the website contact form or customer support.",
        "location": "We are physically located in Budhanilkantha-03, Kathmandu, Nepal opposite to Park Village Resort."
    }


# ==================== TOOL DECLARATIONS ====================

# Define all function declarations for Gemini
check_availability_tool = FunctionDeclaration(
    name="check_availability",
    description="Check if bikes are available for rental for a specific date range. Use this when users ask about availability for specific dates.",
    parameters={
        "type": "object",
        "properties": {
            "start_date_str": {
                "type": "string",
                "description": "The start date of the rental in YYYY-MM-DD format."
            },
            "end_date_str": {
                "type": "string",
                "description": "The end date of the rental in YYYY-MM-DD format."
            },
            "bike_type": {
                "type": "string",
                "description": "Optional type of bike (e.g., 'scooter', 'motorcycle', 'electric')."
            }
        },
        "required": ["start_date_str", "end_date_str"]
    }
)

get_bike_listings_tool = FunctionDeclaration(
    name="get_bike_listings",
    description="Get a list of available bikes with optional filters. Use this when users want to browse bikes or ask 'what bikes do you have'.",
    parameters={
        "type": "object",
        "properties": {
            "bike_type": {
                "type": "string",
                "description": "Optional filter by bike type (scooter, motorcycle, electric)."
            },
            "max_price": {
                "type": "number",
                "description": "Optional maximum price per day filter."
            }
        }
    }
)

get_price_ranges_tool = FunctionDeclaration(
    name="get_price_ranges",
    description="Get pricing information including price ranges by bike type and discount structure. Use this when users ask about prices, costs, or discounts.",
    parameters={
        "type": "object",
        "properties": {}
    }
)

get_bike_details_tool = FunctionDeclaration(
    name="get_bike_details",
    description="Get detailed specifications and features of a specific bike. Use this when users ask about a specific bike's features or technical details.",
    parameters={
        "type": "object",
        "properties": {
            "bike_identifier": {
                "type": "string",
                "description": "Bike ID or name to get details for."
            }
        },
        "required": ["bike_identifier"]
    }
)

get_payment_methods_tool = FunctionDeclaration(
    name="get_payment_methods",
    description="Get information about available payment methods and payment options. Use this when users ask about how to pay or payment options.",
    parameters={
        "type": "object",
        "properties": {}
    }
)

get_required_documents_tool = FunctionDeclaration(
    name="get_required_documents",
    description="Get information about documents required to rent a bike. Use this when users ask what documents they need or rental requirements.",
    parameters={
        "type": "object",
        "properties": {}
    }
)

get_host_info_tool = FunctionDeclaration(
    name="get_host_info",
    description="Get information about how to become a bike host on EasyMoto. Use this when users ask about listing their bike or becoming a host.",
    parameters={
        "type": "object",
        "properties": {}
    }
)

get_easymoto_info_tool = FunctionDeclaration(
    name="get_easymoto_info",
    description="Get general information about EasyMoto service, how it works, and features. Use this when users ask about the company or how the service works.",
    parameters={
        "type": "object",
        "properties": {}
    }
)

# Create tools object with all function declarations
tools = Tool(function_declarations=[
    check_availability_tool,
    get_bike_listings_tool,
    get_price_ranges_tool,
    get_bike_details_tool,
    get_payment_methods_tool,
    get_required_documents_tool,
    get_host_info_tool,
    get_easymoto_info_tool
])

# ==================== CHATBOT RESPONSE HANDLER ====================

def get_chatbot_response(user_message):
    """
    Process the user message using Gemini and return the assistant's response.
    """
    try:
        # Reload API key to ensure it's picked up
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("DEBUG: GEMINI_API_KEY is missing.")
            return "Configuration Error: GEMINI_API_KEY is missing. Please check your .env file."
        
        genai.configure(api_key=api_key)

        # Enhanced system instruction
        system_instruction = """You are EasyMoto Assistant, a helpful and friendly AI assistant for EasyMoto bike rental service.

You can help users with:
- Checking bike availability for specific dates
- Browsing available bikes and their features
- Understanding pricing and discounts (5% for 7+ days, 10% for 14+ days, 15% for 21+ days, 20% for 28+ days)
- Learning about payment methods (eSewa, PayPal, Cash on Delivery)
- Finding out required documents for rental
- Understanding how to become a bike host
- General information about EasyMoto service

Always be helpful, concise, and friendly. When presenting bike information, format it nicely. When users want to book, guide them through checking availability first. If they ask about features or details of a specific bike, use the get_bike_details function.

For date-related queries, always use YYYY-MM-DD format. Today's date is """ + timezone.now().strftime("%Y-%m-%d") + "."

        try:
            # Create model with all tools
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                tools=[
                    check_availability,
                    get_bike_listings,
                    get_price_ranges,
                    get_bike_details,
                    get_payment_methods,
                    get_required_documents,
                    get_host_info,
                    get_easymoto_info
                ],
                system_instruction=system_instruction
            )
            
            # Start chat with automatic function calling enabled
            chat = model.start_chat(enable_automatic_function_calling=True)
            
            # Send message and get response
            response = chat.send_message(user_message)
            response_text = response.text
            
            print(f"DEBUG: Successfully generated response")
            return response_text
            
        except Exception as e:
            print(f"DEBUG: Error with gemini-1.5-flash: {e}")
            return f"I'm sorry, I'm having trouble connecting right now. Please try again. (Error: {str(e)})"

    except Exception as e:
        print(f"DEBUG: General Error in get_chatbot_response: {e}")
        return f"I'm sorry, I encountered an error: {str(e)}"
