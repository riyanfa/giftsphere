# GiftSphere

GiftSphere is an affiliate-based social gifting platform designed for the Saudi market. It helps users discover gifts, manage wishlists, create Qattah group gifts, organize Secret Gift exchanges, receive quiz-based recommendations, and open external Amazon/Noon affiliate links.

## Features

- OTP phone authentication
- Product browsing, search, category filtering, and budget filtering
- Featured products and curated collections
- Wishlist creation and product management
- Quiz-based gift recommendations
- Qattah group gifting with invite codes, pledges, and payment instructions
- Secret Gift exchange with random assignment generation
- Event reminders and upcoming reminders
- Affiliate click tracking
- In-app notifications

## Tech Stack

- Flutter
- Django
- Django REST Framework
- PostgreSQL
- Docker
- Bruno for API testing

## Installation

```bash
git clone https://github.com/riyanfa/giftsphere.git
cd giftsphere

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Docker

```bash
docker compose up --build
```

Useful Docker commands:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py test core
```

## Main API Endpoints

### Auth

```http
POST /api/login/request/
POST /api/login/verify/
```

### Products

```http
GET  /api/products/
GET  /api/products/collections/
GET  /api/products/featured/
POST /api/products/<id>/affiliate-click/
POST /api/products/quiz/
```

### Wishlist

```http
GET  /api/wishlist/
POST /api/wishlist/create/
POST /api/wishlist/add_product/
POST /api/wishlist/remove_product/
```

### Qattah

```http
GET  /api/qattah/
POST /api/qattah/create/
POST /api/qattah/join/
POST /api/qattah/<id>/pledge/
```

### Secret Gift

```http
GET  /api/exchange/
POST /api/exchange/create/
POST /api/exchange/join/
POST /api/exchange/<id>/draw/
GET  /api/exchange/<id>/my/
```

### Reminders

```http
GET    /api/reminders/
POST   /api/reminders/create/
GET    /api/reminders/upcoming/
PATCH  /api/reminders/<id>/
DELETE /api/reminders/<id>/
```

## Testing

```bash
python manage.py test core
```

The backend tests cover authentication, product browsing, wishlist operations, Qattah, Secret Gift exchange, reminders, affiliate clicks, and permission checks.

## Project Scope

GiftSphere focuses on social gifting and affiliate product discovery.

Out of scope:

- Direct payment processing
- Wallet balance management
- Vendor onboarding
- Shipping and delivery logistics
- Internal order processing
