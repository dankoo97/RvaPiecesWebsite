import subprocess

from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Lints the project"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Fix the linting errors",
        )

        parser.add_argument(
            "--path",
            type=str,
            help="Path to the file or directory to lint, otherwise lints the entire project",
        )

        parser.add_argument(
            "--html",
            action="store_true",
            help="Lint html files",
        )

        parser.add_argument(
            "--python",
            action="store_true",
            help="Lint python files",
        )

    def handle(self, *args, **options):
        if options["python"]:
            args = [
                "ruff",
                "check",
                options["path"] or ".",
            ]

            if options["fix"]:
                args.append("--fix")

            subprocess.run(
                args,
                check=False,
            )

        if options["html"]:
            subprocess.run(
                [
                    "djlint",
                    options["path"] or "./templates/**/*",
                    "--extension=html.j2",
                    "--lint",
                    "--profile=django",
                ],
                check=False,
            )
