import importlib
from django.core.management.base import BaseCommand
from django.apps import apps
from accounts.models import Permission


class Command(BaseCommand):
    help = "Discovers and syncs permissions from each app's permission.py into the database."

    def handle(self, *args, **options):
        total_synced = 0
        total_created = 0
        total_updated = 0

        self.stdout.write(self.style.NOTICE("Starting permissions synchronization..."))

        for app_config in apps.get_app_configs():
            module_path = f"{app_config.name}.permission"
            try:
                mod = importlib.import_module(module_path)
            except ModuleNotFoundError:
                continue

            perms = getattr(mod, 'PERMISSIONS', None) or getattr(mod, f"{app_config.name.upper()}_PERMISSIONS", None)
            if not perms:
                continue

            self.stdout.write(f"Found permissions in app '{app_config.name}' ({len(perms)} items)")
            for p in perms:
                app_name = getattr(p, 'app_name', None) or app_config.name
                obj, created = Permission.objects.update_or_create(
                    code_name=p.code_name,
                    defaults={
                        'name': p.name,
                        'module_name': p.module_name,
                        'app_name': app_name,
                        'description': p.description,
                    }
                )
                total_synced += 1
                if created:
                    total_created += 1
                else:
                    total_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully synced {total_synced} permissions ({total_created} created, {total_updated} updated)."
        ))
