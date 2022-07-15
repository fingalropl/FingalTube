from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from profile_edit.models import ProfileEdit
from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post
from .utils import paginator

User = get_user_model()

def index(request):
    posts = Post.objects.select_related('group', 'author')
    page_obj = paginator(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    posts_count = posts.count()
    page_obj = paginator(request, posts)
    follower_count = Follow.objects.filter(author=author).count
    profile = get_object_or_404(ProfileEdit, author=author)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    else:
        following = False

    context = {
        'profile': profile,
        'follower_count': follower_count,
        'author': author,
        'posts_count': posts_count,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    posts_count = author.posts.count()
    comments = Comment.objects.filter(post=post)
    form = CommentForm(request.POST or None)
    context = {
        'author': author,
        'post': post,
        'posts_count': posts_count,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid() and request.method == "POST":
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author)

    context = {
        'form': form,
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id, )
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(request.POST or None, instance=post,
                    files=request.FILES or None)
    if form.is_valid() and request.method == "POST":
        form.save()
        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'form': form,
        'is_edit': True
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post.objects.select_related('author', 'group',),
                             pk=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(request, posts)
    context = {
        'page_obj': page_obj,

    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    follow_queryset = Follow.objects.filter(user=user, author=author)
    if user != author and not follow_queryset.exists():
        Follow.objects.create(user=user, author=author)
    return redirect(reverse('posts:profile', args=(username,)))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow_queryset = Follow.objects.filter(user=request.user, author=author)
    if follow_queryset.exists():
        follow_queryset.delete()
    return redirect('posts:profile', username=author.username)
