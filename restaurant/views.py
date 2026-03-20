from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import date, timedelta
from restaurant.models import Restaurant, AuditLog, Announcement
from workers.models import Worker
from menu.models import Dish, MenuCategory
from tables.models import Table
from orders.models import Order, OrderItem
from billing.models import Invoice
from reviews.models import Review
import json


def require_owner(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('owner_login')
        if not hasattr(request.user, 'restaurant') or request.user.restaurant.status != Restaurant.STATUS_ACTIVE:
            return redirect('owner_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def require_worker_role(*roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('staff_login')
            if not hasattr(request.user, 'worker_profile'):
                return redirect('staff_login')
            if request.user.worker_profile.role not in roles:
                return render(request, 'core/403.html', status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_superadmin(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('superadmin_login')
        if not hasattr(request.user, 'super_admin_profile'):
            return render(request, 'core/403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


# ===== OWNER DASHBOARD =====

@require_owner
def owner_dashboard(request):
    restaurant = request.user.restaurant
    today = date.today()

    # Today's stats
    today_invoices = Invoice.objects.filter(restaurant=restaurant, created_at__date=today)
    today_revenue = today_invoices.aggregate(total=Sum('grand_total'))['total'] or 0
    today_customers = today_invoices.aggregate(total=Sum('customer_count'))['total'] or 0

    active_tables = Table.objects.filter(restaurant=restaurant, status=Table.STATUS_OCCUPIED).count()
    active_workers = Worker.objects.filter(restaurant=restaurant, is_active=True).count()

    tables = Table.objects.filter(restaurant=restaurant)
    all_tables_count = tables.count()

    # Revenue last 7 days
    revenue_data = []
    labels = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        rev = Invoice.objects.filter(restaurant=restaurant, created_at__date=day).aggregate(total=Sum('grand_total'))['total'] or 0
        revenue_data.append(float(rev))
        labels.append(day.strftime('%d %b'))

    # Top dishes
    top_dishes = OrderItem.objects.filter(
        order__restaurant=restaurant,
        order__created_at__date=today
    ).values('dish__name').annotate(count=Sum('quantity')).order_by('-count')[:5]

    # Worker leaderboard
    waiter_perf = Invoice.objects.filter(
        restaurant=restaurant,
        created_at__date=today,
        waiter__isnull=False
    ).values('waiter__full_name', 'waiter__worker_id').annotate(
        bills=Count('id'),
        revenue=Sum('grand_total')
    ).order_by('-bills')[:5]

    context = {
        'restaurant': restaurant,
        'today_revenue': today_revenue,
        'today_customers': today_customers,
        'active_tables': active_tables,
        'active_workers': active_workers,
        'tables': tables,
        'all_tables_count': all_tables_count,
        'revenue_data': json.dumps(revenue_data),
        'revenue_labels': json.dumps(labels),
        'top_dishes': list(top_dishes),
        'waiter_perf': list(waiter_perf),
        'recent_invoices': today_invoices.select_related('table', 'waiter')[:5],
        'user_role': 'owner',
    }
    return render(request, 'dashboards/owner_dashboard.html', context)


@require_owner
def owner_workers(request):
    restaurant = request.user.restaurant
    workers = Worker.objects.filter(restaurant=restaurant).select_related('user')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            full_name = request.POST.get('full_name', '').strip()
            role = request.POST.get('role', '')
            phone = request.POST.get('phone', '').strip()
            password = request.POST.get('password', '')

            if full_name and role and password:
                username = f"worker_{User.objects.count() + 1:06d}"
                user = User.objects.create_user(username=username, password=password)
                worker = Worker.objects.create(
                    restaurant=restaurant, user=user, full_name=full_name,
                    role=role, phone=phone
                )
                AuditLog.objects.create(
                    actor=request.user,
                    actor_name=request.user.get_full_name(),
                    action='Worker Added',
                    description=f'Added {worker.worker_id} — {full_name} as {worker.get_role_display()}',
                    restaurant=restaurant
                )
                messages.success(request, f'Worker {worker.worker_id} created successfully!')
                return redirect('owner_workers')
            else:
                messages.error(request, 'Please fill all required fields.')

        elif action == 'delete':
            worker_id = request.POST.get('worker_id')
            try:
                worker = Worker.objects.get(id=worker_id, restaurant=restaurant)
                worker.is_active = False
                worker.save()
                messages.success(request, f'Worker {worker.worker_id} deactivated.')
            except Worker.DoesNotExist:
                messages.error(request, 'Worker not found.')
            return redirect('owner_workers')

    context = {
        'restaurant': restaurant,
        'workers': workers,
        'role_choices': Worker.ROLE_CHOICES,
        'user_role': 'owner',
    }
    return render(request, 'dashboards/owner_workers.html', context)


@require_owner
def owner_menu(request):
    restaurant = request.user.restaurant
    categories = MenuCategory.objects.filter(restaurant=restaurant)
    dishes = Dish.objects.filter(restaurant=restaurant).select_related('category')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_dish':
            name = request.POST.get('name', '').strip()
            price = request.POST.get('price', 0)
            category_id = request.POST.get('category_id') or None
            description = request.POST.get('description', '').strip()
            food_type = request.POST.get('food_type', 'veg')
            image_url = request.POST.get('image_url', '').strip()

            if name and price:
                category = None
                if category_id:
                    try:
                        category = MenuCategory.objects.get(id=category_id, restaurant=restaurant)
                    except MenuCategory.DoesNotExist:
                        pass
                dish = Dish.objects.create(
                    restaurant=restaurant,
                    category=category,
                    name=name,
                    price=price,
                    description=description,
                    food_type=food_type,
                    image_url=image_url or None,
                )
                if 'image' in request.FILES:
                    dish.image_local = request.FILES['image']
                    dish.save()
                messages.success(request, f'Dish "{name}" added successfully!')
            else:
                messages.error(request, 'Name and price are required.')
            return redirect('owner_menu')

        elif action == 'toggle_availability':
            dish_id = request.POST.get('dish_id')
            try:
                dish = Dish.objects.get(id=dish_id, restaurant=restaurant)
                dish.is_available = not dish.is_available
                dish.save()
            except Dish.DoesNotExist:
                pass
            return redirect('owner_menu')

        elif action == 'add_category':
            cat_name = request.POST.get('cat_name', '').strip()
            if cat_name:
                MenuCategory.objects.create(restaurant=restaurant, name=cat_name)
                messages.success(request, f'Category "{cat_name}" added.')
            return redirect('owner_menu')

        elif action == 'delete_dish':
            dish_id = request.POST.get('dish_id')
            try:
                dish = Dish.objects.get(id=dish_id, restaurant=restaurant)
                dish.delete()
                messages.success(request, 'Dish deleted.')
            except Dish.DoesNotExist:
                pass
            return redirect('owner_menu')

    context = {
        'restaurant': restaurant,
        'categories': categories,
        'dishes': dishes,
        'food_type_choices': Dish.FOOD_TYPE_CHOICES,
        'user_role': 'owner',
    }
    return render(request, 'dashboards/owner_menu.html', context)


@require_owner
def owner_tables(request):
    restaurant = request.user.restaurant
    tables = Table.objects.filter(restaurant=restaurant)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            number = int(request.POST.get('number', 0))
            capacity = int(request.POST.get('capacity', 4))
            zone = request.POST.get('zone', '').strip()
            if number > 0:
                if Table.objects.filter(restaurant=restaurant, number=number).exists():
                    messages.error(request, f'Table {number} already exists.')
                else:
                    Table.objects.create(restaurant=restaurant, number=number, capacity=capacity, zone=zone)
                    messages.success(request, f'Table {number} added.')
            return redirect('owner_tables')
        elif action == 'delete':
            table_id = request.POST.get('table_id')
            Table.objects.filter(id=table_id, restaurant=restaurant).delete()
            messages.success(request, 'Table removed.')
            return redirect('owner_tables')

    context = {
        'restaurant': restaurant,
        'tables': tables,
        'user_role': 'owner',
    }
    return render(request, 'dashboards/owner_tables.html', context)


@require_owner
def owner_invoices(request):
    restaurant = request.user.restaurant
    invoices = Invoice.objects.filter(restaurant=restaurant).select_related('table', 'waiter', 'receptionist')

    date_filter = request.GET.get('date')
    if date_filter:
        invoices = invoices.filter(created_at__date=date_filter)

    context = {
        'restaurant': restaurant,
        'invoices': invoices[:50],
        'user_role': 'owner',
    }
    return render(request, 'dashboards/owner_invoices.html', context)


@require_owner
def owner_analytics(request):
    restaurant = request.user.restaurant
    today = date.today()

    # Weekly revenue
    weekly_rev = []
    weekly_labels = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        rev = Invoice.objects.filter(restaurant=restaurant, created_at__date=day).aggregate(total=Sum('grand_total'))['total'] or 0
        weekly_rev.append(float(rev))
        weekly_labels.append(day.strftime('%d %b'))

    # Monthly revenue
    monthly_rev = []
    monthly_labels = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        rev = Invoice.objects.filter(restaurant=restaurant, created_at__date=day).aggregate(total=Sum('grand_total'))['total'] or 0
        monthly_rev.append(float(rev))
        monthly_labels.append(day.strftime('%d'))

    context = {
        'restaurant': restaurant,
        'weekly_rev': json.dumps(weekly_rev),
        'weekly_labels': json.dumps(weekly_labels),
        'monthly_rev': json.dumps(monthly_rev),
        'monthly_labels': json.dumps(monthly_labels),
        'user_role': 'owner',
    }
    return render(request, 'dashboards/owner_analytics.html', context)


@require_owner
def owner_reviews(request):
    restaurant = request.user.restaurant
    reviews = Review.objects.filter(invoice__restaurant=restaurant).select_related('waiter', 'invoice')
    context = {
        'restaurant': restaurant,
        'reviews': reviews,
        'user_role': 'owner',
    }
    return render(request, 'dashboards/owner_reviews.html', context)


@require_owner
def owner_qr_menu(request):
    restaurant = request.user.restaurant
    if request.method == 'POST' and request.POST.get('action') == 'regenerate':
        # Generate QR code
        try:
            import qrcode
            import io
            from django.core.files.base import ContentFile

            menu_url = f"/menu/{restaurant.slug}/"
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(f"http://localhost:8000{menu_url}")
            qr.make(fit=True)
            img = qr.make_image(fill_color="#0E0C0A", back_color="#F5F0E8")
            img_io = io.BytesIO()
            img.save(img_io, format='PNG')
            img_io.seek(0)
            restaurant.qr_code_local.save(
                f'qr_{restaurant.slug}.png',
                ContentFile(img_io.read()),
                save=True
            )
            messages.success(request, 'QR code regenerated!')
        except Exception as e:
            messages.error(request, f'QR generation failed: {e}')
        return redirect('owner_qr_menu')

    context = {
        'restaurant': restaurant,
        'menu_url': f"/menu/{restaurant.slug}/",
        'user_role': 'owner',
    }
    return render(request, 'dashboards/owner_qr_menu.html', context)


@require_owner
def owner_settings(request):
    restaurant = request.user.restaurant
    if request.method == 'POST':
        restaurant.name = request.POST.get('name', restaurant.name)
        restaurant.phone = request.POST.get('phone', restaurant.phone)
        restaurant.gst_number = request.POST.get('gst_number', restaurant.gst_number)
        restaurant.fssai_number = request.POST.get('fssai_number', restaurant.fssai_number)
        if 'logo' in request.FILES:
            restaurant.logo_local = request.FILES['logo']
        if 'banner' in request.FILES:
            restaurant.banner_local = request.FILES['banner']
        restaurant.save()
        messages.success(request, 'Settings updated successfully!')
        return redirect('owner_settings')

    context = {
        'restaurant': restaurant,
        'user_role': 'owner',
    }
    return render(request, 'dashboards/owner_settings.html', context)


# ===== MANAGER DASHBOARD =====

@require_worker_role('manager', 'asst_manager')
def manager_dashboard(request):
    worker = request.user.worker_profile
    restaurant = worker.restaurant
    today = date.today()

    active_tables = Table.objects.filter(restaurant=restaurant, status=Table.STATUS_OCCUPIED).count()
    tables = Table.objects.filter(restaurant=restaurant)

    context = {
        'restaurant': restaurant,
        'worker': worker,
        'tables': tables,
        'active_tables': active_tables,
        'user_role': worker.role,
    }
    return render(request, 'dashboards/manager_dashboard.html', context)


@require_worker_role('manager', 'asst_manager')
def manager_workers(request):
    worker = request.user.worker_profile
    restaurant = worker.restaurant
    workers = Worker.objects.filter(restaurant=restaurant)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            full_name = request.POST.get('full_name', '').strip()
            role = request.POST.get('role', '')
            password = request.POST.get('password', '')
            # Managers cannot add other managers
            if role in ['manager'] and worker.role != 'manager':
                messages.error(request, 'You cannot add Managers.')
            elif full_name and role and password:
                username = f"worker_{User.objects.count() + 1:06d}"
                user = User.objects.create_user(username=username, password=password)
                new_worker = Worker.objects.create(
                    restaurant=restaurant, user=user,
                    full_name=full_name, role=role
                )
                messages.success(request, f'Worker {new_worker.worker_id} created!')
            return redirect('manager_workers')

    context = {
        'restaurant': restaurant,
        'worker': worker,
        'workers': workers,
        'role_choices': [(r, d) for r, d in Worker.ROLE_CHOICES if r not in ['manager', 'asst_manager']],
        'user_role': worker.role,
    }
    return render(request, 'dashboards/manager_workers.html', context)


@require_worker_role('manager', 'asst_manager')
def manager_menu(request):
    worker = request.user.worker_profile
    restaurant = worker.restaurant
    dishes = Dish.objects.filter(restaurant=restaurant).select_related('category')
    categories = MenuCategory.objects.filter(restaurant=restaurant)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_category':
            cat_name = request.POST.get('cat_name', '').strip()
            if cat_name:
                MenuCategory.objects.create(restaurant=restaurant, name=cat_name)
                messages.success(request, f'Category "{cat_name}" added.')
            return redirect('manager_menu')
            
        elif action == 'add_dish':
            name = request.POST.get('name', '').strip()
            price = request.POST.get('price', 0)
            category_id = request.POST.get('category_id') or None
            description = request.POST.get('description', '').strip()
            food_type = request.POST.get('food_type', 'veg')
            image_url = request.POST.get('image_url', '').strip()

            if name and price:
                category = None
                if category_id:
                    try:
                        category = MenuCategory.objects.get(id=category_id, restaurant=restaurant)
                    except MenuCategory.DoesNotExist:
                        pass
                dish = Dish.objects.create(
                    restaurant=restaurant,
                    category=category,
                    name=name,
                    price=price,
                    description=description,
                    food_type=food_type,
                    image_url=image_url or None,
                )
                if 'image' in request.FILES:
                    dish.image_local = request.FILES['image']
                    dish.save()
                messages.success(request, f'Dish "{name}" added successfully!')
            else:
                messages.error(request, 'Name and price are required.')
            return redirect('manager_menu')
            
        elif action == 'delete_dish':
            dish_id = request.POST.get('dish_id')
            try:
                dish = Dish.objects.get(id=dish_id, restaurant=restaurant)
                dish.delete()
                messages.success(request, 'Dish deleted.')
            except Dish.DoesNotExist:
                pass
            return redirect('manager_menu')
            
        elif action == 'delete_category':
            category_id = request.POST.get('category_id')
            try:
                category = MenuCategory.objects.get(id=category_id, restaurant=restaurant)
                category.delete()
                messages.success(request, 'Category deleted.')
            except MenuCategory.DoesNotExist:
                pass
            return redirect('manager_menu')
            
        elif action == 'toggle_availability':
            dish_id = request.POST.get('dish_id')
            try:
                dish = Dish.objects.get(id=dish_id, restaurant=restaurant)
                dish.is_available = not dish.is_available
                dish.save()
            except Dish.DoesNotExist:
                pass
        return redirect('manager_menu')

    context = {
        'restaurant': restaurant,
        'worker': worker,
        'dishes': dishes,
        'categories': categories,
        'user_role': worker.role,
    }
    return render(request, 'dashboards/manager_menu.html', context)


@require_worker_role('manager', 'asst_manager')
def manager_tables(request):
    worker = request.user.worker_profile
    restaurant = worker.restaurant
    tables = Table.objects.filter(restaurant=restaurant)
    context = {
        'restaurant': restaurant,
        'worker': worker,
        'tables': tables,
        'user_role': worker.role,
    }
    return render(request, 'dashboards/manager_tables.html', context)


@require_worker_role('manager', 'asst_manager')
def manager_invoices(request):
    worker = request.user.worker_profile
    restaurant = worker.restaurant
    invoices = Invoice.objects.filter(restaurant=restaurant).select_related('table', 'waiter')[:50]
    context = {
        'restaurant': restaurant,
        'worker': worker,
        'invoices': invoices,
        'user_role': worker.role,
    }
    return render(request, 'dashboards/manager_invoices.html', context)


@require_worker_role('manager', 'asst_manager')
def manager_qr_menu(request):
    worker = request.user.worker_profile
    restaurant = worker.restaurant
    context = {
        'restaurant': restaurant,
        'worker': worker,
        'menu_url': f"/menu/{restaurant.slug}/",
        'user_role': worker.role,
    }
    return render(request, 'dashboards/owner_qr_menu.html', context)


@require_worker_role('manager')
def asst_manager_dashboard(request):
    return manager_dashboard(request)


# ===== RECEPTIONIST DASHBOARD =====

@require_worker_role('receptionist')
def reception_dashboard(request):
    worker = request.user.worker_profile
    restaurant = worker.restaurant
    today = date.today()

    tables = Table.objects.filter(restaurant=restaurant)
    today_invoices = Invoice.objects.filter(restaurant=restaurant, created_at__date=today).count()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'seat_customer':
            table_id = request.POST.get('table_id')
            party_size = int(request.POST.get('party_size', 1))
            try:
                table = Table.objects.get(id=table_id, restaurant=restaurant, status=Table.STATUS_FREE)
                table.status = Table.STATUS_OCCUPIED
                table.current_customers = party_size
                table.save()
                # Create order
                waiter_id = request.POST.get('waiter_id')
                waiter = None
                if waiter_id:
                    try:
                        waiter = Worker.objects.get(id=waiter_id, restaurant=restaurant)
                    except Worker.DoesNotExist:
                        pass
                Order.objects.create(
                    restaurant=restaurant,
                    table=table,
                    waiter=waiter,
                    customer_count=party_size
                )
                messages.success(request, f'Table {table.number} seated with {party_size} guests.')
            except Table.DoesNotExist:
                messages.error(request, 'Table not available.')
            return redirect('reception_dashboard')

    waiters = Worker.objects.filter(restaurant=restaurant, role=Worker.ROLE_WAITER, is_active=True)
    context = {
        'restaurant': restaurant,
        'worker': worker,
        'tables': tables,
        'today_invoices': today_invoices,
        'waiters': waiters,
        'user_role': 'receptionist',
    }
    return render(request, 'dashboards/reception_dashboard.html', context)


@require_worker_role('receptionist')
def reception_billing(request, table_id):
    worker = request.user.worker_profile
    restaurant = worker.restaurant

    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    try:
        order = Order.objects.get(table=table, status=Order.STATUS_OPEN)
    except Order.DoesNotExist:
        messages.error(request, 'No active order for this table.')
        return redirect('reception_dashboard')

    dishes = Dish.objects.filter(restaurant=restaurant, is_available=True)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_item':
            dish_id = request.POST.get('dish_id')
            qty = int(request.POST.get('quantity', 1))
            try:
                dish = Dish.objects.get(id=dish_id, restaurant=restaurant)
                item, created = OrderItem.objects.get_or_create(
                    order=order, dish=dish,
                    defaults={'quantity': qty, 'unit_price': dish.price}
                )
                if not created:
                    item.quantity += qty
                    item.save()
                messages.success(request, f'Added {dish.name}.')
            except Dish.DoesNotExist:
                messages.error(request, 'Dish not found.')
            return redirect('reception_billing', table_id=table_id)

        elif action == 'finalize':
            discount_type = request.POST.get('discount_type', '')
            raw_discount = request.POST.get('discount_value', '').strip()
            discount_value = float(raw_discount) if raw_discount else 0.0
            payment_mode = request.POST.get('payment_mode', 'cash')

            subtotal = order.get_total()
            discount_amount = 0
            if discount_type == 'flat':
                discount_amount = discount_value
            elif discount_type == 'percent':
                discount_amount = float(subtotal) * discount_value / 100

            taxable = float(subtotal) - discount_amount
            gst_rate = 5.0
            gst_amount = taxable * gst_rate / 100
            grand_total = taxable + gst_amount

            invoice = Invoice.objects.create(
                restaurant=restaurant,
                table=table,
                order=order,
                waiter=order.waiter,
                receptionist=worker,
                subtotal=subtotal,
                discount_type=discount_type,
                discount_value=discount_value,
                discount_amount=discount_amount,
                gst_rate=gst_rate,
                gst_amount=gst_amount,
                grand_total=grand_total,
                payment_mode=payment_mode,
                customer_count=order.customer_count,
            )

            order.status = Order.STATUS_COMPLETED
            order.save()
            table.status = Table.STATUS_FREE
            table.current_customers = 0
            table.save()

            messages.success(request, f'Invoice {invoice.invoice_number} generated! ₹{grand_total:.2f}')
            return redirect('reception_invoices')

    context = {
        'restaurant': restaurant,
        'worker': worker,
        'table': table,
        'order': order,
        'order_items': order.items.select_related('dish').all(),
        'dishes': dishes,
        'subtotal': order.get_total(),
        'user_role': 'receptionist',
    }
    return render(request, 'dashboards/reception_billing.html', context)


@require_worker_role('receptionist')
def reception_invoices(request):
    worker = request.user.worker_profile
    restaurant = worker.restaurant
    today = date.today()
    invoices = Invoice.objects.filter(restaurant=restaurant, created_at__date=today).select_related('table', 'waiter')
    context = {
        'restaurant': restaurant,
        'worker': worker,
        'invoices': invoices,
        'user_role': 'receptionist',
    }
    return render(request, 'dashboards/reception_invoices.html', context)


# ===== WAITER DASHBOARD =====

@require_worker_role('waiter')
def waiter_dashboard(request):
    worker = request.user.worker_profile
    restaurant = worker.restaurant
    orders = Order.objects.filter(
        restaurant=restaurant,
        status=Order.STATUS_OPEN
    ).select_related('table')
    free_tables = Table.objects.filter(restaurant=restaurant, status=Table.STATUS_FREE)

    context = {
        'restaurant': restaurant,
        'worker': worker,
        'assigned_orders': orders,
        'free_tables': free_tables,
        'user_role': 'waiter',
    }
    return render(request, 'dashboards/waiter_dashboard.html', context)


@require_worker_role('waiter')
def waiter_table(request, table_id):
    worker = request.user.worker_profile
    restaurant = worker.restaurant

    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    try:
        order = Order.objects.get(table=table, status=Order.STATUS_OPEN)
        if order.waiter != worker:
            return render(request, 'core/403.html', status=403)
    except Order.DoesNotExist:
        messages.error(request, 'No active order for this table.')
        return redirect('waiter_dashboard')

    dishes = Dish.objects.filter(restaurant=restaurant, is_available=True).select_related('category')
    categories = MenuCategory.objects.filter(restaurant=restaurant, is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_item':
            dish_id = request.POST.get('dish_id')
            quantity = int(request.POST.get('quantity', 1))
            try:
                dish = Dish.objects.get(id=dish_id, restaurant=restaurant, is_available=True)
                item, created = OrderItem.objects.get_or_create(
                    order=order, dish=dish,
                    status=OrderItem.ITEM_STATUS_PENDING,
                    defaults={'quantity': quantity}
                )
                if not created:
                    item.quantity += quantity
                    item.save()
                messages.success(request, f'Added {dish.name} to order.')
            except Dish.DoesNotExist:
                messages.error(request, 'Dish not found or unavailable.')
            return redirect('waiter_table', table_id=table_id)

        elif action == 'remove_item':
            item_id = request.POST.get('item_id')
            try:
                # Remove the entire item line if it's still pending
                item = OrderItem.objects.get(id=item_id, order=order, status=OrderItem.ITEM_STATUS_PENDING)
                item_name = item.dish.name
                item.delete()
                messages.success(request, f'Removed {item_name} from order.')
            except OrderItem.DoesNotExist:
                messages.error(request, 'Cannot remove item (it may already be in the kitchen).')
            return redirect('waiter_table', table_id=table_id)

    context = {
        'restaurant': restaurant,
        'worker': worker,
        'table': table,
        'order': order,
        'order_items': order.items.select_related('dish').all(),
        'menu_items': dishes,
        'categories': categories,
        'user_role': 'waiter',
    }
    return render(request, 'dashboards/waiter_table.html', context)


# ===== CHEF DASHBOARD =====

@require_worker_role('chef')
def chef_dashboard(request):
    worker = request.user.worker_profile
    restaurant = worker.restaurant

    pending_items = OrderItem.objects.filter(
        order__restaurant=restaurant,
        order__status=Order.STATUS_OPEN,
        status__in=[OrderItem.ITEM_STATUS_PENDING, OrderItem.ITEM_STATUS_IN_KITCHEN]
    ).select_related('dish', 'order__table').order_by('added_at')

    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        new_status = request.POST.get('status')
        try:
            item = OrderItem.objects.get(id=item_id, order__restaurant=restaurant)
            if new_status in ['in_kitchen', 'served']:
                item.status = new_status
                item.save()
        except OrderItem.DoesNotExist:
            pass
        return redirect('chef_dashboard')

    context = {
        'restaurant': restaurant,
        'worker': worker,
        'pending_items': pending_items,
        'user_role': 'chef',
    }
    return render(request, 'dashboards/chef_dashboard.html', context)


@login_required
def invoice_print(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if hasattr(request.user, 'worker_profile'):
        restaurant = request.user.worker_profile.restaurant
    elif hasattr(request.user, 'restaurant'):
        restaurant = request.user.restaurant
    else: 
        restaurant = invoice.restaurant
        
    if invoice.restaurant != restaurant and not hasattr(request.user, 'super_admin_profile'):
        return render(request, 'core/403.html', status=403)
        
    return render(request, 'dashboards/invoice_print.html', {'invoice': invoice, 'restaurant': invoice.restaurant})


# ===== SUPER ADMIN =====

@require_superadmin
def superadmin_dashboard(request):
    total_restaurants = Restaurant.objects.count()
    active_restaurants = Restaurant.objects.filter(status=Restaurant.STATUS_ACTIVE).count()
    pending_restaurants = Restaurant.objects.filter(status=Restaurant.STATUS_PENDING).count()
    total_workers = Worker.objects.count()
    today = date.today()
    today_invoices = Invoice.objects.filter(created_at__date=today).count()
    today_revenue = Invoice.objects.filter(created_at__date=today).aggregate(total=Sum('grand_total'))['total'] or 0

    pending_list = Restaurant.objects.filter(status=Restaurant.STATUS_PENDING).select_related('owner')[:10]

    context = {
        'total_restaurants': total_restaurants,
        'active_restaurants': active_restaurants,
        'pending_restaurants': pending_restaurants,
        'total_workers': total_workers,
        'today_invoices': today_invoices,
        'today_revenue': today_revenue,
        'pending_list': pending_list,
        'user_role': 'superadmin',
    }
    return render(request, 'dashboards/superadmin_dashboard.html', context)


@require_superadmin
def superadmin_restaurants(request):
    restaurants = Restaurant.objects.all().select_related('owner')
    context = {
        'restaurants': restaurants,
        'user_role': 'superadmin',
    }
    return render(request, 'dashboards/superadmin_restaurants.html', context)


@require_superadmin
def superadmin_pending(request):
    pending = Restaurant.objects.filter(status=Restaurant.STATUS_PENDING).select_related('owner')
    context = {
        'pending': pending,
        'user_role': 'superadmin',
    }
    return render(request, 'dashboards/superadmin_pending.html', context)


@require_superadmin
def superadmin_approve(request, restaurant_id):
    if request.method == 'POST':
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        restaurant.status = Restaurant.STATUS_ACTIVE
        restaurant.approval_date = timezone.now()
        restaurant.save()

        # Auto-generate QR code
        try:
            import qrcode
            import io
            from django.core.files.base import ContentFile
            menu_url = f"http://localhost:8000/menu/{restaurant.slug}/"
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(menu_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#0E0C0A", back_color="#F5F0E8")
            img_io = io.BytesIO()
            img.save(img_io, format='PNG')
            img_io.seek(0)
            restaurant.qr_code_local.save(
                f'qr_{restaurant.slug}.png',
                ContentFile(img_io.read()),
                save=True
            )
        except Exception as e:
            print(f"QR generation error: {e}")

        AuditLog.objects.create(
            actor=request.user,
            actor_name=request.user.get_full_name() or request.user.email,
            action='Restaurant Approved',
            description=f'Approved {restaurant.name}',
            restaurant=restaurant
        )
        messages.success(request, f'{restaurant.name} approved and activated!')
    return redirect('superadmin_pending')


@require_superadmin
def superadmin_reject(request, restaurant_id):
    if request.method == 'POST':
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        note = request.POST.get('note', '')
        restaurant.status = Restaurant.STATUS_REJECTED
        restaurant.rejection_note = note
        restaurant.save()
        AuditLog.objects.create(
            actor=request.user,
            actor_name=request.user.get_full_name() or request.user.email,
            action='Restaurant Rejected',
            description=f'Rejected {restaurant.name}. Note: {note}',
            restaurant=restaurant
        )
        messages.warning(request, f'{restaurant.name} rejected.')
    return redirect('superadmin_pending')


@require_superadmin
def superadmin_audit(request):
    logs = AuditLog.objects.all().select_related('actor', 'restaurant')[:100]
    context = {
        'logs': logs,
        'user_role': 'superadmin',
    }
    return render(request, 'dashboards/superadmin_audit.html', context)


@require_superadmin
def superadmin_broadcast(request):
    announcements = Announcement.objects.filter(is_active=True)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        if title and message:
            Announcement.objects.create(title=title, message=message, created_by=request.user)
            messages.success(request, 'Announcement broadcast to all restaurants!')
        return redirect('superadmin_broadcast')
    context = {
        'announcements': announcements,
        'user_role': 'superadmin',
    }
    return render(request, 'dashboards/superadmin_broadcast.html', context)
