/**
 * Bike Recommendations JavaScript
 * 
 * Handles fetching and displaying personalized bike recommendations
 * and similar bikes on various pages.
 */

(function($) {
    'use strict';

    /**
     * Load personalized recommendations for the user
     * @param {string} strategy - Recommendation strategy ('hybrid', 'popularity', 'content', 'collaborative')
     * @param {number} limit - Number of recommendations to fetch
     * @param {string} containerId - ID of the container element
     */
    function loadRecommendations(strategy = 'hybrid', limit = 6, containerId = 'recommended-bikes-container') {
        const container = $(`#${containerId}`);
        
        // Show loading state
        container.html(`
            <div class="col-12 text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading recommendations...</span>
                </div>
                <p class="mt-3 text-muted">Finding bikes you'll love...</p>
            </div>
        `);

        $.ajax({
            url: '/api/bike/recommendations/',
            method: 'GET',
            data: { strategy, limit },
            headers: {
                'Accept': 'application/json'
            },
            success: function(recommendations) {
                console.log('Recommendations loaded:', recommendations);
                displayRecommendations(recommendations, container);
            },
            error: function(xhr, status, error) {
                console.error('Error loading recommendations:', error);
                container.html(`
                    <div class="col-12 text-center py-5">
                        <i class="fas fa-exclamation-circle fa-3x text-warning mb-3"></i>
                        <p class="text-muted">Unable to load recommendations. Please try again later.</p>
                    </div>
                `);
            }
        });
    }

    /**
     * Display recommendations in the container
     * @param {Array} recommendations - Array of bike objects
     * @param {jQuery} container - Container element
     */
    function displayRecommendations(recommendations, container) {
        container.empty();

        if (!recommendations || recommendations.length === 0) {
            container.html(`
                <div class="col-12 text-center py-5">
                    <i class="fas fa-info-circle fa-3x text-info mb-3"></i>
                    <p class="text-muted">No recommendations available at the moment.</p>
                    <a href="/bikes/" class="btn btn-primary mt-3">Browse All Bikes</a>
                </div>
            `);
            return;
        }

        recommendations.forEach(bike => {
            const bikeCard = createBikeCard(bike, true);
            container.append(bikeCard);
        });
    }

    /**
     * Load similar bikes for a specific bike
     * @param {number} bikeId - ID of the bike
     * @param {number} limit - Number of similar bikes to fetch
     * @param {string} containerId - ID of the container element
     */
    function loadSimilarBikes(bikeId, limit = 6, containerId = 'similar-bikes-container') {
        const container = $(`#${containerId}`);
        
        // Show loading state
        container.html(`
            <div class="col-12 text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading similar bikes...</span>
                </div>
            </div>
        `);

        $.ajax({
            url: `/api/bike/${bikeId}/similar/`,
            method: 'GET',
            data: { limit },
            headers: {
                'Accept': 'application/json'
            },
            success: function(similarBikes) {
                console.log('Similar bikes loaded:', similarBikes);
                displayRecommendations(similarBikes, container);
            },
            error: function(xhr, status, error) {
                console.error('Error loading similar bikes:', error);
                container.html(`
                    <div class="col-12 text-center py-4">
                        <p class="text-muted">Unable to load similar bikes.</p>
                    </div>
                `);
            }
        });
    }

    /**
     * Create a bike card HTML element
     * @param {Object} bike - Bike object
     * @param {boolean} showRecommendationInfo - Whether to show recommendation score/reason
     * @returns {jQuery} Bike card element
     */
    function createBikeCard(bike, showRecommendationInfo = false) {
        const bikeDetailUrl = `/bikes/${bike.id}/`;
        const bookingCreateUrl = `/bookings/create/?bike_id=${bike.id}`;
        const imageUrl = bike.image || '/static/images/default-bike.png';
        const rating = bike.average_rating ? `⭐ ${parseFloat(bike.average_rating).toFixed(1)}` : 'No ratings yet';
        
        let recommendationBadge = '';
        if (showRecommendationInfo && bike.recommendation_score) {
            const scoreClass = bike.recommendation_score >= 70 ? 'success' : bike.recommendation_score >= 50 ? 'warning' : 'info';
            recommendationBadge = `
                <div class="position-absolute top-0 end-0 m-2">
                    <span class="badge bg-${scoreClass}">
                        ${Math.round(bike.recommendation_score)}% Match
                    </span>
                </div>
            `;
        }

        return $(`
            <div class="col-md-4 col-sm-6 mb-4">
                <div class="card h-100 shadow-sm hover-shadow position-relative">
                    ${recommendationBadge}
                    <img src="${imageUrl}" class="card-img-top" alt="${bike.name}" 
                         style="height: 200px; object-fit: cover;" 
                         onerror="this.src='/static/images/default-bike.png';">
                    <div class="card-body d-flex flex-column">
                        <h5 class="card-title">${bike.name}</h5>
                        <p class="card-text text-muted small mb-2">
                            <i class="fas fa-tag"></i> ${bike.type || 'N/A'} 
                            ${bike.brand ? `| ${bike.brand}` : ''}
                        </p>
                        ${showRecommendationInfo && bike.recommendation_reason ? `
                            <p class="card-text small text-primary mb-2">
                                <i class="fas fa-lightbulb"></i> ${bike.recommendation_reason}
                            </p>
                        ` : ''}
                        <p class="card-text">
                            <strong>NPR${bike.price_per_day}</strong>/day
                        </p>
                        <p class="card-text small text-muted">${rating}</p>
                        <div class="mt-auto d-flex gap-2">
                            <a href="${bikeDetailUrl}" class="btn btn-outline-primary btn-sm flex-fill">
                                <i class="fas fa-info-circle"></i> Details
                            </a>
                            <a href="${bookingCreateUrl}" class="btn btn-primary btn-sm flex-fill">
                                <i class="fas fa-calendar-check"></i> Book
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `);
    }

    /**
     * Initialize recommendations on page load
     */
    $(document).ready(function() {
        // Load recommendations on dashboard
        if ($('#recommended-bikes-container').length) {
            loadRecommendations('hybrid', 6, 'recommended-bikes-container');
        }

        // Load similar bikes on bike detail page
        if ($('#similar-bikes-container').length) {
            const bikeId = $('#similar-bikes-container').data('bike-id');
            if (bikeId) {
                loadSimilarBikes(bikeId, 6, 'similar-bikes-container');
            }
        }

        // Strategy selector (if exists)
        $('#recommendation-strategy').on('change', function() {
            const strategy = $(this).val();
            loadRecommendations(strategy, 6, 'recommended-bikes-container');
        });
    });

    // Expose functions globally for external use
    window.BikeRecommendations = {
        loadRecommendations,
        loadSimilarBikes,
        displayRecommendations,
        createBikeCard
    };

})(jQuery);
