$(document).ready(function() {
    // Initial load
    init3DGallery();
    initMagnifyingGlass();
    initAdvancedGooeyNav();
    loadTestimonials(1);

    /* --- Magnifying Glass Logic --- */
    function initMagnifyingGlass() {
        console.log("Initializing Magnifying Glass...");
        const wrapper = document.querySelector('.magnifying-wrapper');
        const glass = document.getElementById('magnifying-glass');

        if (wrapper && glass) {
            console.log("Magnifying Glass elements found.");
            wrapper.addEventListener('mousemove', function (e) {
                // Get viewport coordinates of the wrapper
                const rect = wrapper.getBoundingClientRect();
                
                // Calculate position relative to the wrapper
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                // Ensure we are hovering basically withinbounds (optional check)
                glass.style.display = 'block';
                
                // For fixed positioning of the glass (since it's z-index 9999 and fixed), 
                // we actually want to use clientX/Y to follow mouse directly on screen
                glass.style.left = e.clientX + 'px';
                glass.style.top = e.clientY + 'px';
            });

            wrapper.addEventListener('mouseleave', function () {
                glass.style.display = 'none';
            });
        } else {
            console.error("Magnifying Glass elements NOT found:", { wrapper, glass });
        }
    }

    /* --- Advanced Gooey Nav Logic (Ported from React) --- */
    function initAdvancedGooeyNav() {
        const container = document.getElementById('gooey-nav-container');
        const navList = document.getElementById('gooey-nav-list');
        const filterRef = container ? container.querySelector('.effect.filter') : null;
        const textRef = container ? container.querySelector('.effect.text') : null;
        
        if (!container || !navList || !filterRef || !textRef) return;

        // Configuration
        const particleCount = 12;
        const particleDistances = [40, 60]; // Adjusted for smaller nav items
        const animationTime = 500;
        const timeVariance = 200;
        const colors = ['1', '2', '3']; // We will map these to CSS vars or actual colors if needed
        // Actually, in CSS: var(--color-X). We need to ensure these vars exist or set color directly.
        // Let's use direct hex colors for simplicity in JS or assume vars.
        // CSS for .point uses var(--color).
        
        let activeIndex = 0;

        const noise = (n = 1) => n / 2 - Math.random() * n;

        const getXY = (distance, pointIndex, totalPoints) => {
            const angle = ((360 + noise(8)) / totalPoints) * pointIndex * (Math.PI / 180);
            return [distance * Math.cos(angle), distance * Math.sin(angle)];
        };

        const createParticle = (i, t, d, r) => {
            let rotate = noise(r / 10);
            return {
                start: getXY(d[0], particleCount - i, particleCount),
                end: getXY(d[1] + noise(7), particleCount - i, particleCount),
                time: t,
                scale: 1 + noise(0.2),
                color: colors[Math.floor(Math.random() * colors.length)],
                rotate: rotate > 0 ? (rotate + r / 20) * 10 : (rotate - r / 20) * 10
            };
        };

        const makeParticles = (element) => {
            const d = particleDistances;
            const r = 100; // particleR
            const bubbleTime = animationTime * 2 + timeVariance;
            element.style.setProperty('--time', `${bubbleTime}ms`);

            // Colors mapping (Blue, Purple, Pink)
            const colorMap = {
                '1': '#2563eb', // Blue
                '2': '#7c3aed', // Purple
                '3': '#ec4899'  // Pink
            };

            for (let i = 0; i < particleCount; i++) {
                const t = animationTime * 2 + noise(timeVariance * 2);
                const p = createParticle(i, t, d, r);
                
                // We need to append to the filterRef (element)
                // But checking the React code, particles are appended to the filter element
                // And active class is toggled to trigger animation.
                
                setTimeout(() => {
                    const particle = document.createElement('span');
                    const point = document.createElement('span');
                    particle.classList.add('particle');
                    
                    particle.style.setProperty('--start-x', `${p.start[0]}px`);
                    particle.style.setProperty('--start-y', `${p.start[1]}px`);
                    particle.style.setProperty('--end-x', `${p.end[0]}px`);
                    particle.style.setProperty('--end-y', `${p.end[1]}px`);
                    particle.style.setProperty('--time', `${p.time}ms`);
                    
                    point.classList.add('point');
                    point.style.setProperty('--scale', `${p.scale}`);
                    point.style.setProperty('--color', colorMap[p.color]);
                    particle.style.setProperty('--rotate', `${p.rotate}deg`);

                    particle.appendChild(point);
                    element.appendChild(particle);

                    // Trigger reflow/animation
                    // In vanilla, we just append and the animation starts due to CSS (assuming active class isn't blocking)
                    // The React code removes 'active' then re-adds it. 
                    // Here we essentially create new particles which run their keyframes on mount.
                    
                    setTimeout(() => {
                        if (particle.parentNode === element) {
                            element.removeChild(particle);
                        }
                    }, p.time); // Remove after animation
                }, i * 10); // Stagger creation slightly
            }
        };

        const updateEffectPosition = (element) => {
            const containerRect = container.getBoundingClientRect();
            const pos = element.getBoundingClientRect();

            const styles = {
                left: `${pos.x - containerRect.x}px`,
                top: `${pos.y - containerRect.y}px`,
                width: `${pos.width}px`,
                height: `${pos.height}px`
            };
            
            Object.assign(filterRef.style, styles);
            Object.assign(textRef.style, styles);
            
            // Clone the content (icon) to the textRef for the "morphing" text effect
            textRef.innerHTML = element.innerHTML;
        };

        const handleItemClick = (e, index, liEl) => {
            if (activeIndex === index) return;
            
            // Update active class on LIs
            const items = navList.querySelectorAll('li');
            items.forEach(item => item.classList.remove('active'));
            liEl.classList.add('active');
            
            activeIndex = index;
            updateEffectPosition(liEl);
            
            // Remove existing particles
            const existingParticles = filterRef.querySelectorAll('.particle');
            existingParticles.forEach(p => p.remove());

            // Trigger text active animation
            textRef.classList.remove('active');
            void textRef.offsetWidth; // Force reflow
            textRef.classList.add('active');

            // Trigger filter active animation (pill expand)
            filterRef.classList.remove('active');
            void filterRef.offsetWidth; 
            filterRef.classList.add('active');

            // Create particles
            makeParticles(filterRef);
        };

        // Initialize items
        const items = navList.querySelectorAll('li');
        items.forEach((item, index) => {
            const link = item.querySelector('a');
            
            link.addEventListener('click', (e) => {
                // e.preventDefault(); // Optional: allow navigation
                handleItemClick(e, index, item);
            });
            
            if (item.classList.contains('active')) {
                activeIndex = index;
                // Delay initial position update slightly to ensure layout is done
                setTimeout(() => {
                    updateEffectPosition(item);
                    textRef.classList.add('active');
                    filterRef.classList.add('active');
                }, 100);
            }
        });

        // Handle Resize
        window.addEventListener('resize', () => {
            const currentActive = navList.querySelectorAll('li')[activeIndex];
            if (currentActive) updateEffectPosition(currentActive);
        });
    }

    // Fetch featured bikes with search/filter
    // 3D Gallery Logic
    function init3DGallery() {
        const wheel = $('#gallery-wheel');
        const radius = 500; // Increased radius to reduce overlap and show 50% of side cards
        let theta = 0;
        
        // Inject styles for active/blur state if not in CSS
        if (!$('#gallery-styles').length) {
            $('head').append(`
                <style id="gallery-styles">
                    .gallery-card {
                        transition: transform 1s, filter 0.5s, opacity 0.5s;
                        filter: blur(4px) grayscale(50%); /* Default state: blurred */
                        opacity: 0.6;
                        cursor: pointer;
                    }
                    .gallery-card.active {
                        filter: blur(0) grayscale(0);
                        opacity: 1;
                        z-index: 10;
                    }
                </style>
            `);
        }

        $.ajax({
            url: '/api/bike/?is_featured=true&page_size=8', 
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            success: function(response) {
                const bikes = response.results || [];
                wheel.empty();

                if (bikes.length === 0) {
                    wheel.html('<div class="text-center text-muted">No featured bikes available.</div>');
                    return;
                }

                const total = bikes.length;
                const angleStep = 360 / total;

                // Create Cards
                bikes.forEach((bike, index) => {
                    const angle = angleStep * index;
                    const bikeDetailUrl = window.bikeDetailBaseUrl + bike.id + '/';
                    
                    const card = $(`
                        <div class="gallery-card" data-index="${index}" style="transform: rotateY(${angle}deg) translateZ(${radius}px);">
                            <img src="${bike.image || '/static/images/default-bike.png'}" alt="${bike.name}" onerror="this.src='/static/images/default-bike.png';">
                            <div class="gallery-card-content">
                                <div>
                                    <h5 class="fw-bold mb-1">${bike.name}</h5>
                                    <p class="text-primary fw-bold mb-2">Rs. ${bike.price_per_day} <span class="text-muted small fw-normal">/ day</span></p>
                                </div>
                                <a href="${bikeDetailUrl}" class="btn btn-sm btn-gradient rounded-pill w-100 shadow-sm">View Details</a>
                            </div>
                        </div>
                    `);
                    
                    // Click to rotate to this card
                    card.on('click', function() {
                        const targetTheta = -(index * angleStep);
                        // Find shortest path
                        const currentRot = theta % 360;
                        const targetRot = targetTheta % 360;
                        let diff = targetRot - currentRot;
                        if (diff < -180) diff += 360;
                        if (diff > 180) diff -= 360;
                        
                        theta += diff;
                        rotateWheel();
                    });

                    wheel.append(card);
                });

                // Update Active State
                function rotateWheel() {
                    wheel.css('transform', `rotateY(${theta}deg)`);
                    
                    // Calculate active index
                    // Normalize theta to positive equivalent for easy mod
                    let normalizedTheta = -theta % 360;
                    if (normalizedTheta < 0) normalizedTheta += 360;
                    
                    // The interaction logic: which angle is closest to 0 (front)?
                    // Card angle is `index * angleStep`.
                    // We want `index * angleStep + theta ~= 0 (mod 360)`
                    // So `index * angleStep ~= -theta`
                    
                    // Find closest index
                    let activeIndex = Math.round(normalizedTheta / angleStep) % total;
                    
                    $('.gallery-card').removeClass('active');
                    $(`.gallery-card[data-index="${activeIndex}"]`).addClass('active');
                }

                // Initial Active
                rotateWheel();

                // Controls
                $('#nextBtn').off('click').on('click', function() {
                    theta -= angleStep;
                    rotateWheel();
                });

                $('#prevBtn').off('click').on('click', function() {
                    theta += angleStep;
                    rotateWheel();
                });
            },
            error: function(err) {
                console.error('Gallery Error:', err);
                wheel.html('<p class="text-center text-danger">Failed to load gallery.</p>');
            }
        });
    }

    // Fetch testimonials
    function loadTestimonials(page = 1) {
        $.ajax({
            url: '/api/testimonial/?is_featured=true&page=' + page + '&page_size=3',
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
                                        <footer class="blockquote-footer">By ${testimonial.user} - ${testimonial.rating} stars</footer>
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
    init3DGallery(); // Ensure this is called if not already at the top, or just rely on the top call.
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