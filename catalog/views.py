from django.shortcuts import render
from django.views import generic, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect
from .models import Book, Author, BookInstance, Genre
import datetime
from catalog.forms import RenewBookModelForm
from django.urls import reverse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .forms import BookForm

# -----------------------------------------
# Function-based Views (FBV)
# -----------------------------------------

@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def my_view(request):
    """Example view demonstrating permission checks."""
    ...
    

def index(request):
    """View function for the home page of the site."""
    
    # Count authors (all() is implied)
    num_authors = Author.objects.count()

    # Number of visits to this view, using session
    num_visits = request.session.get('num_visits', 0)
    num_visits += 1
    request.session['num_visits'] = num_visits

    # Main object counts
    num_books = Book.objects.count()
    num_instances = BookInstance.objects.count()

    # Books available
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # Count genres
    num_genres = Genre.objects.count()

    # Count books with a specific word in title
    word = "the"
    num_books_with_word = Book.objects.filter(title__icontains=word).count()

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genres': num_genres,
        'word': word,
        'num_books_with_word': num_books_with_word,
        'num_visits': num_visits,
    }

    return render(request, 'index.html', context=context)


def return_book(request, pk):
    """Mark a BookInstance as returned."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # Only allow POST requests
    if request.method == 'POST':
        book_instance.status = 'a'  # Available
        book_instance.borrower = None
        book_instance.save()
        return redirect('all-borrowed')  # Redirect to staff borrowed books

    # If GET request, show simple confirmation page
    return render(request, 'catalog/book_confirm_return.html', {'book_instance': book_instance})


def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        # Bind POST data to ModelForm
        form = RenewBookModelForm(request.POST, instance=book_instance)

        if form.is_valid():
            # Save the updated due_back field
            form.save()
            return HttpResponseRedirect(reverse('all-borrowed'))
    else:
        # Set initial date 3 weeks from today
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookModelForm(instance=book_instance, initial={'due_back': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)


# -----------------------------------------
# Class-based Views (CBV) - Lists & Details
# -----------------------------------------

class BookListView(generic.ListView):
    """Generic list view for books."""
    model = Book
    paginate_by = 10
    ordering = ['title']


class BookDetailView(generic.DetailView):
    """Detail view for a single book."""
    model = Book


class AuthorListView(generic.ListView):
    """Generic list view for authors."""
    model = Author
    paginate_by = 3


class AuthorDetailView(generic.DetailView):
    """Detail view for a single author."""
    model = Author


# -----------------------------------------
# Custom Views with Permissions & Login
# -----------------------------------------

class MyView(PermissionRequiredMixin, View):
    """Example class-based view requiring a permission."""
    permission_required = 'catalog.can_mark_returned'


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """List books on loan to current logged-in user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects
            .filter(borrower=self.request.user, status__exact='o')
            .order_by('due_back')
        )

class AllBorrowedBooksListView(PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    template_name = 'catalog/all_borrowed_books.html'
    permission_required = 'catalog.can_mark_returned'
    paginate = 10
    
    def get_queryset(self):
        # Return all loaned books (status = 'o')
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/11/2023'}
    permission_required = 'catalog.add_author'

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    fields = '__all__'
    permission_required = 'catalog.change_author'

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
    permission_required = 'catalog.delete_author'

    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except:
            return HttpResponseRedirect(reverse("author-delete", kwargs={"pk": self.object.pk}))
        

class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    permission_required = 'catalog.add_book'
    template_name = 'catalog/book_form.html'


class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    permission_required = 'catalog.change_book'
    template_name = 'catalog/book_form.html'


class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    permission_required = 'catalog.delete_book'
    template_name = 'catalog/book_confirm_delete.html'
    success_url = reverse_lazy('books')

    def form_valid(self, form):
        """Prevent deletion if BookInstances exist."""
        if self.object.bookinstance_set.exists():
            form.add_error(None, "You cannot delete this book. "
                                 "All associated BookInstance records must be deleted first.")
            return super().form_invalid(form)
        return super().form_valid(form)