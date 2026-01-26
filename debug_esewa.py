import os
import django
import hmac
import hashlib
import base64

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bike_rental_service.settings')
django.setup()

from django.conf import settings

def debug_esewa_config():
    output = []
    output.append("--- eSewa Configuration Debug ---")
    secret_key = settings.ESEWA_SECRET_KEY
    product_code = settings.ESEWA_PRODUCT_CODE
    
    output.append(f"Secret Key: '{secret_key}'")
    output.append(f"Product Code: '{product_code}'")
    
    # Test Signature Generation
    total_amount = "100.00"
    transaction_uuid = "test_txn_123"
    
    message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
    output.append(f"Test Message: '{message}'")
    
    signature = base64.b64encode(
        hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode('utf-8')
    
    output.append(f"Test Signature: '{signature}'")
    output.append("---------------------------------")
    
    with open('debug_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    print("Debug output written to debug_result.txt")

if __name__ == "__main__":
    debug_esewa_config()
