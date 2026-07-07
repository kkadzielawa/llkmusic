from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from blog.models import Post


class Command(BaseCommand):
    help = 'Seeds two sample blog posts about blues and jazz'

    def handle(self, *args, **options):
        # Use the first superuser as the author, or create one
        author = User.objects.filter(is_superuser=True).first()
        if not author:
            author = User.objects.create_superuser(
                'username123', 'username123@llkmusic.com', 'password123'
            )
            self.stdout.write(self.style.WARNING(
                'Created superuser "username123"'
            ))

        post1, created1 = Post.objects.get_or_create(
            slug='12-bar-blues-beginners-guide',
            defaults={
                'title': 'The 12-Bar Blues: A Beginner\'s Guide to the Foundation of Blues Guitar',
                'author': author,
                'body': (
                    'The 12-bar blues is the backbone of blues music and one of the '
                    'first progressions every guitarist should learn. Built on just '
                    'three chords — the I, IV, and V — this deceptively simple '
                    'structure has powered countless classics from Robert Johnson to '
                    'B.B. King to Stevie Ray Vaughan.\n\n'
                    'In its most basic form, the 12-bar blues in the key of A uses '
                    'A7 (I), D7 (IV), and E7 (V). The progression follows a '
                    'predictable pattern over 12 measures:\n\n'
                    'Bars 1–4: A7 | A7 | A7 | A7\n'
                    'Bars 5–6: D7 | D7\n'
                    'Bars 7–8: A7 | A7\n'
                    'Bars 9–10: E7 | D7\n'
                    'Bars 11–12: A7 | E7 (turnaround)\n\n'
                    'What makes this form so powerful is how much room it leaves '
                    'for expression. Once you have the changes memorized, start '
                    'experimenting with shuffle rhythms, dominant 7th voicings up '
                    'the neck, and call-and-response phrasing between your rhythm '
                    'and lead playing. The blues is as deep as you want to take it.'
                ),
                'published': True,
            }
        )

        post2, created2 = Post.objects.get_or_create(
            slug='jazz-chord-voicings-for-blues-guitarists',
            defaults={
                'title': 'Jazz Chord Voicings Every Blues Guitarist Should Know',
                'author': author,
                'body': (
                    'If you come from a blues background, jazz harmony can feel '
                    'overwhelming — but the truth is, you already know more than '
                    'you think. Many jazz voicings are natural extensions of the '
                    'dominant 7th chords you already use in blues.\n\n'
                    'Start with the "Freddie Green" style: rootless voicings on '
                    'the middle four strings. For a Cmaj7 chord, try playing '
                    'x-3-5-4-5-x. For Dm7, use x-5-7-5-6-x. These compact shapes '
                    'are easy to move chromatically and sound sophisticated over '
                    'a ii-V-I progression.\n\n'
                    'Next, explore the minor 7th and diminished passing chords. '
                    'In a jazz-blues in Bb, try: Bb7 | Eb7 | Bb7 | Bdim7 | '
                    'Cm7 | F7 | Bb7 | G7 | Cm7 | F7 | Bb7 | F7. Notice how '
                    'the diminished chord on beat 4 of bar 3 creates a smooth '
                    'chromatic walk-up into the ii chord.\n\n'
                    'The key takeaway: jazz and blues are not separate languages. '
                    'They share the same roots. Adding a few jazz voicings to your '
                    'blues vocabulary will make your comping richer, your solos '
                    'more melodic, and your ears sharper.'
                ),
                'published': True,
            }
        )

        for post, created in [(post1, created1), (post2, created2)]:
            status = 'Created' if created else 'Already exists'
            self.stdout.write(self.style.SUCCESS(
                f'{status}: "{post.title}"'
            ))
