from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    help = "Create an application Admin (role=admin) account. Usage: createadminuser <username> <email> <password>"

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("email")
        parser.add_argument("password")

    def handle(self, *args, **opts):
        if User.objects.filter(username=opts["username"]).exists():
            raise CommandError("Username already exists.")
        if User.objects.filter(email__iexact=opts["email"]).exists():
            raise CommandError("Email already exists.")
        User.objects.create_user(
            username=opts["username"],
            email=opts["email"],
            password=opts["password"],
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Admin '{opts['username']}' created."))
