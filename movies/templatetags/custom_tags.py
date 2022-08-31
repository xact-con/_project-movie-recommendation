from django import template
# import django
# django.setup()
# from movies.models import Actor

register = template.Library()


@register.filter
def get_flat_values_queryset(queryset, args):
    args_list = args.split(',', maxsplit=1)
    field = args_list[0]
    sep = '/'
    if len(args_list) == 2:
        sep = ', '
    return sep.join(queryset.values_list(field, flat=True))


@register.filter
def get_top_role(queryset):
    rate = queryset.roles.all().values_list('rate', flat=True).order_by('rate').reverse().first()
    actor_no = queryset.roles.all().values_list('actor', flat=True).order_by('rate').reverse().first()
    actor = queryset.actors.filter(actor_id=actor_no).values_list('actor_name', flat=True).first()
    actor = str(actor).split(' ')
    actor = actor[-1]

    return f"{actor}-{rate}"


@register.filter
def order_by(queryset, args):
    args = [x.strip() for x in args.split(',')]
    return queryset.order_by(*args)
