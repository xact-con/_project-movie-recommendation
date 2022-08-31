from django.shortcuts import render


def events_main(request):
    context = {
        'events': 'events',
    }

    return render(request, "events/main.html", context)
