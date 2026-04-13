# core/views/__init__.py
from .auth import request_otp, verify_otp
from .products import get_products
from .wishlists import get_wishlist, delete_wishlist
from .util_views import get_current_user, set_full_name
from .gift_exchange import create_exchange,join_exchange,draw_assignments,my_assignment

