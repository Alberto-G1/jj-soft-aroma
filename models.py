from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()

class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Category(db.Model):
    __tablename__ = 'categories'
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(100), nullable=False)
    slug      = db.Column(db.String(100), unique=True, nullable=False)
    icon_url  = db.Column(db.String(300), nullable=True)
    products  = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False)
    price       = db.Column(db.Numeric(12, 2), nullable=False)
    sale_price  = db.Column(db.Numeric(12, 2), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image_url   = db.Column(db.String(300), nullable=True)
    stock       = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    images      = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')

class ProductImage(db.Model):
    __tablename__ = 'product_images'
    id          = db.Column(db.Integer, primary_key=True)
    product_id  = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    image_url   = db.Column(db.String(300), nullable=False)
    is_main     = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Customer(db.Model):
    __tablename__ = 'customers'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(150), nullable=False)
    phone      = db.Column(db.String(20), unique=True, nullable=False)
    location   = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Order(db.Model):
    __tablename__ = 'orders'
    id             = db.Column(db.Integer, primary_key=True)
    customer_name  = db.Column(db.String(150), nullable=False)
    phone          = db.Column(db.String(20), nullable=False)
    location       = db.Column(db.String(200), nullable=False)
    delivery_notes = db.Column(db.String(300), nullable=True) 
    total_price    = db.Column(db.Numeric(12, 2), nullable=False)
    payment_method = db.Column(db.String(50), default='whatsapp')
    status         = db.Column(db.String(50), default='pending')
    created_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    items          = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity   = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    product    = db.relationship('Product')

class Review(db.Model):
    __tablename__ = 'reviews'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(150), nullable=False)
    role        = db.Column(db.String(150), nullable=True)
    rating      = db.Column(db.Integer, nullable=False, default=5)
    message     = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id               = db.Column(db.Integer, primary_key=True)
    name             = db.Column(db.String(150), nullable=False)
    contact          = db.Column(db.String(200), nullable=False)
    subject          = db.Column(db.String(200), nullable=False)
    message          = db.Column(db.Text, nullable=False)
    recipient_email  = db.Column(db.String(200), nullable=False)
    delivery_status  = db.Column(db.String(30), default='pending')
    error_message    = db.Column(db.String(300), nullable=True)
    sent_at          = db.Column(db.DateTime, nullable=True)
    created_at       = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    icon       = db.Column(db.String(50), default='bell')
    color      = db.Column(db.String(30), default='primary')
    is_read    = db.Column(db.Boolean, default=False)
    link       = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class StoreSetting(db.Model):
    __tablename__ = 'store_settings'
    id                     = db.Column(db.Integer, primary_key=True)
    store_name             = db.Column(db.String(200), default='J&J Soft Aroma')
    phone                  = db.Column(db.String(20), default='0760868005')
    email                  = db.Column(db.String(200), default='nuwarindaalbertgrande@gmail.com')
    address                = db.Column(db.String(300), default='Kampala, Uganda')
    currency               = db.Column(db.String(10), default='UGX')
    free_delivery_threshold= db.Column(db.Numeric(12, 2), default=50000)
    sms_notifications      = db.Column(db.Boolean, default=True)
    notify_phone           = db.Column(db.String(20), default='0763085855')

class Offer(db.Model):
    __tablename__ = 'offers'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(160), nullable=False)
    subtitle    = db.Column(db.String(160), nullable=True)
    description = db.Column(db.Text, nullable=True)
    button_text = db.Column(db.String(80), default='Shop the Deal')
    button_link = db.Column(db.String(260), default='/products')
    badge_text  = db.Column(db.String(90), nullable=True)
    bg_color    = db.Column(db.String(40), default='blue')
    image_url   = db.Column(db.String(300), nullable=True)
    is_active   = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
