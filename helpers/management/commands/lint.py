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
            help="Path to the file or directory to lint",
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
        ruff = {}
        djhtml = {}

        if options["path"]:
            ruff["path"] = options["path"]
            djhtml["path"] = options["path"]
        else:
            ruff["path"] = "."
            djhtml["path"] = "."

        if options["fix"]:
            ruff["fix"] = "format"
            djhtml["fix"] = "--reformat"
        else:
            ruff["fix"] = "check"
            djhtml["fix"] = "--lint"

        if options["python"]:
            subprocess.run(["ruff", ruff["fix"], ruff["path"]], check=False)

        if options["html"]:
            subprocess.run(
                ["djlint", "./templates/**/*", "--extension=html.j2", djhtml["fix"], "--profile=django"],
                check=False,
            )
