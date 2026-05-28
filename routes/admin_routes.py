from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, AdminUser, Product, Category, Order, OrderItem, Customer, Notification, StoreSetting, Review, ContactMessage, ProductImage, Offer
import bcrypt
import os
import logging
from werkzeug.utils import secure_filename
import uuid
import cloudinary
import cloudinary.uploader

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, folder='images'):
    """Upload file to Cloudinary and return image URL"""
    try:
        # Validate file
        if not file or not allowed_file(file.filename):
            return None

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            folder=f"jj-soft-aroma/{folder}"
        )

        # Return secure Cloudinary URL
        return upload_result.get("secure_url")

    except Exception as e:
        logger.error(f"Cloudinary upload error: {e}")
        return None
    
    
# ─── AUTH ───────────────────────────────────────────────
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = AdminUser.query.filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

# ─── DASHBOARD ──────────────────────────────────────────
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    from models import Review
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import func

    total_products  = Product.query.count()
    total_orders    = Order.query.count()
    pending_orders  = Order.query.filter_by(status='pending').count()
    low_stock       = Product.query.filter(Product.stock < 5).all()
    recent_orders   = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    total_revenue   = db.session.query(func.sum(Order.total_price)).scalar() or 0
    pending_reviews = Review.query.filter_by(is_approved=False).count()
    total_customers = Customer.query.count()

    # ── ORDERS BY DAY for multiple periods ──
    def get_orders_by_day(days):
        result = []
        for i in range(days - 1, -1, -1):
            day   = datetime.now(timezone.utc).date() - timedelta(days=i)
            count = Order.query.filter(
                func.date(Order.created_at) == day
            ).count()
            result.append({
                'date':  day.strftime('%d %b'),
                'count': count
            })
        return result

    orders_by_day = {
        '7':  get_orders_by_day(7),
        '30': get_orders_by_day(30),
        '90': get_orders_by_day(90),
    }

    # ── REVENUE BY DAY for multiple periods ──
    def get_revenue_by_day(days):
        result = []
        for i in range(days - 1, -1, -1):
            day   = datetime.now(timezone.utc).date() - timedelta(days=i)
            total = db.session.query(func.sum(Order.total_price)).filter(
                func.date(Order.created_at) == day
            ).scalar() or 0
            result.append({
                'date':  day.strftime('%d %b'),
                'total': float(total)
            })
        return result

    revenue_by_day = {
        '7':  get_revenue_by_day(7),
        '30': get_revenue_by_day(30),
        '90': get_revenue_by_day(90),
    }

    # ── STATUS COUNTS ──
    statuses     = ['pending', 'confirmed', 'processing', 'delivered', 'cancelled']
    status_counts = []
    for s in statuses:
        count = Order.query.filter_by(status=s).count()
        if count > 0:
            status_counts.append({'status': s.title(), 'count': count})
    if not status_counts:
        status_counts = [{'status': 'No orders', 'count': 1}]

    # ── TOP PRODUCTS ──
    from models import OrderItem
    top = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total')
    ).join(OrderItem, Product.id == OrderItem.product_id)\
     .group_by(Product.id)\
     .order_by(func.sum(OrderItem.quantity).desc())\
     .limit(5).all()
    top_products = [{'name': t[0], 'total': int(t[1])} for t in top] or \
                   [{'name': 'No data', 'total': 0}]

    return render_template('admin/dashboard.html',
        total_products=total_products,
        total_orders=total_orders,
        pending_orders=pending_orders,
        low_stock=low_stock,
        recent_orders=recent_orders,
        total_revenue=total_revenue,
        pending_reviews=pending_reviews,
        total_customers=total_customers,
        orders_by_day=orders_by_day,
        revenue_by_day=revenue_by_day,
        status_counts=status_counts,
        top_products=top_products,
    )

# ─── NOTIFICATIONS ───────────────────────────────────────
@admin_bp.route('/notifications')
@login_required
def notifications():
    all_notifs = Notification.query.order_by(Notification.created_at.desc()).all()
    Notification.query.update({'is_read': True})
    db.session.commit()
    return render_template('admin/notifications.html', notifications=all_notifs)

@admin_bp.route('/notifications/count')
@login_required
def notification_count():
    count = Notification.query.filter_by(is_read=False).count()
    return jsonify({'count': count})

@admin_bp.route('/notifications/delete/<int:id>', methods=['POST'])
@login_required
def delete_notification(id):
    notif = Notification.query.get_or_404(id)
    db.session.delete(notif)
    db.session.commit()
    return redirect(url_for('admin.notifications'))

# ─── PRODUCTS ───────────────────────────────────────────
@admin_bp.route('/products')
@login_required
def products():
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category', '').strip()
    stock_filter = request.args.get('stock', '').strip()
    featured_filter = request.args.get('featured', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    per_page = min(max(per_page, 6), 48)

    query = Product.query

    if search:
        query = query.filter(db.or_(
            Product.name.ilike(f'%{search}%'),
            Product.description.ilike(f'%{search}%')
        ))

    if category_id:
        query = query.filter(Product.category_id == int(category_id))

    if stock_filter == 'low':
        query = query.filter(Product.stock < 5)
    elif stock_filter == 'in_stock':
        query = query.filter(Product.stock >= 5)
    elif stock_filter == 'out':
        query = query.filter(Product.stock <= 0)

    if featured_filter == 'yes':
        query = query.filter(Product.is_featured.is_(True))
    elif featured_filter == 'no':
        query = query.filter(Product.is_featured.is_(False))

    pagination = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        'admin/products.html',
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        filters={
            'search': search,
            'category': category_id,
            'stock': stock_filter,
            'featured': featured_filter,
            'per_page': per_page,
        },
        total_products=Product.query.count()
    )

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    categories = Category.query.all()
    if request.method == 'POST':
        try:
            name        = request.form.get('name')
            price       = request.form.get('price')
            sale_price_raw = request.form.get('sale_price', '').strip()
            sale_price  = float(sale_price_raw) if sale_price_raw else None
            description = request.form.get('description')
            stock       = request.form.get('stock')
            category_id = request.form.get('category_id')
            is_featured = True if request.form.get('is_featured') else False
            image_url   = None
            file = request.files.get('image')
            if file and allowed_file(file.filename):
                image_url = save_file(file, folder='products')
            product = Product(
                name=name, price=float(price), sale_price=sale_price,
                description=description,
                stock=int(stock), category_id=int(category_id) if category_id else None,
                is_featured=is_featured, image_url=image_url
            )
            db.session.add(product)
            db.session.flush()
            
            # Handle multiple product images
            images = request.files.getlist('product_images')
            valid_images = [img for img in images if img and allowed_file(img.filename)]
            for idx, img_file in enumerate(valid_images):
                img_url = save_file(img_file, folder='products')
                product_image = ProductImage(
                    product_id=product.id,
                    image_url=img_url,
                    is_main=(idx == 0),
                    display_order=idx
                )
                db.session.add(product_image)
            
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin.products'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding product: {e}")
            flash('Failed to add product. Please check your inputs.', 'danger')
    return render_template('admin/add_product.html', categories=categories)

@admin_bp.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product    = Product.query.get_or_404(id)
    categories = Category.query.all()
    if request.method == 'POST':
        try:
            product.name        = request.form.get('name')
            product.price       = float(request.form.get('price'))
            sale_price_raw = request.form.get('sale_price', '').strip()
            product.sale_price  = float(sale_price_raw) if sale_price_raw else None
            product.description = request.form.get('description')
            product.stock       = int(request.form.get('stock'))
            product.is_featured = True if request.form.get('is_featured') else False
            cat_id = request.form.get('category_id')
            product.category_id = int(cat_id) if cat_id else None
            file = request.files.get('image')
            if file and allowed_file(file.filename):
                product.image_url = save_file(file, folder='products')
            
            # Handle multiple product images
            images = request.files.getlist('product_images')
            valid_images = [img for img in images if img and allowed_file(img.filename)]
            if valid_images:
                # Delete old images from ProductImage table
                ProductImage.query.filter_by(product_id=product.id).delete()
                for idx, img_file in enumerate(valid_images):
                    img_url = save_file(img_file, folder='products')
                    product_image = ProductImage(
                        product_id=product.id,
                        image_url=img_url,
                        is_main=(idx == 0),
                        display_order=idx
                    )
                    db.session.add(product_image)
            
            db.session.commit()
            flash('Product updated!', 'success')
            return redirect(url_for('admin.products'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error editing product {id}: {e}")
            flash('Failed to update product. Please check your inputs.', 'danger')
    return render_template('admin/edit_product.html', product=product, categories=categories)

@admin_bp.route('/products/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    try:
        if OrderItem.query.filter_by(product_id=product.id).first():
            flash('This product is linked to existing orders, so it was not deleted. Edit stock to 0 instead if you want to stop selling it.', 'warning')
            return redirect(url_for('admin.products'))
        ProductImage.query.filter_by(product_id=product.id).delete()
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting product {id}: {e}')
        flash('Product could not be deleted because it is linked to other records.', 'danger')
    return redirect(url_for('admin.products'))

# ─── CATEGORIES ─────────────────────────────────────────
@admin_bp.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    if request.method == 'POST':
        try:
            name = (request.form.get('name') or '').strip()
            if not name:
                flash('Category name is required.', 'danger')
                return redirect(url_for('admin.categories'))
            slug = name.lower().replace(' ', '-')
            icon_url = None
            file = request.files.get('icon')

            if file and allowed_file(file.filename):
                icon_url = save_file(file, folder='categories')

            if not Category.query.filter_by(slug=slug).first():
                db.session.add(Category(name=name, slug=slug, icon_url=icon_url))
                db.session.commit()
                flash('Category added!', 'success')
            else:
                flash('Category already exists.', 'warning')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding category: {e}")
            flash('Failed to add category. Please try again.', 'danger')
        return redirect(url_for('admin.categories'))

    search = request.args.get('search', '').strip()
    product_filter = request.args.get('product_filter', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    per_page = min(max(per_page, 6), 48)

    query = Category.query
    if search:
        query = query.filter(db.or_(Category.name.ilike(f'%{search}%'), Category.slug.ilike(f'%{search}%')))

    if product_filter == 'has_products':
        query = query.filter(Category.products.any())
    elif product_filter == 'empty':
        query = query.filter(~Category.products.any())

    pagination = query.order_by(Category.name.asc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'admin/categories.html',
        categories=pagination.items,
        pagination=pagination,
        filters={
            'search': search,
            'product_filter': product_filter,
            'per_page': per_page,
        },
        total_categories=Category.query.count()
    )

@admin_bp.route('/categories/edit/<int:id>', methods=['POST'])
@login_required
def edit_category(id):
    cat = Category.query.get_or_404(id)
    try:
        cat.name = request.form.get('name')
        cat.slug = cat.name.lower().replace(' ', '-')
        file = request.files.get('icon')
        if file and allowed_file(file.filename):
            cat.icon_url = save_file(file, folder='categories')
        db.session.commit()
        flash('Category updated!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error editing category {id}: {e}")
        flash('Failed to update category. Please try again.', 'danger')
    return redirect(url_for('admin.categories'))

@admin_bp.route('/categories/delete/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    try:
        Product.query.filter_by(category_id=cat.id).update({'category_id': None})
        db.session.delete(cat)
        db.session.commit()
        flash('Category deleted. Products from this category were moved to Uncategorized.', 'info')
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting category {id}: {e}')
        flash('Category could not be deleted.', 'danger')
    return redirect(url_for('admin.categories'))

# ─── ORDERS ─────────────────────────────────────────────
STATUS_FLOW = ['pending', 'confirmed', 'processing', 'delivered']

@admin_bp.route('/orders')
@login_required
def orders():
    search     = request.args.get('search', '')
    status     = request.args.get('status', '')
    date_filter= request.args.get('date', '')
    page       = request.args.get('page', 1, type=int)
    query      = Order.query

    if search:
        query = query.filter(
            db.or_(Order.customer_name.ilike(f'%{search}%'),
                   Order.phone.ilike(f'%{search}%'))
        )
    if status:
        query = query.filter_by(status=status)
    if date_filter:
        from datetime import datetime as dt
        try:
            d = dt.strptime(date_filter, '%Y-%m-%d')
            query = query.filter(db.func.date(Order.created_at) == d.date())
        except:
            pass

    pagination  = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=10)
    all_orders  = pagination.items
    return render_template('admin/orders.html',
        orders=all_orders,
        pagination=pagination,
        search=search,
        status=status,
        date_filter=date_filter,
        status_flow=STATUS_FLOW
    )

@admin_bp.route('/orders/<int:id>')
@login_required
def order_detail(id):
    order = Order.query.get_or_404(id)
    return render_template('admin/order_detail.html', order=order, status_flow=STATUS_FLOW)

@admin_bp.route('/orders/<int:id>/next-status', methods=['POST'])
@login_required
def next_status(id):
    order = Order.query.get_or_404(id)
    if order.status in STATUS_FLOW:
        idx = STATUS_FLOW.index(order.status)
        if idx < len(STATUS_FLOW) - 1:
            order.status = STATUS_FLOW[idx + 1]
            db.session.commit()
            flash(f'Order status updated to {order.status.title()}.', 'success')
    return redirect(url_for('admin.orders'))

@admin_bp.route('/orders/<int:id>/status', methods=['POST'])
@login_required
def update_order_status(id):
    order        = Order.query.get_or_404(id)
    order.status = request.form.get('status')
    db.session.commit()
    flash('Order status updated.', 'success')
    return redirect(url_for('admin.order_detail', id=id))

@admin_bp.route('/orders/<int:id>/print')
@login_required
def print_order(id):
    order = Order.query.get_or_404(id)
    return render_template('admin/print_receipt.html', order=order)

@admin_bp.route('/orders/<int:id>/delete', methods=['POST'])
@login_required
def delete_order(id):
    order = Order.query.get_or_404(id)
    for item in order.items:
        db.session.delete(item)
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted.', 'info')
    return redirect(url_for('admin.orders'))

# ─── CUSTOMERS ──────────────────────────────────────────
@admin_bp.route('/customers')
@login_required
def customers():
    search = request.args.get('search', '')
    query  = Customer.query
    if search:
        query = query.filter(
            db.or_(Customer.name.ilike(f'%{search}%'),
                   Customer.phone.ilike(f'%{search}%'),
                   Customer.location.ilike(f'%{search}%'))
        )
    all_customers = query.order_by(Customer.created_at.desc()).all()

    # build stats per customer from orders table
    customer_stats = {}
    for c in all_customers:
        orders = Order.query.filter_by(phone=c.phone).all()
        customer_stats[c.id] = {
            'order_count': len(orders),
            'total_spent': sum(o.total_price for o in orders)
        }

    return render_template('admin/customers.html',
        customers=all_customers,
        customer_stats=customer_stats,
        search=search
    )

# ─── REVIEWS ────────────────────────────────────────────
@admin_bp.route('/reviews')
@login_required
def reviews():
    pending  = Review.query.filter_by(is_approved=False).order_by(Review.created_at.desc()).all()
    approved = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', pending=pending, approved=approved)

@admin_bp.route('/reviews/<int:id>/approve', methods=['POST'])
@login_required
def approve_review(id):
    review = Review.query.get_or_404(id)
    review.is_approved = True
    db.session.commit()
    flash('Review approved and is now live.', 'success')
    return redirect(url_for('admin.reviews'))

@admin_bp.route('/reviews/<int:id>/reject', methods=['POST'])
@login_required
def reject_review(id):
    review = Review.query.get_or_404(id)
    db.session.delete(review)
    db.session.commit()
    flash('Review removed.', 'info')
    return redirect(url_for('admin.reviews'))


# ─── OFFERS ─────────────────────────────────────────────
@admin_bp.route('/offers', methods=['GET', 'POST'])
@login_required
def offers():
    if request.method == 'POST':
        try:
            image_url = None
            file = request.files.get('image')
            if file and allowed_file(file.filename):
                image_url = save_file(file, folder='offers')
            offer = Offer(
                title=request.form.get('title'),
                subtitle=request.form.get('subtitle'),
                description=request.form.get('description'),
                badge_text=request.form.get('badge_text'),
                button_text=request.form.get('button_text') or 'Shop the Deal',
                button_link=request.form.get('button_link') or '/products',
                bg_color=request.form.get('bg_color') or 'blue',
                image_url=image_url,
                is_active=True if request.form.get('is_active') else False,
                display_order=int(request.form.get('display_order') or 0)
            )
            db.session.add(offer)
            db.session.commit()
            flash('Offer saved and ready for the homepage.', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error saving offer: {e}')
            flash('Failed to save offer.', 'danger')
        return redirect(url_for('admin.offers'))
    return render_template('admin/offers.html', offers=Offer.query.order_by(Offer.display_order.asc(), Offer.created_at.desc()).all())

@admin_bp.route('/offers/delete/<int:id>', methods=['POST'])
@login_required
def delete_offer(id):
    offer = Offer.query.get_or_404(id)
    db.session.delete(offer)
    db.session.commit()
    flash('Offer deleted.', 'info')
    return redirect(url_for('admin.offers'))

@admin_bp.route('/offers/toggle/<int:id>', methods=['POST'])
@login_required
def toggle_offer(id):
    offer = Offer.query.get_or_404(id)
    offer.is_active = not offer.is_active
    db.session.commit()
    flash('Offer status updated.', 'success')
    return redirect(url_for('admin.offers'))

# ─── SETTINGS ───────────────────────────────────────────
@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    store = StoreSetting.query.first()
    if not store:
        store = StoreSetting()
        db.session.add(store)
        db.session.commit()

    contact_email_count = ContactMessage.query.count()
    contact_sent_count = ContactMessage.query.filter_by(delivery_status='sent').count()
    contact_failed_count = ContactMessage.query.filter_by(delivery_status='failed').count()
    recent_contact_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'store':
            store.store_name              = request.form.get('store_name')
            store.phone                   = request.form.get('phone')
            store.email                   = request.form.get('email')
            store.address                 = request.form.get('address')
            store.currency                = request.form.get('currency')
            store.free_delivery_threshold = float(request.form.get('free_delivery_threshold', 0))
            store.sms_notifications       = True if request.form.get('sms_notifications') else False
            store.notify_phone            = request.form.get('notify_phone')
            db.session.commit()
            flash('Store settings saved!', 'success')

        elif action == 'password':
            new_password     = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            if new_password and new_password == confirm_password:
                hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                current_user.password_hash = hashed.decode('utf-8')
                db.session.commit()
                flash('Password updated successfully!', 'success')
            elif new_password != confirm_password:
                flash('Passwords do not match.', 'danger')

        return redirect(url_for('admin.settings'))

    return render_template(
        'admin/settings.html',
        store=store,
        contact_email_count=contact_email_count,
        contact_sent_count=contact_sent_count,
        contact_failed_count=contact_failed_count,
        recent_contact_messages=recent_contact_messages,
    )