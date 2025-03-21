$(document).ready(function() {
    // Fetch featured bikes with search/filter
    function loadFeaturedBikes(page = 1, search = '', filter = '') {
        let url = '/api/bike/?is_featured=true&page=' + page + '&page_size=3';
        if (search) url += '&search=' + encodeURIComponent(search);
        if (filter) {
            if (filter === 'available') url += '&availability_status=true';
            else if (filter) url += '&type=' + filter;
        }

        $.ajax({
            url: url,
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            },
            success: function(response) {
                console.log('Bikes API response:', response);
                const bikes = response.results || [];
                const container = $('#featured-bikes-container');
                container.empty();
                console.log('Number of bikes:', bikes.length);
                if (bikes.length === 0) {
                    container.html('<p class="text-center">No featured bikes available. Contact an admin to add featured bikes.</p>');
                } else {
                    bikes.forEach(bike => {
                        const bikeDetailUrl = `${window.bikeDetailBaseUrl}${bike.id}/`;
                        const bookingCreateUrl = `${window.bookingCreateBaseUrl}?bike_id=${bike.id}`;

                        container.append(`
                            <div class="col-md-4">
                                <div class="card mb-3" style="width: 18rem;">
                                    <img src="${bike.image || '/static/images/default-bike.png'}" class="card-img-top" alt="${bike.name}" onerror="this.src='/static/images/default-bike.png';">
                                    <div class="card-body text-center">
                                        <h5 class="card-title"> ${bike.name}</h5>
                                        <p class="card-text">Price per day: $${bike.price_per_day}</p>
                                        <div class="d-flex justify-content-between">
                                            <a href="${bikeDetailUrl}" class="btn btn-primary">View Details</a>
                                            <a href="${bookingCreateUrl}" class="btn btn-success ${!bike.availability_status ? 'disabled' : ''}">Book Now</a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `);
                    });

                    // Update pagination
                    const paginator = response;
                    const pagination = $('#featured-bikes-pagination');
                    pagination.empty();
                    if (paginator.previous) {
                        pagination.append(`<li class="page-item"><a class="page-link" href="#" data-page="${paginator.previous_page || (page - 1)}">«</a></li>`);
                    }
                    for (let i = 1; i <= (paginator.total_pages || 1); i++) {
                        pagination.append(`<li class="page-item ${page === i ? 'active' : ''}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`);
                    }
                    if (paginator.next) {
                        pagination.append(`<li class="page-item"><a class="page-link" href="#" data-page="${paginator.next_page || (page + 1)}">»</a></li>`);
                    }
                    pagination.find('a').on('click', function(e) {
                        e.preventDefault();
                        loadFeaturedBikes($(this).data('page'), $('#bikeSearchInput').val(), $('#bikeFilter').val());
                    });
                }
            },
            error: function(xhr, status, error) {
                console.error('Error fetching bikes:', error, xhr.responseText);
                $('#featured-bikes-container').html('<p class="text-center">Failed to load bikes. Please try again later.</p>');
            }
        });
    }

    // Fetch testimonials
    function loadTestimonials(page = 1) {
        $.ajax({
            url: '/api/testimonial/?page=' + page + '&page_size=3',
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            },
            success: function(response) {
                console.log('Testimonials API response:', response);
                const testimonials = response.results || [];
                const container = $('#testimonials-container');
                container.empty();
                console.log('Number of testimonials:', testimonials.length);
                if (testimonials.length === 0) {
                    container.html('<p class="text-center">No testimonials available.</p>');
                } else {
                    testimonials.forEach(testimonial => {
                        container.append(`
                            <div class="col-md-4">
                                <div class="card mb-3" style="width: 18rem;">
                                    <div class="card-body text-center">
                                        <p class="card-text">${testimonial.content}</p>
                                        <footer class="blockquote-footer">By ${testimonial.user.username} - ${testimonial.rating} stars</footer>
                                    </div>
                                </div>
                            </div>
                        `);
                    });

                    // Update pagination
                    const paginator = response;
                    const pagination = $('#testimonials-pagination');
                    pagination.empty();
                    if (paginator.previous) {
                        pagination.append(`<li class="page-item"><a class="page-link" href="#" data-page="${paginator.previous_page || (page - 1)}">«</a></li>`);
                    }
                    for (let i = 1; i <= (paginator.total_pages || 1); i++) {
                        pagination.append(`<li class="page-item ${page === i ? 'active' : ''}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`);
                    }
                    if (paginator.next) {
                        pagination.append(`<li class="page-item"><a class="page-link" href="#" data-page="${paginator.next_page || (page + 1)}">»</a></li>`);
                    }
                    pagination.find('a').on('click', function(e) {
                        e.preventDefault();
                        loadTestimonials($(this).data('page'));
                    });
                }
            },
            error: function(xhr, status, error) {
                console.error('Error fetching testimonials:', error, xhr.responseText);
                $('#testimonials-container').html('<p class="text-center">Failed to load testimonials. Please try again later.</p>');
            }
        });
    }

    // Handle search and filter
    $('#bikeSearchForm').on('submit', function(e) {
        e.preventDefault();
        const search = $('#bikeSearchInput').val();
        const filter = $('#bikeFilter').val();
        window.location.href = `{% url 'bikes:bike-list' %}?search=${encodeURIComponent(search)}&type=${encodeURIComponent(filter === 'available' ? '' : filter)}&availability_status=${encodeURIComponent(filter === 'available' ? 'true' : '')}`;
    });

    $('#bikeFilter').on('change', function() {
        const search = $('#bikeSearchInput').val();
        const filter = $(this).val();
        window.location.href = `{% url 'bikes:bike-list' %}?search=${encodeURIComponent(search)}&type=${encodeURIComponent(filter === 'available' ? '' : filter)}&availability_status=${encodeURIComponent(filter === 'available' ? 'true' : '')}`;
    });

    // Initial load
    loadFeaturedBikes(1);
    loadTestimonials(1);

    // Contact form submission
    $('#contactForm').on('submit', function(e) {
        e.preventDefault();

        // Collect form data as a JSON object
        const formData = {
            name: $('#name').val(),
            email: $('#email').val(),
            contact_number: $('#contact_number').val(),
            message: $('#message').val()
        };

        $.ajax({
            url: '/api/user/contact/',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            headers: {
                'X-CSRFToken': csrftoken  // Include the CSRF token
            },
            success: function(response) {
                alert('Message sent successfully!');
                $('#contactForm')[0].reset();
                $('#contactForm').removeClass('was-validated');
            },
            error: function(xhr, status, error) {
                let errorMessage = 'Error sending message: ';
                if (xhr.status === 400) {
                    const errors = xhr.responseJSON.errors;
                    errorMessage += '\n';
                    for (const field in errors) {
                        errorMessage += `${field}: ${errors[field]}\n`;
                    }
                } else {
                    errorMessage += error;
                }
                alert(errorMessage);
            }
        });
    });
});