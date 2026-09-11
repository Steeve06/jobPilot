from django.core.management.base import BaseCommand, CommandError

from accounts.models import Profile
from resumes.models import Resume
from scoring.service import score_unscored_postings


class Command(BaseCommand):
    help = 'Score unscored postings for a given profile against its resume'

    def add_arguments(self, parser):
        parser.add_argument('profile_id', type=int)

    def handle(self, *args, **options):
        try:
            profile = Profile.objects.get(id=options['profile_id'])
        except Profile.DoesNotExist:
            raise CommandError(f'Profile {options["profile_id"]} does not exist')

        try:
            resume = profile.resume
        except Resume.DoesNotExist:
            raise CommandError(f'Profile {profile} has no resume yet — build one first (Sprint 7).')

        self.stdout.write(f'Scoring postings for {profile}...')

        def on_progress(index, total, posting, error):
            marker = 'FAILED' if error else 'OK'
            self.stdout.write(f'  [{index}/{total}] {posting.company} — {posting.title[:50]} ({marker})')

        result = score_unscored_postings(profile, resume, on_progress=on_progress)

        self.stdout.write(self.style.SUCCESS(
            f"Scored {result['scored']} of {result['eligible']} eligible postings "
            f"({result['filtered_out']} filtered out by hard filters)."
        ))
        if result.get('skipped_cap'):
            self.stdout.write(self.style.WARNING('Daily scoring cap reached — remaining postings left unscored.'))