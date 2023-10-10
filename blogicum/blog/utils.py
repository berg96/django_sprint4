from django.db.models import Count


def add_comment_count(qs):
    return qs.annotate(comment_count=Count('comments')).order_by('-pub_date')
