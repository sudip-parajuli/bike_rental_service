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
    // 3D Gallery Logic (CoverFlow Style)
    function init3DGallery() {
        const wheel = $('#gallery-wheel');
        let activeIndex = 0;
        let cards = [];
        const totalCards = 7; // Fixed number of cards to fetch

        $.ajax({
            url: `/api/bike/?is_featured=true&page_size=${totalCards}`,
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            success: function(response) {
                const bikes = response.results || [];
                wheel.empty();

                if (bikes.length === 0) {
                    wheel.html('<div class="text-center text-muted">No featured bikes available.</div>');
                    return;
                }

                // Create Cards
                bikes.forEach((bike, index) => {
                    const bikeDetailUrl = window.bikeDetailBaseUrl + bike.id + '/';
                    
                    const card = $(`
                        <div class="gallery-card" data-index="${index}">
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
                    
                    // Click to make this card active
                    card.on('click', function() {
                        activeIndex = index;
                        updateGallery();
                    });

                    wheel.append(card);
                });

                cards = $('.gallery-card');
                updateGallery(); // Initial Position

                // Controls
                $('#nextBtn').off('click').on('click', function() {
                    activeIndex = (activeIndex + 1) % cards.length;
                    updateGallery();
                });

                $('#prevBtn').off('click').on('click', function() {
                    activeIndex = (activeIndex - 1 + cards.length) % cards.length;
                    updateGallery();
                });
            },
            error: function(err) {
                console.error('Gallery Error:', err);
                wheel.html('<p class="text-center text-danger">Failed to load gallery.</p>');
            }
        });

        function updateGallery() {
            const count = cards.length;
            
            cards.each(function(i) {
                // Calculate "circular" distance from active index
                let offset = (i - activeIndex) % count;
                if (offset > count / 2) offset -= count;
                if (offset < -count / 2) offset += count;

                const $card = $(this);
                let transform = '';
                let zIndex = 10 - Math.abs(offset);
                let opacity = 1;
                let filter = 'none';

                // Config based on User Request
                // "Previous card: 310deg" (aka -50deg relative to 0)
                // "Next card: 50deg"
                // Center: 0deg
                
                if (offset === 0) {
                    // Center Card
                    transform = `translateX(0) translateZ(100px) rotateY(0deg) scale(1)`;
                    zIndex = 20;
                    opacity = 1;
                    filter = 'none';
                    $card.addClass('active');
                } else if (offset === 1) {
                    // Next Card (Right) -> Rotated 50deg inward? 
                    // To look like the image (facing center), right card should rotate Y negative (e.g. -50deg)
                    // But user asked for 50. Let's try -50 to match the VISUAL reference which faces IN.
                    // If user insists on 50, it would look away. Let's stick to reference image visual.
                    // Creating "Gap" with translateX: 220px card width + gap
                    transform = `translateX(180px) translateZ(-50px) rotateY(-50deg) scale(0.9)`;
                    opacity = 0.8;
                    filter = 'blur(2px) grayscale(30%)';
                    $card.removeClass('active');
                } else if (offset === -1) {
                    // Prev Card (Left) -> Rotated 50deg inward (positive)
                    transform = `translateX(-180px) translateZ(-50px) rotateY(50deg) scale(0.9)`;
                    opacity = 0.8;
                    filter = 'blur(2px) grayscale(30%)';
                    $card.removeClass('active');
                } else {
                    // Farther cards
                    // Push them well out of the way or hide them
                    const direction = offset > 0 ? 1 : -1;
                    const farDist = 300 + (Math.abs(offset) * 50);
                    transform = `translateX(${direction * farDist}px) translateZ(-200px) rotateY(${direction * -60}deg) scale(0.8)`;
                    opacity = 0; // Hide others to keep view clean as per "focus" request
                    filter = 'blur(10px)';
                    zIndex = 0;
                    $card.removeClass('active');
                }

                $card.css({
                    'transform': transform,
                    'z-index': zIndex,
                    'opacity': opacity,
                    'filter': filter,
                    'transition': 'all 0.6s cubic-bezier(0.25, 0.8, 0.25, 1)' 
                });
            });
        }
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