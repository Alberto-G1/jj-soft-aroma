from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from datetime import datetime, timezone
from models import db, Product, Category, Order, OrderItem, Offer
import logging

logger = logging.getLogger(__name__)
customer_bp = Blueprint('customer', __name__)

def get_cart():
    cart = session.get('cart', {})
    normalized_cart = {}

    for product_id, item in cart.items():
        try:
            normalized_cart[str(product_id)] = {
                'name': item.get('name', ''),
                'price': float(item.get('price', 0) or 0),
                'quantity': int(item.get('quantity', 0) or 0),
                'image': item.get('image', '') or ''
            }
        except (TypeError, ValueError, AttributeError):
            continue

    return normalized_cart

def save_cart(cart):
    session['cart'] = cart
    session.modified = True

def cart_total(cart):
    total = 0
    for product_id, item in cart.items():
        total += float(item.get('price', 0) or 0) * int(item.get('quantity', 0) or 0)
    return total

# ─── HOME ────────────────────────────────────────────────
@customer_bp.route('/')
def home():
    from models import Review
    featured   = Product.query.filter_by(is_featured=True).limit(8).all()
    categories = Category.query.all()
    reviews    = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).limit(6).all()
    offers     = Offer.query.filter_by(is_active=True).order_by(Offer.display_order.asc(), Offer.created_at.desc()).limit(2).all()
    return render_template('customer/home.html', featured=featured, categories=categories, reviews=reviews, offers=offers)

# ─── PRODUCTS ────────────────────────────────────────────
@customer_bp.route('/products')
def products():
    category_slug = request.args.get('category')
    search        = request.args.get('search', '')
    query         = Product.query

    if category_slug:
        cat   = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    all_products = query.order_by(Product.created_at.desc()).all()
    categories   = Category.query.all()
    return render_template('customer/products.html',
        products=all_products,
        categories=categories,
        selected_category=category_slug,
        search=search
    )

# ─── PRODUCT DETAIL ──────────────────────────────────────
@customer_bp.route('/product/<int:id>')
def product_detail(id):
    product  = Product.query.get_or_404(id)
    related  = Product.query.filter_by(category_id=product.category_id).filter(Product.id != id).limit(4).all()
    return render_template('customer/product_detail.html', product=product, related=related)

# ─── CART ────────────────────────────────────────────────
@customer_bp.route('/cart')
def cart():
    from models import Review
    cart     = get_cart()
    total    = cart_total(cart)
    featured = []
    if not cart:
        featured = Product.query.filter_by(is_featured=True).limit(4).all()
    return render_template('customer/cart.html', cart=cart, total=total, featured=featured)

@customer_bp.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product  = Product.query.get_or_404(product_id)
    cart     = get_cart()
    pid      = str(product_id)
    quantity = int(request.form.get('quantity', 1))

    # use sale price if active
    effective_price = product.sale_price if product.sale_price and product.sale_price < product.price else product.price

    if pid in cart:
        cart[pid]['quantity'] += quantity
    else:
        cart[pid] = {
            'name':     product.name,
            'price':    float(effective_price),
            'quantity': int(quantity),
            'image':    product.image_url or ''
        }
    save_cart(cart)
    flash(f'{product.name} added to cart!', 'success')
    return redirect(request.referrer or url_for('customer.products'))

@customer_bp.route('/cart/remove/<product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = get_cart()
    if product_id in cart:
        del cart[product_id]
    save_cart(cart)
    return redirect(url_for('customer.cart'))

@customer_bp.route('/cart/update/<product_id>', methods=['POST'])
def update_cart(product_id):
    cart     = get_cart()
    quantity = int(request.form.get('quantity', 1))
    if product_id in cart:
        if quantity <= 0:
            del cart[product_id]
        else:
            cart[product_id]['quantity'] = quantity
    save_cart(cart)
    return redirect(url_for('customer.cart'))

# ─── CHECKOUT ────────────────────────────────────────────
@customer_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    from models import Customer, Notification, StoreSetting
    from utils import send_sms, create_notification
    cart  = get_cart()
    if not cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('customer.cart'))
    total = cart_total(cart)

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        phone    = request.form.get('phone', '').strip()
        location = request.form.get('location', '').strip()
        delivery_notes = request.form.get('delivery_notes', '').strip()

        # ── input validation ──
        if not name or not phone or not location:
            flash('Please fill in your name, phone number, and delivery location.', 'danger')
            return render_template('customer/checkout.html', cart=cart, total=total)

        try:
            # ── save or update customer ──
            customer = Customer.query.filter_by(phone=phone).first()
            if not customer:
                customer = Customer(name=name, phone=phone, location=location)
                db.session.add(customer)
            else:
                customer.name     = name
                customer.location = location

            # ── save order ──
            order = Order(
                customer_name=name,
                phone=phone,
                location=location,
                delivery_notes=delivery_notes,
                total_price=total,
                payment_method='whatsapp',
                status='pending'
            )
            db.session.add(order)
            db.session.flush()

            for pid, item in cart.items():
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=int(pid),
                    quantity=int(item.get('quantity', 0) or 0),
                    unit_price=float(item.get('price', 0) or 0)
                )
                db.session.add(order_item)
                product = Product.query.get(int(pid))
                if product:
                    product.stock = max(0, product.stock - int(item.get('quantity', 0) or 0))

            db.session.commit()

            # ── in-app notification ──
            item_count = sum(i['quantity'] for i in cart.values())
            create_notification(
                db, Notification,
                title=f'New Order #{order.id} from {name}',
                message=f'{item_count} item(s) — UGX {total:,.0f} — {location}',
                icon='bag-check',
                color='success',
                link=f'/admin/orders/{order.id}'
            )

            # ── SMS notification ──
            settings = StoreSetting.query.first()
            if settings and settings.sms_notifications:
                items_text = ', '.join([f"{i['name']} x{i['quantity']}" for i in cart.values()])
                sms_msg = (
                    f"New J&J Order #{order.id}!\n"
                    f"Customer: {name}\n"
                    f"Phone: {phone}\n"
                    f"Location: {location}\n"
                    f"Items: {items_text}\n"
                    f"Total: UGX {total:,.0f}"
                )
                send_sms(sms_msg, settings.notify_phone)

            session['cart'] = {}

            whatsapp_msg = f"Hello J&J Soft Aroma!%0A%0ANew Order from {name}%0APhone: {phone}%0ALocation: {location}%0A%0AItems:%0A"
            for pid, item in cart.items():
                whatsapp_msg += f"- {item['name']} x{int(item.get('quantity', 0) or 0)} @ UGX {float(item.get('price', 0) or 0):,.0f}%0A"
            if delivery_notes:
                whatsapp_msg += f"%0ADelivery Notes: {delivery_notes}"
            whatsapp_msg += f"%0ATotal: UGX {total:,.0f}%0A%0AOrder ID: #{order.id}"
            whatsapp_url = f"https://wa.me/256760868005?text={whatsapp_msg}"

            return redirect(url_for('customer.order_confirmation',
                                    order_id=order.id, wa=whatsapp_url))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Checkout error: {e}")
            flash('Something went wrong while placing your order. Please try again.', 'danger')
            return render_template('customer/checkout.html', cart=cart, total=total)

    return render_template('customer/checkout.html', cart=cart, total=total)

    
# ─── ORDER CONFIRMATION ──────────────────────────────────
@customer_bp.route('/order-confirmation/<int:order_id>')
def order_confirmation(order_id):
    order        = Order.query.get_or_404(order_id)
    whatsapp_url = request.args.get('wa', '')
    return render_template('customer/order_confirmation.html', order=order, whatsapp_url=whatsapp_url)

# ─── ABOUT ───────────────────────────────────────────────
@customer_bp.route('/about')
def about():
    return render_template('customer/about.html')

# ─── FAQ ─────────────────────────────────────────────────
@customer_bp.route('/faq')
def faq():
    return render_template('customer/faq.html')

# ─── CONTACT ─────────────────────────────────────────────
@customer_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name    = request.form.get('name')
        email   = request.form.get('email')
        subject = request.form.get('subject', 'General Enquiry')
        message = request.form.get('message')

        # always send to whatsapp as backup
        wa_text = (
            f"Hello J&J Soft Aroma!%0A"
            f"My name is {name}.%0A"
            f"Email: {email}%0A"
            f"Subject: {subject}%0A%0A"
            f"Message:%0A{message}"
        )
        whatsapp_url = f"https://wa.me/256763085855?text={wa_text}"

        # try sending email
        try:
            import smtplib
            import os
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            mail_user = os.getenv('MAIL_USERNAME')
            mail_pass = os.getenv('MAIL_PASSWORD')

            if mail_user and mail_pass:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = f"[J&J Soft Aroma] {subject} — from {name}"
                msg['From']    = mail_user
                msg['To']      = mail_user
                msg['Reply-To']= email

                html_body = f"""
                <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
                  <div style="background:#1a3c5e;padding:20px;border-radius:8px 8px 0 0;">
                    <h2 style="color:#fff;margin:0;">New Contact Message</h2>
                    <p style="color:#90caf9;margin:4px 0 0;">J&J Soft Aroma Website</p>
                  </div>
                  <div style="background:#f9f9f9;padding:24px;border:1px solid #eee;">
                    <table style="width:100%;border-collapse:collapse;">
                      <tr>
                        <td style="padding:8px 0;color:#666;width:120px;">Name</td>
                        <td style="padding:8px 0;font-weight:bold;">{name}</td>
                      </tr>
                      <tr>
                        <td style="padding:8px 0;color:#666;">Email</td>
                        <td style="padding:8px 0;">
                          <a href="mailto:{email}">{email}</a>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:8px 0;color:#666;">Subject</td>
                        <td style="padding:8px 0;">{subject}</td>
                      </tr>
                    </table>
                    <hr style="border:1px solid #eee;margin:16px 0;">
                    <p style="color:#666;margin-bottom:8px;">Message:</p>
                    <div style="background:#fff;padding:16px;border-radius:6px;
                                border-left:4px solid #4caf88;line-height:1.7;">
                      {message.replace(chr(10), '<br>')}
                    </div>
                  </div>
                  <div style="background:#eee;padding:12px;text-align:center;
                              border-radius:0 0 8px 8px;font-size:0.8rem;color:#999;">
                    J&J Soft Aroma — Built by GGT Grand Grande Technologies
                  </div>
                </div>
                """

                msg.attach(MIMEText(html_body, 'html'))

                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(mail_user, mail_pass)
                    server.sendmail(mail_user, mail_user, msg.as_string())

                flash('Message sent! We will get back to you soon.', 'success')
            else:
                flash('Message received! Redirecting to WhatsApp to confirm.', 'info')
                return redirect(whatsapp_url)

        except Exception as e:
            import logging
            logging.getLogger('routes.customer_routes').error(
                f"Contact email error: {e}"
            )
            flash('Message received! Redirecting you to WhatsApp.', 'info')
            return redirect(whatsapp_url)

        return redirect(url_for('customer.contact'))


    from models import StoreSetting, ContactMessage
    from utils import send_contact_email

    store = StoreSetting.query.first()
    if not store:
        store = StoreSetting()
        db.session.add(store)
        db.session.commit()

    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        contact = request.form.get('contact', '').strip()
        subject = request.form.get('subject', 'General Enquiry').strip()
        message = request.form.get('message', '').strip()

        if not name or not contact or not message:
            flash('Please fill in your name, contact, and message.', 'danger')
            return render_template('customer/contact.html', store=store)

        recipient_email = (store.email or 'nuwarindaalbertgrande@gmail.com').strip()
        contact_log = ContactMessage(
            name=name,
            contact=contact,
            subject=subject,
            message=message,
            recipient_email=recipient_email,
            delivery_status='pending'
        )
        db.session.add(contact_log)
        db.session.commit()

        try:
            send_contact_email(recipient_email, name, contact, subject, message)
            contact_log.delivery_status = 'sent'
            contact_log.sent_at = datetime.now(timezone.utc)
            db.session.commit()
            flash('Your message has been emailed successfully. We will reply soon.', 'success')
        except Exception as e:
            contact_log.delivery_status = 'failed'
            contact_log.error_message = str(e)[:300]
            db.session.commit()
            logger.error(f"Contact email error: {e}")
            flash('We saved your message, but the email delivery failed. Please try WhatsApp as well.', 'warning')

        return redirect(url_for('customer.contact'))

    return render_template('customer/contact.html', store=store)

# ─── REVIEWS ─────────────────────────────────────────────
@customer_bp.route('/submit-review', methods=['POST'])
def submit_review():
    from models import Review
    name    = request.form.get('name')
    role    = request.form.get('role')
    rating  = int(request.form.get('rating', 5))
    message = request.form.get('message')

    if name and message:
        review = Review(name=name, role=role, rating=rating, message=message)
        db.session.add(review)
        db.session.commit()
        flash('Thank you for your review! It will appear after approval.', 'success')
    else:
        flash('Please fill in all required fields.', 'danger')

    return redirect(request.referrer or url_for('customer.home'))