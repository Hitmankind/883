from django.core.management.base import BaseCommand
from students.models import Course


SUBJECTS = [
    ("CSCI944", "Perception and Planning"),
    ("CSIT884", "Web Development"),
    ("CSCI946", "Big Data Analytics"),
    ("CSIT985", "Strategic Network Design"),
    ("CSIT998", "Professional Capstone Project"),
    ("CSIT999", "Project"),
    ("CSIT881", "Programming and Data Structures"),
    ("CSIT882", "Data Management Systems"),
    ("CSIT883", "System Analysis and Project Management"),
    ("CSCI971", "Modern Cryptography"),
    ("ENGG982", "Professional Communications and Engineering Workplace Practice 2"),
    ("ECTE962", "Telecommunications System Modelling"),
    ("ECTE992", "The Future Internet: Architectures and Communication"),
    ("ECTE908", "Image Processing for Autonomous Systems"),
    ("ECTE940", "Advanced Project"),
    ("ECTE955", "Advanced Laboratory"),
    ("ECT8363", "Communication Systems"),
    ("ENGG955", "Engineering Research Methods"),
    ("ENGG950", "Innovation and Design"),
]


class Command(BaseCommand):
    help = "Load provided subjects into Course model (id, name in English)."

    def add_arguments(self, parser):
        parser.add_argument("--credits", type=int, default=3, help="Default credits for inserted courses")

    def handle(self, *args, **options):
        credits = options["credits"]
        created_count = 0
        for code, name in SUBJECTS:
            code = code.strip().upper()
            name = name.strip()
            course, created = Course.objects.get_or_create(
                course_id=code,
                defaults={"course_name": name, "credits": credits},
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created course: {code} - {name} ({credits} credits)"))
            else:
                # Update name/credits if changed
                updated = False
                if course.course_name != name:
                    course.course_name = name
                    updated = True
                if course.credits != credits:
                    course.credits = credits
                    updated = True
                if updated:
                    course.save()
                    self.stdout.write(self.style.WARNING(f"Updated course: {code} - {name} ({credits} credits)"))
                else:
                    self.stdout.write(f"Exists: {code} - {name}")

        self.stdout.write(self.style.SUCCESS(f"Done. Created {created_count} new courses."))