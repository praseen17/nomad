import os
import django
import uuid

# Set up Django environment manually
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nomad.settings')
django.setup()

from django.contrib.auth.models import User
from restaurant.models import Restaurant, SuperAdmin
from workers.models import Worker

def create_dummy_data():
    print("Creating dummy data for NOMAD...")
    
    # 1. Super Admin
    if not User.objects.filter(email='admin@nomad.com').exists():
        admin_user = User.objects.create_superuser('admin', 'admin@nomad.com', 'admin123')
        SuperAdmin.objects.create(user=admin_user)
        print("✅ SuperAdmin created: admin@nomad.com / admin123")
    else:
        print("⚠️ SuperAdmin already exists.")

    # 2. Restaurant Owner
    if not User.objects.filter(email='owner@test.com').exists():
        owner_user = User.objects.create_user('testowner', 'owner@test.com', 'password123')
        owner_user.first_name = "Test"
        owner_user.last_name = "Owner"
        owner_user.save()
        
        restaurant = Restaurant.objects.create(
            owner=owner_user,
            name="The Grand Nomad",
            slug="grand-nomad",
            restaurant_type="fine_dining",
            address_city="Mumbai",
            status='active'
        )
        print("✅ Owner & Restaurant created: owner@test.com / password123")
    else:
        print("⚠️ Owner already exists.")
        restaurant = Restaurant.objects.get(slug="grand-nomad")

    # 3. Workers (Manager, Receptionist, Waiter, Chef)
    roles = [
        ('manager', 'MGR-1001', 'Maya Manager'),
        ('receptionist', 'REC-2001', 'Rahul Reception'),
        ('waiter', 'WTR-3001', 'Wendy Waiter'),
        ('chef', 'CHF-4001', 'Charlie Chef')
    ]

    for role, worker_id, full_name in roles:
        if not Worker.objects.filter(worker_id=worker_id).exists():
            uid = uuid.uuid4().hex
            username = f"{worker_id.lower()}_{uid[0:6]}"
            user = User.objects.create_user(username=username, password='password123')
            
            Worker.objects.create(
                user=user,
                restaurant=restaurant,
                full_name=full_name,
                role=role,
                worker_id=worker_id,
                is_active=True
            )
            print(f"✅ {role.capitalize()} created: {worker_id} / password123")
        else:
            print(f"⚠️ Worker {worker_id} already exists.")

    print("\n🎉 Dummy data generated successfully! You can now test the login gateways.")

if __name__ == '__main__':
    create_dummy_data()
