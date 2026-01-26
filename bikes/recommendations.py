"""
Bike Recommendation System

This module provides personalized bike recommendations using multiple strategies:
1. Popularity-based: Recommend highly-rated and frequently booked bikes
2. Content-based: Recommend bikes similar to user's rental history
3. Collaborative filtering: Recommend bikes that similar users have rented
4. Hybrid: Combine all strategies with weighted scoring
"""

from django.db.models import Count, Avg, Q, F
from django.core.cache import cache
from bikes.models import Bike
from bookings.models import Booking, Feedback
from collections import Counter
from datetime import timedelta
from django.utils import timezone


class BikeRecommendationEngine:
    """
    Main recommendation engine that provides personalized bike suggestions.
    """
    
    def __init__(self, user=None):
        self.user = user
        self.cache_timeout = 3600  # 1 hour cache
    
    def get_recommendations(self, strategy='hybrid', limit=6, exclude_ids=None, evaluation_mode=False):
        """
        Get bike recommendations based on the specified strategy.
        
        Args:
            strategy: 'popularity', 'content', 'collaborative', or 'hybrid'
            limit: Number of recommendations to return
            exclude_ids: List of bike IDs to exclude from recommendations
            evaluation_mode: If True, allows recommending bikes already rented (for testing)
            
        Returns:
            QuerySet of recommended bikes with recommendation_score and recommendation_reason
        """
        exclude_ids = exclude_ids or []
        
        # Check cache first (ignore cache in evaluation mode)
        if self.user and self.user.is_authenticated and not evaluation_mode:
            cache_key = f'recommendations_{self.user.id}_{strategy}_{limit}'
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
        
        # Get recommendations based on strategy
        if strategy == 'popularity':
            recommendations = self._get_popular_bikes(limit, exclude_ids)
        elif strategy == 'content' and self.user and self.user.is_authenticated:
            recommendations = self._get_content_based_recommendations(limit, exclude_ids, evaluation_mode)
        elif strategy == 'collaborative' and self.user and self.user.is_authenticated:
            recommendations = self._get_collaborative_recommendations(limit, exclude_ids, evaluation_mode)
        elif strategy == 'hybrid' and self.user and self.user.is_authenticated:
            recommendations = self._get_hybrid_recommendations(limit, exclude_ids, evaluation_mode)
        else:
            # Default to popularity for unauthenticated users
            recommendations = self._get_popular_bikes(limit, exclude_ids)
        
        # Cache the result
        if self.user and self.user.is_authenticated and not evaluation_mode:
            cache.set(cache_key, recommendations, self.cache_timeout)
        
        return recommendations
    
    def _get_popular_bikes(self, limit=6, exclude_ids=None):
        """
        Get popular bikes based on ratings and booking frequency.
        
        Scoring:
        - Average rating (0-5): 50% weight
        - Booking count (normalized): 50% weight
        """
        exclude_ids = exclude_ids or []
        
        # Get bikes with their stats
        bikes = Bike.objects.filter(
            is_approved=True,
            availability_status=True
        ).exclude(
            id__in=exclude_ids
        ).annotate(
            booking_count=Count('bookings', filter=Q(bookings__status='completed')),
            avg_rating=Avg('bookings__feedback__rating')
        )
        
        # Calculate scores
        scored_bikes = []
        max_bookings = bikes.aggregate(max_count=Count('bookings'))['max_count'] or 1
        
        for bike in bikes:
            # Rating score (0-50)
            rating_score = ((bike.avg_rating or 3.0) / 5.0) * 50
            
            # Booking frequency score (0-50)
            booking_score = (bike.booking_count / max_bookings) * 50
            
            # Total score
            total_score = rating_score + booking_score
            
            bike.recommendation_score = round(total_score, 2)
            bike.recommendation_reason = f"Popular choice with {bike.avg_rating or 'N/A'} rating"
            scored_bikes.append(bike)
        
        # Sort by score and return top N
        scored_bikes.sort(key=lambda x: x.recommendation_score, reverse=True)
        return scored_bikes[:limit]
    
    def _get_content_based_recommendations(self, limit=6, exclude_ids=None, evaluation_mode=False):
        """
        Recommend bikes similar to user's rental history.
        
        Analyzes:
        - Bike type preference
        - Brand preference
        - Price range preference
        - Feature preferences (engine type, displacement)
        """
        exclude_ids = exclude_ids or []
        
        # Get user's rental history
        user_bookings = Booking.objects.filter(
            user=self.user,
            status='completed'
        ).select_related('bike')
        
        if not user_bookings.exists():
            # No history, fall back to popular bikes
            return self._get_popular_bikes(limit, exclude_ids)
        
        # Analyze user preferences
        rented_bikes = [booking.bike for booking in user_bookings]
        
        # Type preference
        type_counter = Counter([bike.type for bike in rented_bikes])
        preferred_type = type_counter.most_common(1)[0][0] if type_counter else None
        
        # Brand preference
        brand_counter = Counter([bike.brand for bike in rented_bikes if bike.brand])
        preferred_brand = brand_counter.most_common(1)[0][0] if brand_counter else None
        
        # Price range
        prices = [float(bike.price_per_day) for bike in rented_bikes]
        avg_price = sum(prices) / len(prices) if prices else 0
        price_tolerance = avg_price * 0.3  # 30% tolerance
        
        # Get candidate bikes
        bikes = Bike.objects.filter(
            is_approved=True,
            availability_status=True
        ).exclude(
            id__in=exclude_ids
        )
        
        if not evaluation_mode:
            bikes = bikes.exclude(id__in=[bike.id for bike in rented_bikes])  # Exclude already rented
        
        # Score each bike
        scored_bikes = []
        for bike in bikes:
            score = 0
            reasons = []
            
            # Type match (30 points)
            if bike.type == preferred_type:
                score += 30
                reasons.append(f"matches your preference for {preferred_type}s")
            
            # Brand match (20 points)
            if bike.brand == preferred_brand:
                score += 20
                reasons.append(f"from your preferred brand {preferred_brand}")
            
            # Price range match (20 points)
            if avg_price - price_tolerance <= float(bike.price_per_day) <= avg_price + price_tolerance:
                score += 20
                reasons.append("in your price range")
            
            # Rating bonus (30 points max)
            if bike.average_rating:
                score += (float(bike.average_rating) / 5.0) * 30
            
            if score > 0:
                bike.recommendation_score = round(score, 2)
                bike.recommendation_reason = "Similar to your rentals: " + ", ".join(reasons[:2])
                scored_bikes.append(bike)
        
        # Sort by score and return top N
        scored_bikes.sort(key=lambda x: x.recommendation_score, reverse=True)
        return scored_bikes[:limit]
    
    def _get_collaborative_recommendations(self, limit=6, exclude_ids=None, evaluation_mode=False):
        """
        Recommend bikes that similar users have rented.
        
        Finds users with similar rental patterns and recommends their bikes.
        """
        exclude_ids = exclude_ids or []
        
        # Get user's rented bike IDs
        user_bike_ids = set(
            Booking.objects.filter(
                user=self.user,
                status='completed'
            ).values_list('bike_id', flat=True)
        )
        
        if not user_bike_ids:
            # No history, fall back to popular bikes
            return self._get_popular_bikes(limit, exclude_ids)
        
        # Find similar users (users who rented at least one same bike)
        similar_users = Booking.objects.filter(
            bike_id__in=user_bike_ids,
            status='completed'
        ).exclude(
            user=self.user
        ).values_list('user_id', flat=True).distinct()
        
        # Get bikes rented by similar users
        recommended_bike_ids = Booking.objects.filter(
            user_id__in=similar_users,
            status='completed'
        ).exclude(
            bike_id__in=exclude_ids
        )
        
        if not evaluation_mode:
            recommended_bike_ids = recommended_bike_ids.exclude(bike_id__in=user_bike_ids)
            
        recommended_bike_ids = recommended_bike_ids.values('bike_id').annotate(
            rental_count=Count('id'),
            avg_rating=Avg('feedback__rating')
        ).order_by('-rental_count', '-avg_rating')
        
        # Get the actual bikes
        bikes = Bike.objects.filter(
            id__in=[item['bike_id'] for item in recommended_bike_ids[:limit * 2]],
            is_approved=True,
            availability_status=True
        )
        
        # Score bikes
        scored_bikes = []
        for bike in bikes:
            # Find the stats for this bike
            stats = next((item for item in recommended_bike_ids if item['bike_id'] == bike.id), None)
            if stats:
                score = (stats['rental_count'] * 10) + ((stats['avg_rating'] or 3.0) * 10)
                bike.recommendation_score = round(score, 2)
                bike.recommendation_reason = f"Rented by {stats['rental_count']} similar users"
                scored_bikes.append(bike)
        
        scored_bikes.sort(key=lambda x: x.recommendation_score, reverse=True)
        return scored_bikes[:limit]
    
    def _get_hybrid_recommendations(self, limit=6, exclude_ids=None, evaluation_mode=False):
        """
        Combine all recommendation strategies with weighted scoring.
        
        Weights:
        - Content-based: 40%
        - Collaborative: 40%
        - Popularity: 20%
        """
        exclude_ids = exclude_ids or []
        
        # Get recommendations from each strategy
        content_recs = self._get_content_based_recommendations(limit * 2, exclude_ids, evaluation_mode)
        collab_recs = self._get_collaborative_recommendations(limit * 2, exclude_ids, evaluation_mode)
        popular_recs = self._get_popular_bikes(limit * 2, exclude_ids)
        
        # Combine and weight scores
        bike_scores = {}
        
        for bike in content_recs:
            bike_scores[bike.id] = {
                'bike': bike,
                'score': bike.recommendation_score * 0.4,
                'reasons': [bike.recommendation_reason]
            }
        
        for bike in collab_recs:
            if bike.id in bike_scores:
                bike_scores[bike.id]['score'] += bike.recommendation_score * 0.4
                bike_scores[bike.id]['reasons'].append(bike.recommendation_reason)
            else:
                bike_scores[bike.id] = {
                    'bike': bike,
                    'score': bike.recommendation_score * 0.4,
                    'reasons': [bike.recommendation_reason]
                }
        
        for bike in popular_recs:
            if bike.id in bike_scores:
                bike_scores[bike.id]['score'] += bike.recommendation_score * 0.2
            else:
                bike_scores[bike.id] = {
                    'bike': bike,
                    'score': bike.recommendation_score * 0.2,
                    'reasons': [bike.recommendation_reason]
                }
        
        # Create final list
        final_recommendations = []
        for bike_id, data in sorted(bike_scores.items(), key=lambda x: x[1]['score'], reverse=True)[:limit]:
            bike = data['bike']
            bike.recommendation_score = round(data['score'], 2)
            bike.recommendation_reason = data['reasons'][0] if data['reasons'] else "Recommended for you"
            final_recommendations.append(bike)
        
        return final_recommendations
    
    def get_similar_bikes(self, bike_id, limit=6):
        """
        Get bikes similar to a specific bike.
        
        Args:
            bike_id: ID of the bike to find similar bikes for
            limit: Number of similar bikes to return
            
        Returns:
            List of similar bikes
        """
        try:
            reference_bike = Bike.objects.get(id=bike_id)
        except Bike.DoesNotExist:
            return []
        
        # Find similar bikes
        similar_bikes = Bike.objects.filter(
            is_approved=True,
            availability_status=True,
            type=reference_bike.type  # Same type
        ).exclude(
            id=bike_id
        )
        
        # Score by similarity
        scored_bikes = []
        for bike in similar_bikes:
            score = 0
            reasons = []
            
            # Same brand (30 points)
            if bike.brand == reference_bike.brand:
                score += 30
                reasons.append(f"same brand ({bike.brand})")
            
            # Similar price (30 points)
            price_diff = abs(float(bike.price_per_day) - float(reference_bike.price_per_day))
            price_similarity = max(0, 30 - (price_diff / float(reference_bike.price_per_day)) * 30)
            score += price_similarity
            if price_similarity > 15:
                reasons.append("similar price")
            
            # Rating (20 points)
            if bike.average_rating:
                score += (float(bike.average_rating) / 5.0) * 20
            
            # Same features (20 points)
            if bike.engine_type == reference_bike.engine_type:
                score += 10
            if bike.displacement == reference_bike.displacement:
                score += 10
                reasons.append("similar specs")
            
            bike.recommendation_score = round(score, 2)
            bike.recommendation_reason = "Similar: " + ", ".join(reasons[:2]) if reasons else "Similar bike"
            scored_bikes.append(bike)
        
        scored_bikes.sort(key=lambda x: x.recommendation_score, reverse=True)
        return scored_bikes[:limit]


# Convenience functions
def get_recommendations_for_user(user, strategy='hybrid', limit=6, exclude_ids=None):
    """Get recommendations for a specific user."""
    engine = BikeRecommendationEngine(user=user)
    return engine.get_recommendations(strategy=strategy, limit=limit, exclude_ids=exclude_ids)


def get_popular_bikes(limit=6, exclude_ids=None):
    """Get popular bikes (no user context needed)."""
    engine = BikeRecommendationEngine()
    return engine._get_popular_bikes(limit=limit, exclude_ids=exclude_ids)


def get_similar_bikes(bike_id, limit=6):
    """Get bikes similar to a specific bike."""
    engine = BikeRecommendationEngine()
    return engine.get_similar_bikes(bike_id=bike_id, limit=limit)
