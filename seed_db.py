import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'giftsphere.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Profile, Category, Product, GroupGift, Pledge, Wishlist


def seed():
    print("Clearing old data...")
    User.objects.filter(is_superuser=False).delete()
    Category.objects.all().delete()
    Product.objects.all().delete()

    print("1. Creating Users...")
    users_data = [
        {"username": "0551112222", "name": "Ahmed"},
        {"username": "0553334444", "name": "Sarah"},
        {"username": "0555556666", "name": "Khalid"},
        {"username": "0557778888", "name": "Noura"},
    ]

    db_users = []
    for u in users_data:
        user = User.objects.create_user(username=u["username"], first_name=u["name"])
        Profile.objects.create(user=user, phone_number=u["username"], otp_code="1234")
        db_users.append(user)

    ahmed, sarah, khalid, noura = db_users

    print("2. Creating Categories...")
    cat_tech = Category.objects.create(name="Electronics", icon="computer")
    cat_perfume = Category.objects.create(name="Perfumes", icon="local_florist")
    cat_auto = Category.objects.create(name="Auto & Car", icon="directions_car")

    print("3. Creating Products...")
    p1 = Product.objects.create(
        name="Sony PlayStation 5",
        category=cat_tech,
        price=2099.00,
        description="The ultimate gaming console.",
        image_url="https://placehold.co/400x400/png?text=PS5",
        affiliate_link="https://amazon.sa/dp/ps5-dummy",
        store_name="Amazon SA"
    )

    p2 = Product.objects.create(
        name="Dior Sauvage Eau de Parfum",
        category=cat_perfume,
        price=540.00,
        description="A bold and powerful fragrance.",
        image_url="https://placehold.co/400x400/png?text=Dior+Sauvage",
        affiliate_link="https://noon.com/sa-en/dior-dummy",
        store_name="Noon"
    )

    p3 = Product.objects.create(
        name="Ford Escape 2014 Right Front Shock Strut",
        category=cat_auto,
        price=350.00,
        description="OEM replacement part for 2.0L engine.",
        image_url="https://placehold.co/400x400/png?text=Car+Part",
        affiliate_link="https://amazon.sa/dp/ford-dummy",
        store_name="Amazon SA"
    )

    print("4. Creating Group Gifts (The Qattah)...")
    gift1 = GroupGift.objects.create(
        organizer=ahmed,
        product=p1,
        title="Khalid's Graduation Gift",
        target_amount=2099.00,
        collected_amount=1000.00,
        status="ACTIVE"
    )

    print("5. Creating Pledges...")
    Pledge.objects.create(group_gift=gift1, user=ahmed, amount=500.00, message="Mabrook Khalid!")
    Pledge.objects.create(group_gift=gift1, user=sarah, amount=500.00, message="So proud of you!")

    print("6. Creating Wishlists...")
    wishlist1 = Wishlist.objects.create(user=sarah, title="Sarah's Wedding Registry")
    wishlist1.products.add(p2)  # Add perfume
    wishlist1.shared.add(noura)  # Share with Noura

    print("✅ SUCCESS! Database seeded with mock data.")


if __name__ == '__main__':
    seed()