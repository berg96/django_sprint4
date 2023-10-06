from datetime import datetime
from django.db.models import Count


def published(qs):
    return qs.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=datetime.now(),
    )


def add_comment_count(qs):
    return qs.annotate(comment_count=Count('comment')).order_by('-pub_date')
