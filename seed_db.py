import os
import django
from decimal import Decimal
from datetime import timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "giftsphere.settings")
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone

from core.models import (
    Category,
    Product,
    Profile,
    Wishlist,
    WishlistItem,
    GroupGift,
    GroupGiftParticipant,
    SecretGiftExchange,
    SecretGiftParticipant,
    EventReminder,
)


def create_user(username, phone, first_name, last_name):
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
        },
    )

    user.first_name = first_name
    user.last_name = last_name
    user.save()

    Profile.objects.get_or_create(
        user=user,
        defaults={"phone_number": phone},
    )

    return user


def create_category(name, icon="star"):
    category, _ = Category.objects.get_or_create(
        name=name,
        defaults={"icon": icon},
    )
    return category


def create_product(
    name,
    category,
    price,
    description,
    image_url,
    affiliate_link,
    store_name="Amazon SA",
    occasion="",
    target_gender="any",
    min_age=None,
    max_age=None,
    interests="",
    is_featured=False,
    collection_name="",
):
    product, created = Product.objects.get_or_create(
        name=name,
        defaults={
            "category": category,
            "price": Decimal(str(price)),
            "description": description,
            "image_url": image_url,
            "affiliate_link": affiliate_link,
            "store_name": store_name,
            "occasion": occasion,
            "target_gender": target_gender,
            "min_age": min_age,
            "max_age": max_age,
            "interests": interests,
            "is_active": True,
            "is_featured": is_featured,
            "collection_name": collection_name,
        },
    )

    if not created:
        product.category = category
        product.price = Decimal(str(price))
        product.description = description
        product.image_url = image_url
        product.affiliate_link = affiliate_link
        product.store_name = store_name
        product.occasion = occasion
        product.target_gender = target_gender
        product.min_age = min_age
        product.max_age = max_age
        product.interests = interests
        product.is_active = True
        product.is_featured = is_featured
        product.collection_name = collection_name
        product.save()

    return product


def run():
    print("Seeding GiftSphere dummy data...")

    # Users
    ali = create_user("512345678", "512345678", "Ali", "Al Saud")
    sara = create_user("512345679", "512345679", "Sara", "Khalid")
    omar = create_user("512345680", "512345680", "Omar", "Fahad")

    # Categories
    electronics = create_category("Electronics", "devices")
    perfumes = create_category("Perfumes", "spa")
    books = create_category("Books", "menu_book")
    games = create_category("Games", "sports_esports")
    accessories = create_category("Accessories", "watch")
    gift_cards = create_category("Gift Cards", "card_giftcard")
    fitness = create_category("Fitness", "fitness_center")
    home = create_category("Home & Lifestyle", "home")

    products = [
        {
            "name": "Sony Wireless Headphones",
            "category": electronics,
            "price": "299.00",
            "description": "Comfortable wireless headphones suitable for gaming, studying, and music.",
            "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "graduation",
            "target_gender": "any",
            "min_age": 16,
            "max_age": 35,
            "interests": "gaming, music, tech, student",
            "is_featured": True,
            "collection_name": "Graduation Gifts",
        },
        {
            "name": "Gaming Mouse",
            "category": games,
            "price": "149.00",
            "description": "High precision gaming mouse for PC gamers and students.",
            "image_url": "https://images.unsplash.com/photo-1527814050087-3793815479db",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "birthday",
            "target_gender": "any",
            "min_age": 13,
            "max_age": 30,
            "interests": "gaming, pc, esports, tech",
            "is_featured": True,
            "collection_name": "Gifts for Gamers",
        },
        {
            "name": "Mechanical Keyboard",
            "category": electronics,
            "price": "259.00",
            "description": "Mechanical keyboard for productivity, gaming, and programming.",
            "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "graduation",
            "target_gender": "any",
            "min_age": 16,
            "max_age": 40,
            "interests": "programming, gaming, tech, study",
            "is_featured": True,
            "collection_name": "Gifts for Students",
        },
        {
            "name": "Amazon Gift Card",
            "category": gift_cards,
            "price": "100.00",
            "description": "Flexible digital gift card suitable for most occasions.",
            "image_url": "https://images.unsplash.com/photo-1607083206968-13611e3d76db",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "birthday",
            "target_gender": "any",
            "min_age": 12,
            "max_age": 60,
            "interests": "shopping, digital, flexible",
            "is_featured": True,
            "collection_name": "Budget Gifts",
        },
        {
            "name": "Luxury Oud Perfume",
            "category": perfumes,
            "price": "350.00",
            "description": "Elegant oud perfume suitable for Eid, weddings, and formal occasions.",
            "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "eid",
            "target_gender": "any",
            "min_age": 20,
            "max_age": 60,
            "interests": "perfume, luxury, oud, fragrance",
            "is_featured": True,
            "collection_name": "Eid Gifts",
        },
        {
            "name": "Women Floral Perfume",
            "category": perfumes,
            "price": "220.00",
            "description": "Soft floral perfume suitable for birthdays and special occasions.",
            "image_url": "https://images.unsplash.com/photo-1541643600914-78b084683601",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "birthday",
            "target_gender": "female",
            "min_age": 18,
            "max_age": 50,
            "interests": "perfume, beauty, fragrance",
            "is_featured": False,
            "collection_name": "Gifts for Her",
        },
        {
            "name": "Smart Watch",
            "category": accessories,
            "price": "399.00",
            "description": "Smart watch for fitness tracking, notifications, and daily use.",
            "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "graduation",
            "target_gender": "any",
            "min_age": 16,
            "max_age": 45,
            "interests": "fitness, tech, lifestyle, student",
            "is_featured": True,
            "collection_name": "Graduation Gifts",
        },
        {
            "name": "Leather Wallet",
            "category": accessories,
            "price": "120.00",
            "description": "Classic leather wallet suitable for practical everyday use.",
            "image_url": "https://images.unsplash.com/photo-1627123424574-724758594e93",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "birthday",
            "target_gender": "male",
            "min_age": 18,
            "max_age": 60,
            "interests": "fashion, practical, accessories",
            "is_featured": False,
            "collection_name": "Budget Gifts",
        },
        {
            "name": "Coffee Maker",
            "category": home,
            "price": "280.00",
            "description": "Compact coffee maker for home, office, and students.",
            "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "birthday",
            "target_gender": "any",
            "min_age": 18,
            "max_age": 60,
            "interests": "coffee, home, lifestyle, office",
            "is_featured": True,
            "collection_name": "Home & Lifestyle",
        },
        {
            "name": "Islamic Desk Decoration",
            "category": home,
            "price": "89.00",
            "description": "Simple Islamic-themed desk decoration suitable for Ramadan and Eid.",
            "image_url": "https://images.unsplash.com/photo-1564769662533-4f00a87b4056",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "eid",
            "target_gender": "any",
            "min_age": 15,
            "max_age": 70,
            "interests": "islamic, home, decoration, ramadan",
            "is_featured": False,
            "collection_name": "Eid Gifts",
        },
        {
            "name": "Fitness Resistance Bands",
            "category": fitness,
            "price": "75.00",
            "description": "Portable resistance bands for home workouts and fitness routines.",
            "image_url": "https://images.unsplash.com/photo-1518611012118-696072aa579a",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "birthday",
            "target_gender": "any",
            "min_age": 15,
            "max_age": 45,
            "interests": "fitness, gym, health, sports",
            "is_featured": False,
            "collection_name": "Budget Gifts",
        },
        {
            "name": "Programming Book",
            "category": books,
            "price": "135.00",
            "description": "Beginner-friendly programming book for students and future developers.",
            "image_url": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "graduation",
            "target_gender": "any",
            "min_age": 16,
            "max_age": 35,
            "interests": "programming, study, software, backend",
            "is_featured": False,
            "collection_name": "Gifts for Students",
        },
        {
            "name": "Novel Gift Set",
            "category": books,
            "price": "180.00",
            "description": "A selected book gift set for readers and literature lovers.",
            "image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "birthday",
            "target_gender": "any",
            "min_age": 14,
            "max_age": 60,
            "interests": "reading, books, novels, literature",
            "is_featured": False,
            "collection_name": "Gifts for Readers",
        },
        {
            "name": "Bluetooth Speaker",
            "category": electronics,
            "price": "199.00",
            "description": "Portable Bluetooth speaker for gatherings, trips, and daily listening.",
            "image_url": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "birthday",
            "target_gender": "any",
            "min_age": 15,
            "max_age": 40,
            "interests": "music, tech, travel, friends",
            "is_featured": True,
            "collection_name": "Gifts for Friends",
        },
        {
            "name": "Desk Organizer",
            "category": home,
            "price": "65.00",
            "description": "Minimal desk organizer for students and office use.",
            "image_url": "https://images.unsplash.com/photo-1497366754035-f200968a6e72",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "graduation",
            "target_gender": "any",
            "min_age": 12,
            "max_age": 40,
            "interests": "study, office, organization, student",
            "is_featured": False,
            "collection_name": "Budget Gifts",
        },
        {
            "name": "Skincare Gift Set",
            "category": accessories,
            "price": "240.00",
            "description": "Self-care skincare set suitable for birthdays and appreciation gifts.",
            "image_url": "https://images.unsplash.com/photo-1556228578-8c89e6adf883",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "birthday",
            "target_gender": "female",
            "min_age": 18,
            "max_age": 50,
            "interests": "beauty, skincare, self-care",
            "is_featured": True,
            "collection_name": "Gifts for Her",
        },
        {
            "name": "Prayer Mat Gift Set",
            "category": home,
            "price": "160.00",
            "description": "Elegant prayer mat gift set suitable for Ramadan, Eid, and family gifts.",
            "image_url": "https://images.unsplash.com/photo-1609599006353-e629aaabfeae",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "eid",
            "target_gender": "any",
            "min_age": 16,
            "max_age": 70,
            "interests": "islamic, prayer, eid, family",
            "is_featured": True,
            "collection_name": "Eid Gifts",
        },
        {
            "name": "Backpack for Students",
            "category": accessories,
            "price": "180.00",
            "description": "Durable backpack suitable for university students and daily use.",
            "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "graduation",
            "target_gender": "any",
            "min_age": 15,
            "max_age": 30,
            "interests": "student, university, travel, study",
            "is_featured": False,
            "collection_name": "Gifts for Students",
        },
        {
            "name": "Wireless Charger",
            "category": electronics,
            "price": "95.00",
            "description": "Fast wireless charger for phones and everyday desk use.",
            "image_url": "https://images.unsplash.com/photo-1618577608401-7f1f7ab268fb",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "birthday",
            "target_gender": "any",
            "min_age": 15,
            "max_age": 45,
            "interests": "tech, phone, accessories, practical",
            "is_featured": False,
            "collection_name": "Budget Gifts",
        },
        {
            "name": "Football Jersey",
            "category": fitness,
            "price": "210.00",
            "description": "Sports jersey gift for football fans.",
            "image_url": "https://images.unsplash.com/photo-1579952363873-27f3bade9f55",
            "affiliate_link": "https://www.amazon.sa/",
            "occasion": "birthday",
            "target_gender": "male",
            "min_age": 12,
            "max_age": 35,
            "interests": "football, sports, fitness, fans",
            "is_featured": False,
            "collection_name": "Gifts for Friends",
        },
    ]

    created_products = []
    for p in products:
        created_products.append(create_product(**p))

    # Wishlist sample
    wishlist, _ = Wishlist.objects.get_or_create(
        user=ali,
        title="My Graduation Wishlist",
        defaults={"visibility": "PUBLIC"},
    )

    for product in created_products[:5]:
        WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=product,
        )

    # Qattah sample
    qattah, created = GroupGift.objects.get_or_create(
        organizer=ali,
        title="Graduation Qattah for Headphones",
        defaults={
            "recipient": sara,
            "product": created_products[0],
            "target_amount": created_products[0].price,
            "collected_amount": Decimal("50.00"),
            "status": "ACTIVE",
            "deadline": timezone.now() + timedelta(days=5),
            "payment_method_note": "Transfer to STC Pay 05xxxxxxxx",
        },
    )

    GroupGiftParticipant.objects.get_or_create(
        group_gift=qattah,
        user=ali,
        defaults={"status": GroupGiftParticipant.STATUS_ACCEPTED},
    )

    GroupGiftParticipant.objects.get_or_create(
        group_gift=qattah,
        user=omar,
        defaults={"status": GroupGiftParticipant.STATUS_ACCEPTED},
    )

    # Secret Gift sample
    exchange, _ = SecretGiftExchange.objects.get_or_create(
        organizer=ali,
        title="Friends Secret Gift",
        defaults={
            "budget": Decimal("150.00"),
            "status": "PENDING",
        },
    )

    for user in [ali, sara, omar]:
        SecretGiftParticipant.objects.get_or_create(
            exchange=exchange,
            user=user,
            defaults={"status": SecretGiftParticipant.STATUS_ACCEPTED},
        )

    # Event reminders
    EventReminder.objects.get_or_create(
        user=ali,
        title="Sara Graduation",
        defaults={
            "event_date": timezone.now() + timedelta(days=10),
            "reminder_date": timezone.now() + timedelta(days=7),
            "recipient_name": "Sara",
            "notes": "Prepare graduation gift and check wishlist.",
        },
    )

    EventReminder.objects.get_or_create(
        user=ali,
        title="Eid Gift Reminder",
        defaults={
            "event_date": timezone.now() + timedelta(days=20),
            "reminder_date": timezone.now() + timedelta(days=15),
            "recipient_name": "Family",
            "notes": "Check Eid gift collection.",
        },
    )

    print("Done.")
    print(f"Users: {User.objects.count()}")
    print(f"Categories: {Category.objects.count()}")
    print(f"Products: {Product.objects.count()}")
    print(f"Wishlists: {Wishlist.objects.count()}")
    print(f"Qattahs: {GroupGift.objects.count()}")
    print(f"Secret Gift Exchanges: {SecretGiftExchange.objects.count()}")
    print(f"Reminders: {EventReminder.objects.count()}")


if __name__ == "__main__":
    run()