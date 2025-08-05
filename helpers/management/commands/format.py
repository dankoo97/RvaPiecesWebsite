import subprocess

from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Formats the project"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Fix formatting errors",
        )

        parser.add_argument(
            "--path",
            type=str,
            help="Path to the file or directory to format, otherwise formats the entire project",
        )

        parser.add_argument(
            "--html",
            action="store_true",
            help="Format html files",
        )

        parser.add_argument(
            "--python",
            action="store_true",
            help="Format python files",
        )

    def handle(self, *args, **options):
        if options["python"]:
            subprocess.run(
                [
                    "ruff",
                    "format" if options["fix"] else "check",
                    options["path"] or ".",
                ],
                check=False,
            )

        if options["html"]:
            subprocess.run(
                [
                    "djlint",
                    options["path"] or "./templates/**/*",
                    "--extension=html.j2",
                    "--reformat" if options["fix"] else "--check",
                    "--profile=django",
                ],
                check=False,
            )
