from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # Import signals to ensure they are registered
        import users.signals

        # Self-healing database synchronizer for Site and Google SocialApp
        try:
            from django.contrib.sites.models import Site
            from allauth.socialaccount.models import SocialApp
            from decouple import config
            import sys

            # Run only when running the actual server (skip during migration/makemigrations)
            avoid_commands = {'migrate', 'makemigrations', 'collectstatic', 'test'}
            if not any(cmd in sys.argv for cmd in avoid_commands):
                # 1. Ensure Site ID=1 exists and has the correct domain
                domain_name = config('PRODUCTION_DOMAIN', default='www.easymoto.com.np')
                site, created = Site.objects.get_or_create(
                    id=1,
                    defaults={
                        'domain': domain_name,
                        'name': 'EasyMoto'
                    }
                )
                if not created and site.domain != domain_name:
                    site.domain = domain_name
                    site.save()

                # 2. Sync Google credentials from environment variables
                client_id = config('GOOGLE_CLIENT_ID', default=None)
                secret = config('GOOGLE_CLIENT_SECRET', default=None)

                if client_id and secret:
                    app, app_created = SocialApp.objects.get_or_create(
                        provider='google',
                        defaults={
                            'name': 'Google Auth',
                            'client_id': client_id,
                            'secret': secret
                        }
                    )
                    
                    # Update credentials if they changed in Render env settings
                    if not app_created:
                        if app.client_id != client_id or app.secret != secret:
                            app.client_id = client_id
                            app.secret = secret
                            app.save()

                    # 3. Ensure the SocialApp is linked to the Site
                    if not app.sites.filter(id=site.id).exists():
                        app.sites.add(site)

                    print(f"[Self-Healing] Successfully synchronized Google SocialApp for site: {site.domain}")
        except Exception as e:
            # Catch database exceptions gracefully during cold starts or migrations
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Self-healing database sync skipped: {e}")