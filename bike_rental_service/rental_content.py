"""Verified business information; keep visible copy and structured data aligned."""
FAQS = [
    ('Booking', 'How do I reserve a scooter or motorcycle?', 'Browse the fleet, choose a bike and share your pickup and return dates. Confirm availability, the total price and rental terms with EasyMoto before paying. You can also contact us on WhatsApp.'),
    ('Documents', 'What documents do Nepali customers need?', 'Bring a National ID, citizenship certificate or passport, a valid driving licence for verification, and a blank cheque or cash deposit. Confirm the deposit arrangement with our team before pickup.'),
    ('Documents', 'What should international customers bring?', 'Bring your passport, valid driving licence, International Driving Permit (IDP), a cash security deposit, and a letter of accommodation or a guarantor from Nepal. Contact us before booking to confirm your documents and licence category.'),
    ('Pickup', 'Where is the EasyMoto pickup location?', 'Our shop is in Budhanilkantha-03, Kathmandu, opposite Park Village Resort. Agree on your pickup time with our team before arriving.'),
    ('Pricing', 'How much is the security deposit?', 'The deposit is usually NPR 5,000. The exact amount depends on the two-wheeler, rental duration and arrangement. Confirm your amount, accepted deposit method, refund timing and deductions before booking.'),
    ('Pricing', 'What does the daily rental price include?', 'We provide a helmet. Fuel is paid for by the renter. Each bike lists its daily rate; confirm the total price, insurance coverage and any other charges before paying.'),
    ('Pricing', 'Do you offer hourly rentals and when must I return?', 'We offer daily rentals, not hourly rentals. The rental day ends at 7 PM. If you do not return the bike by then, a NPR 500 night or late-return charge is added. Agree on your pickup and return arrangements before setting off.'),
    ('Trips', 'Can I rent for several days or a longer stay?', 'Tell us your dates and intended route. We can discuss a suitable scooter or motorcycle and confirm availability and a quote for your full rental period.'),
    ('Trips', 'Can I take the bike outside Kathmandu?', 'Share your route before booking so we can confirm permitted destinations and vehicle suitability. Check road conditions and weather before riding; do not assume every bike is suitable for mountain or off-road travel.'),
    ('Booking', 'What if I need to cancel or return late?', 'Contact EasyMoto as soon as your plans change. A NPR 500 night or late-return charge applies if you do not return by 7 PM. Ask for the cancellation policy before confirming your reservation.'),
    ('Pickup', 'When is the shop open?', 'Our Google business profile lists Sunday to Friday 7:00 AM–6:30 PM and Saturday 8:30 AM–4:00 PM. Holiday hours may differ; confirm your pickup appointment with our team.'),
]

def public_context():
    return {'rental_faqs': [{'category': c, 'question': q, 'answer': a} for c, q, a in FAQS]}
