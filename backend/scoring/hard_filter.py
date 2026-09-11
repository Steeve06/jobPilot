from django.db.models import Q


def apply_hard_filters(postings_queryset, active_search_profiles):
   
    if not active_search_profiles:
        return postings_queryset

    combined_query = Q(pk__in=[])  # start empty, OR in each search profile's match
    for sp in active_search_profiles:
        sp_query = Q()
        if sp.title_keywords:
            keyword_query = Q()
            for kw in sp.title_keywords:
                keyword_query |= Q(title__icontains=kw)
            sp_query &= keyword_query

        if sp.excluded_keywords:
            for kw in sp.excluded_keywords:
                sp_query &= ~Q(title__icontains=kw)

        if sp.remote_ok is False:
            pass  # intentionally not filtering out remote postings on this basis alone

        combined_query |= sp_query

    return postings_queryset.filter(combined_query)