from django.db.models import Count
from django.db.models.query import QuerySet


def add_comment_count(qs: QuerySet) -> QuerySet:
    return qs.annotate(comment_count=Count('comments')).order_by('-pub_date')
