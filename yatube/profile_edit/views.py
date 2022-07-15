
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from .forms import ProfileEditForm

from .models import ProfileEdit

User = get_user_model()

@login_required
def profile_edit(request, username):
    author = get_object_or_404(User, username=username)
    form = ProfileEditForm(request.POST or None, files=request.FILES or None)
    if form.is_valid() and request.method == "POST":
        ProfileEdit = form.save(commit=False)
        ProfileEdit.author = request.user
        ProfileEdit.save()
        return redirect('posts:profile', username=username)
    
    context = {
        'author': author,
        'form':form,
    }
    return render(request, 'profile_edit/profile_edit.html', context)
