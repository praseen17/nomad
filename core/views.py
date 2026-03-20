from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db import transaction
from restaurant.models import Restaurant, SuperAdmin, AuditLog
from workers.models import Worker
import uuid


def landing(request):
    """Main landing page."""
    return render(request, 'core/landing.html')


def owner_login(request):
    """Restaurant owner login."""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user:
                # Check if owner
                if hasattr(user, 'restaurant'):
                    if user.restaurant.status == Restaurant.STATUS_ACTIVE:
                        login(request, user)
                        request.session['user_role'] = 'owner'
                        request.session['restaurant_id'] = user.restaurant.id
                        return redirect('owner_dashboard')
                    elif user.restaurant.status == Restaurant.STATUS_PENDING:
                        messages.warning(request, 'Your restaurant is still pending approval.')
                        return redirect('owner_login')
                    elif user.restaurant.status == Restaurant.STATUS_SUSPENDED:
                        messages.error(request, 'Your account has been suspended. Contact support.')
                        return redirect('owner_login')
                    else:
                        messages.error(request, 'Your application was rejected. Contact support.')
                        return redirect('owner_login')
                else:
                    messages.error(request, 'No restaurant associated with this account.')
                    return redirect('owner_login')
            else:
                messages.error(request, 'Invalid email or password.')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'core/owner_login.html')


def staff_login(request):
    """Worker/staff login using worker ID + password."""
    if request.method == 'POST':
        worker_id = request.POST.get('worker_id', '').strip().upper()
        password = request.POST.get('password', '')

        try:
            worker = Worker.objects.select_related('user', 'restaurant').get(worker_id=worker_id, is_active=True)
            user = authenticate(request, username=worker.user.username, password=password)
            if user:
                login(request, user)
                request.session['user_role'] = worker.role
                request.session['worker_id'] = worker.id
                request.session['restaurant_id'] = worker.restaurant.id
                return redirect(worker.get_dashboard_url())
            else:
                messages.error(request, 'Invalid Staff ID or password.')
        except Worker.DoesNotExist:
            messages.error(request, 'Staff ID not found or account inactive.')

    return render(request, 'core/staff_login.html')


def superadmin_login(request):
    """Super admin login — hidden route."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        try:
            user_obj = User.objects.get(email=email)
            if not hasattr(user_obj, 'super_admin_profile'):
                messages.error(request, 'Access denied.')
                return redirect('superadmin_login')

            user = authenticate(request, username=user_obj.username, password=password)
            if user:
                login(request, user)
                request.session['user_role'] = 'superadmin'
                return redirect('superadmin_dashboard')
            else:
                messages.error(request, 'Invalid credentials.')
        except User.DoesNotExist:
            messages.error(request, 'Invalid credentials.')

    return render(request, 'core/superadmin_login.html')


def owner_signup(request):
    """Multi-step restaurant owner signup."""
    step = int(request.session.get('signup_step', 1))

    if request.method == 'POST':
        action = request.POST.get('action', 'next')

        if action == 'prev':
            request.session['signup_step'] = max(1, step - 1)
            return redirect('owner_signup')

        if step == 1:
            # Save step 1 data to session
            data = {
                'full_name': request.POST.get('full_name', '').strip(),
                'email': request.POST.get('email', '').strip(),
                'password': request.POST.get('password', ''),
                'confirm_password': request.POST.get('confirm_password', ''),
                'phone': request.POST.get('phone', '').strip(),
            }

            # Validate
            errors = []
            if not data['full_name']:
                errors.append('Full name is required.')
            if not data['email']:
                errors.append('Email is required.')
            elif User.objects.filter(email=data['email']).exists():
                errors.append('An account with this email already exists.')
            if len(data['password']) < 8:
                errors.append('Password must be at least 8 characters.')
            if data['password'] != data['confirm_password']:
                errors.append('Passwords do not match.')

            if errors:
                for e in errors:
                    messages.error(request, e)
            else:
                request.session['signup_data'] = data
                request.session['signup_step'] = 2
                return redirect('owner_signup')

        elif step == 2:
            data = request.session.get('signup_data', {})
            data.update({
                'restaurant_name': request.POST.get('restaurant_name', '').strip(),
                'restaurant_type': request.POST.get('restaurant_type', ''),
                'address_street': request.POST.get('address_street', '').strip(),
                'address_city': request.POST.get('address_city', '').strip(),
                'address_state': request.POST.get('address_state', '').strip(),
                'address_pincode': request.POST.get('address_pincode', '').strip(),
                'gst_number': request.POST.get('gst_number', '').strip(),
                'fssai_number': request.POST.get('fssai_number', '').strip(),
            })

            errors = []
            if not data.get('restaurant_name'):
                errors.append('Restaurant name is required.')
            if not data.get('restaurant_type'):
                errors.append('Restaurant type is required.')
            if not data.get('address_city'):
                errors.append('City is required.')

            if errors:
                for e in errors:
                    messages.error(request, e)
            else:
                request.session['signup_data'] = data
                request.session['signup_step'] = 3
                return redirect('owner_signup')

        elif step == 3:
            if not request.POST.get('terms_agreed'):
                messages.error(request, 'You must agree to the Terms & Conditions.')
                return render(request, 'core/owner_signup.html', {'step': step})

            data = request.session.get('signup_data', {})

            try:
                with transaction.atomic():
                    # Create user
                    username = f"owner_{uuid.uuid4().hex[:8]}"
                    user = User.objects.create_user(
                        username=username,
                        email=data['email'],
                        password=data['password'],
                        first_name=data['full_name'].split()[0],
                        last_name=' '.join(data['full_name'].split()[1:]),
                    )

                    # Create slug
                    base_slug = slugify(data['restaurant_name'])
                    slug = base_slug
                    counter = 1
                    while Restaurant.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1

                    # Create restaurant
                    restaurant = Restaurant.objects.create(
                        owner=user,
                        name=data['restaurant_name'],
                        slug=slug,
                        restaurant_type=data['restaurant_type'],
                        address_street=data['address_street'],
                        address_city=data['address_city'],
                        address_state=data['address_state'],
                        address_pincode=data['address_pincode'],
                        phone=data.get('phone', ''),
                        gst_number=data.get('gst_number', ''),
                        fssai_number=data.get('fssai_number', ''),
                        status=Restaurant.STATUS_PENDING,
                    )

                    # Handle file uploads
                    if 'logo' in request.FILES:
                        restaurant.logo_local = request.FILES['logo']
                        restaurant.save()
                    if 'banner' in request.FILES:
                        restaurant.banner_local = request.FILES['banner']
                        restaurant.save()

                    # Clear session
                    del request.session['signup_data']
                    del request.session['signup_step']

                    return redirect('signup_success')

            except Exception as e:
                messages.error(request, f'Registration failed. Please try again.')
                print(f"Signup error: {e}")

    context = {
        'step': step,
        'signup_data': request.session.get('signup_data', {}),
        'restaurant_types': Restaurant.TYPE_CHOICES,
    }
    return render(request, 'core/owner_signup.html', context)


def signup_success(request):
    return render(request, 'core/signup_success.html')


def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('landing')


@login_required
def dashboard_redirect(request):
    """Redirect user to their appropriate dashboard."""
    user = request.user
    if hasattr(user, 'super_admin_profile'):
        return redirect('superadmin_dashboard')
    elif hasattr(user, 'restaurant'):
        return redirect('owner_dashboard')
    elif hasattr(user, 'worker_profile'):
        return redirect(user.worker_profile.get_dashboard_url())
    return redirect('landing')


def customer_menu(request, slug):
    """Public customer-facing digital menu."""
    from restaurant.models import Restaurant
    from menu.models import Dish, MenuCategory

    try:
        restaurant = Restaurant.objects.get(slug=slug, status=Restaurant.STATUS_ACTIVE)
    except Restaurant.DoesNotExist:
        return render(request, 'core/404.html', status=404)

    table_number = request.GET.get('table', None)
    categories = MenuCategory.objects.filter(restaurant=restaurant, is_active=True)
    dishes = Dish.objects.filter(restaurant=restaurant).select_related('category')

    # Group dishes by category
    menu_data = []
    for cat in categories:
        cat_dishes = dishes.filter(category=cat)
        if cat_dishes.exists():
            menu_data.append({
                'category': cat,
                'dishes': cat_dishes,
            })

    # Uncategorized dishes
    uncategorized = dishes.filter(category__isnull=True)
    if uncategorized.exists():
        menu_data.append({
            'category': None,
            'dishes': uncategorized,
        })

    context = {
        'restaurant': restaurant,
        'menu_data': menu_data,
        'table_number': table_number,
        'total_dishes': dishes.filter(is_available=True).count(),
    }
    return render(request, 'core/customer_menu.html', context)


def review_page(request, token):
    """One-time customer review page."""
    from billing.models import Invoice
    from reviews.models import Review

    try:
        invoice = Invoice.objects.select_related('waiter', 'restaurant').get(review_token=token)
    except Invoice.DoesNotExist:
        return render(request, 'core/404.html', status=404)

    # Check if already reviewed
    if hasattr(invoice, 'review') and invoice.review.is_used:
        return render(request, 'core/review_already_submitted.html')

    if request.method == 'POST':
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '').strip()

        if 1 <= rating <= 5:
            review, created = Review.objects.get_or_create(
                invoice=invoice,
                defaults={'waiter': invoice.waiter, 'token': token, 'rating': rating, 'comment': comment}
            )
            if not created:
                review.rating = rating
                review.comment = comment
            review.is_used = True
            review.save()
            return redirect('review_thanks')
        else:
            messages.error(request, 'Please select a rating.')

    context = {'invoice': invoice}
    return render(request, 'core/review_page.html', context)


def review_thanks(request):
    return render(request, 'core/review_thanks.html')


def error_403(request, exception=None):
    return render(request, 'core/403.html', status=403)


def error_404(request, exception=None):
    return render(request, 'core/404.html', status=404)


def error_500(request):
    return render(request, 'core/500.html', status=500)
