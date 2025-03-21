document.addEventListener('DOMContentLoaded', () => {
    // Example: Handle booking form submission with AJAX
    const bookingForm = document.querySelector('#bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(bookingForm);
            try {
                const response = await fetch('/api/bookings/create/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Token ${localStorage.getItem('token')}`  // Assume token is stored
                    },
                    body: JSON.stringify(Object.fromEntries(formData))
                });
                const data = await response.json();
                if (data.success) {
                    alert(data.message);
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;  // Redirect to payment
                    } else {
                        window.location.href = '/bookings/';  // Redirect to bookings list
                    }
                } else {
                    alert('Error: ' + JSON.stringify(data.errors));
                }
            } catch (error) {
                alert('An error occurred: ' + error);
            }
        });
    }
});