from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError

from lists.models import Item, List


ERROR_EMPTY_ITEM = "You can't have an empty list item"


def home_page(request):
    return render(request, 'home.html')


def view_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    error = None
    if request.method == 'POST':
        item = Item(text=request.POST['item_text'], list=list_)
        try:
            item.full_clean()
            item.save()
            return redirect(f'/lists/{list_.id}/', {'list': list_})
        except ValidationError:
            error = ERROR_EMPTY_ITEM
    return render(request, 'list.html', {'list': list_, 'error': error})


def new_list(request):
    list_ = List.objects.create()
    item = Item(text=request.POST['item_text'], list=list_)
    try:
        item.full_clean()
        item.save()
    except ValidationError:
        list_.delete()
        return render(request, 'home.html', {'error': ERROR_EMPTY_ITEM})
    return redirect(f'/lists/{list_.id}/')


