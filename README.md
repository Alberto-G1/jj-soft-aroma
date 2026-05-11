# J-J-Soft-Aroma



# J&J Soft Aroma — Frontend Redesign
## Integration Guide for the Developer

---

## 📁 File Structure

```
jj_soft_aroma/
├── static/
│   ├── css/
│   │   └── style.css          ← All CSS (replace any existing stylesheet)
│   └── js/
│       └── main.js            ← All JavaScript (replace any existing JS file)
│
└── templates/
    ├── base.html              ← Master layout (navbar, bottom nav, footer, loader)
    ├── macros.html            ← Product card macro — import into any template
    ├── 404.html               ← 404 error page
    ├── 500.html               ← 500 error page
    └── customer/
        ├── home.html
        ├── products.html
        ├── product_detail.html
        ├── cart.html
        ├── checkout.html
        ├── order_confirmation.html
        ├── about.html
        ├── faq.html
        └── contact.html
```

---

## ✅ What Was Done

### Design Changes (no functionality touched)
- **New design system** — soft luxury baby brand palette (sky blue, sage green, navy, peach)
- **Page loader** — animated dots loader shown on every page load, auto-hides after content loads
- **Redesigned product cards** — image top, category badge, stock label, sale %, quick WhatsApp share,
  smooth hover effects, add-to-cart circle button
- **Bottom navigation bar** — replaces hamburger on mobile (≤991px). Has Home, Shop, WhatsApp
  centre button, Cart, More. Desktop navbar stays unchanged.
- **All CSS separated** into `static/css/style.css`
- **All JavaScript separated** into `static/js/main.js`
- Bootstrap Icons used throughout (already on CDN in base.html) — Font Awesome removed

### CSS / JS
- The old `<style>` block in the HTML has been fully extracted to `style.css`
- The old `<script>` block has been extracted to `main.js`
- Bootstrap 5.3.2 is still used for grid, accordion, and utilities

---

## 🔌 Template Variables Expected

### base.html
- `session.get('cart', {})` — dict of `{product_id: {name, price, quantity, image}}`
- `request.endpoint` — used for active nav highlighting
- `get_flashed_messages(with_categories=true)` — flash messages

### home.html
- `categories` — list of category objects with `.name`, `.slug`, `.icon_url`
- `featured` — list of Product objects

### products.html
- `products` — list of Product objects
- `categories` — list of category objects
- `search` — current search string (str)
- `selected_category` — current category slug (str or None)

### product_detail.html
- `product` — single Product object with:
  `.id`, `.name`, `.description`, `.price`, `.sale_price`, `.stock`,
  `.image_url`, `.category` (obj with `.name`, `.slug`)
- `related` — list of related Product objects (can be empty)

### cart.html
- `cart` — `session['cart']` dict
- `total` — numeric total
- `featured` — optional list for empty-cart suggestions

### checkout.html
- `cart` — `session['cart']` dict
- `total` — numeric total

### order_confirmation.html
- `order` — Order object with:
  `.id`, `.customer_name`, `.phone`, `.location`, `.total_price`
- `whatsapp_url` — pre-built WA link string (optional, can be built in view)

### about.html, faq.html, contact.html
- No special variables required beyond standard Flask context

---

## 📦 Product Card Macro Usage

In any template, import and call like this:

```jinja2
{% from 'macros.html' import product_card %}

<div class="row g-3">
  {% for product in products %}
    <div class="col-6 col-md-3">
      {{ product_card(product) }}
    </div>
  {% endfor %}
</div>
```

The macro expects the Product object to have:
- `.id`, `.name`, `.price`, `.sale_price`, `.stock`, `.image_url`, `.category`
- Route: `customer.product_detail(id=product.id)`
- Route: `customer.add_to_cart(product_id=product.id)` — POST

---

## 📱 Mobile Bottom Nav Notes

- Visible only on screens ≤ 991px (Bootstrap `d-lg-none`)
- Desktop hamburger is hidden at ≤ 991px (no hamburger on mobile)
- Desktop navbar still shows on lg+ screens
- The centre WhatsApp button is raised above the bar
- Cart badge updates from `session['cart']`
- Active state driven by `request.endpoint`

---

## 🎨 CSS Variables (quick reference)

```css
--sky, --sky-light, --sky-pale    /* blue tones */
--green, --green-light, --green-pale /* sage/green tones */
--navy, --navy-deep               /* dark brand navy */
--cream                           /* page background */
--peach, --peach-mid, --gold      /* warm accents */
--text-dark, --text-mid, --text-soft /* text colours */
--shadow-sm, --shadow-md, --shadow-lg
--radius (18px), --radius-sm (10px), --radius-xl (32px)
--transition
```

---

## 🚀 Quick Start Checklist

- [ ] Copy `static/css/style.css` → your Flask `static/css/`
- [ ] Copy `static/js/main.js`    → your Flask `static/js/`
- [ ] Copy all templates to your Flask `templates/` folder
- [ ] Confirm `url_for('static', filename='css/style.css')` resolves
- [ ] Confirm `url_for('static', filename='js/main.js')` resolves
- [ ] Ensure `session['cart']` structure: `{str(product_id): {name, price, quantity, image}}`
- [ ] Register 404/500 handlers in your Flask app:
  ```python
  @app.errorhandler(404)
  def page_not_found(e): return render_template('404.html'), 404

  @app.errorhandler(500)
  def server_error(e): return render_template('500.html'), 500
  ```
- [ ] WhatsApp number is **+256 760 868 005** — update if different

---

Built with ❤️ by **GGT — Grand Grande Technologies**
dev@grandgrandetechnologies.com