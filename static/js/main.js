document.addEventListener('DOMContentLoaded', () => {
    const menuBtn = document.getElementById('menu-btn');
    const navMenu = document.getElementById('nav-menu');
    const cartItemsEl = document.getElementById('cart-items');
    const cartSubtotalEl = document.getElementById('cart-subtotal');
    const cartTotalEl = document.getElementById('cart-total');
    const cartCountEl = document.getElementById('cart-count');
    const clearCartBtn = document.getElementById('clear-cart');
    const checkoutBtn = document.getElementById('checkout-btn');
    const checkoutNote = document.getElementById('checkout-note');
    const checkoutForm = document.getElementById('checkout-form');
    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    const currency = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    });
    const MAX_CART_QUANTITY = 20;
    let cart = loadCart();
    let checkoutMessageTimeout;

    if (menuBtn && navMenu) {
        menuBtn.addEventListener('click', () => {
            navMenu.classList.toggle('show');
            menuBtn.setAttribute('aria-expanded', navMenu.classList.contains('show') ? 'true' : 'false');
            const icon = menuBtn.querySelector('i');
            if (icon) {
                if (navMenu.classList.contains('show')) {
                    icon.classList.remove('fa-bars');
                    icon.classList.add('fa-times');
                } else {
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            }
        });
    }

    addToCartButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const product = button.closest('[data-product-id]');
            if (!product) {
                return;
            }

            addToCart({
                id: product.dataset.productId,
                name: product.dataset.productName,
                price: Number(product.dataset.productPrice),
            });

            showAddFeedback(button, product);
            flyToCart(button, product);
        });
    });

    if (cartItemsEl) {
        cartItemsEl.addEventListener('click', (event) => {
            const button = event.target.closest('[data-cart-action]');
            if (!button) {
                return;
            }

            updateQuantity(button.dataset.productId, button.dataset.cartAction);
        });
    }

    if (clearCartBtn) {
        clearCartBtn.addEventListener('click', () => {
            cart = [];
            saveCart();
            renderCart();
            setCheckoutMessage('');
        });
    }

    if (checkoutForm) {
        checkoutForm.addEventListener('submit', (event) => {
            event.preventDefault();
            if (!cart.length) {
                return;
            }

            submitCheckout();
        });
    }

    renderCart();

    function addToCart(product) {
        const existingItem = cart.find((item) => item.id === product.id);

        if (existingItem) {
            existingItem.quantity = Math.min(existingItem.quantity + 1, MAX_CART_QUANTITY);
        } else {
            cart.push({ ...product, quantity: 1 });
        }

        saveCart();
        renderCart();
        setCheckoutMessage('');
    }

    function updateQuantity(productId, action) {
        cart = cart
            .map((item) => {
                if (item.id !== productId) {
                    return item;
                }

                const nextQuantity = action === 'increase'
                    ? Math.min(item.quantity + 1, MAX_CART_QUANTITY)
                    : item.quantity - 1;
                return { ...item, quantity: nextQuantity };
            })
            .filter((item) => item.quantity > 0);

        saveCart();
        renderCart();
        setCheckoutMessage('');
    }

    function renderCart() {
        const itemCount = cart.reduce((total, item) => total + item.quantity, 0);

        if (cartCountEl) {
            cartCountEl.textContent = itemCount;
            cartCountEl.classList.remove('cart-count-pop');
            void cartCountEl.offsetWidth;
            cartCountEl.classList.add('cart-count-pop');
        }

        if (!cartItemsEl || !cartSubtotalEl || !cartTotalEl) {
            return;
        }

        const subtotal = cart.reduce((total, item) => total + item.price * item.quantity, 0);

        cartSubtotalEl.textContent = currency.format(subtotal);
        cartTotalEl.textContent = currency.format(subtotal);

        if (checkoutBtn) {
            checkoutBtn.disabled = cart.length === 0;
        }

        if (!cart.length) {
            cartItemsEl.innerHTML = '<p class="empty-cart">Your cart is empty.</p>';
            return;
        }

        cartItemsEl.innerHTML = cart.map((item) => {
            const itemTotal = item.price * item.quantity;

            return `
            <div class="cart-item">
                <div>
                    <p class="cart-item-name">${escapeHtml(item.name)}</p>
                    <p class="cart-item-price">${currency.format(item.price)} each</p>
                    <p class="cart-item-total">${currency.format(itemTotal)} total</p>
                </div>
                <div class="quantity-controls" aria-label="Quantity controls for ${escapeHtml(item.name)}">
                    <button type="button" data-cart-action="decrease" data-product-id="${escapeHtml(item.id)}" aria-label="Decrease ${escapeHtml(item.name)} quantity">-</button>
                    <span>${item.quantity}</span>
                    <button type="button" data-cart-action="increase" data-product-id="${escapeHtml(item.id)}" aria-label="Increase ${escapeHtml(item.name)} quantity" ${item.quantity >= MAX_CART_QUANTITY ? 'disabled' : ''}>+</button>
                </div>
            </div>
        `;
        }).join('');
    }

    function loadCart() {
        try {
            const savedCart = window.localStorage.getItem('llkmusic-cart');
            const parsedCart = savedCart ? JSON.parse(savedCart) : [];
            return Array.isArray(parsedCart)
                ? mergeCartItems(parsedCart.map(normalizeCartItem).filter(Boolean))
                : [];
        } catch (error) {
            return [];
        }
    }

    function mergeCartItems(items) {
        const itemsById = new Map();

        items.forEach((item) => {
            const existingItem = itemsById.get(item.id);
            if (existingItem) {
                existingItem.quantity = Math.min(
                    existingItem.quantity + item.quantity,
                    MAX_CART_QUANTITY
                );
                return;
            }

            itemsById.set(item.id, { ...item });
        });

        return Array.from(itemsById.values());
    }

    function normalizeCartItem(item) {
        if (!item || typeof item !== 'object') {
            return null;
        }

        const id = String(item.id || '').trim();
        const name = String(item.name || '').trim();
        const price = Number(item.price);
        const quantity = Math.trunc(Number(item.quantity));

        if (!id || !name || !Number.isFinite(price) || price < 0 || !Number.isFinite(quantity)) {
            return null;
        }

        return {
            id,
            name,
            price,
            quantity: Math.min(Math.max(quantity, 1), MAX_CART_QUANTITY),
        };
    }

    function saveCart() {
        try {
            window.localStorage.setItem('llkmusic-cart', JSON.stringify(cart));
        } catch (error) {
            return;
        }
    }

    function submitCheckout() {
        if (!checkoutForm.reportValidity()) {
            return;
        }

        const checkoutUrl = checkoutForm.dataset.checkoutUrl;
        const formData = new FormData(checkoutForm);
        const payload = {
            customer: {
                name: formData.get('name'),
                email: formData.get('email'),
                notes: formData.get('notes'),
            },
            items: cart.map((item) => ({
                id: item.id,
                quantity: item.quantity,
            })),
        };

        setCheckoutMessage('Submitting your order...', 'info');
        if (checkoutBtn) {
            checkoutBtn.disabled = true;
        }

        fetch(checkoutUrl, {
            method: 'POST',
            body: JSON.stringify(payload),
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(checkoutForm),
            },
        })
            .then((response) => response.json().then((data) => {
                if (!response.ok) {
                    throw new Error(data.error || 'Checkout failed.');
                }
                return data;
            }))
            .then((data) => {
                cart = [];
                saveCart();
                renderCart();
                checkoutForm.reset();
                setCheckoutMessage(data.message, 'success', 5000);
            })
            .catch((error) => {
                setCheckoutMessage(error.message, 'error', 5000);
                renderCart();
            });
    }

    function setCheckoutMessage(message, type = '', autoClearMs = 0) {
        if (checkoutMessageTimeout) {
            window.clearTimeout(checkoutMessageTimeout);
            checkoutMessageTimeout = null;
        }

        if (checkoutNote) {
            checkoutNote.textContent = message;
            checkoutNote.className = type ? `checkout-note checkout-note-${type}` : 'checkout-note';

            if (message && autoClearMs) {
                checkoutMessageTimeout = window.setTimeout(() => {
                    checkoutNote.textContent = '';
                    checkoutNote.className = 'checkout-note';
                    checkoutMessageTimeout = null;
                }, autoClearMs);
            }
        }
    }

    function getCsrfToken(form) {
        const tokenInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
        if (tokenInput) {
            return tokenInput.value;
        }

        const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, (character) => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;',
        }[character]));
    }

    function showAddFeedback(button, productCard) {
        const originalLabel = button.dataset.originalLabel || button.textContent;
        button.dataset.originalLabel = originalLabel;

        if (button.dataset.feedbackTimeout) {
            window.clearTimeout(Number(button.dataset.feedbackTimeout));
        }

        button.classList.add('is-added');
        button.textContent = 'Added!';

        if (productCard) {
            productCard.classList.remove('product-card--flash');
            void productCard.offsetWidth;
            productCard.classList.add('product-card--flash');
            spawnAddToast(productCard);
        }

        const timeoutId = window.setTimeout(() => {
            button.textContent = button.dataset.originalLabel || originalLabel;
            button.classList.remove('is-added');
            delete button.dataset.feedbackTimeout;
        }, 900);

        button.dataset.feedbackTimeout = String(timeoutId);
    }

    function spawnAddToast(productCard) {
        const existingToast = productCard.querySelector('.add-to-cart-toast');
        if (existingToast) {
            existingToast.remove();
        }

        const toast = document.createElement('div');
        toast.className = 'add-to-cart-toast';
        toast.setAttribute('role', 'status');
        toast.textContent = 'Added to cart';
        productCard.appendChild(toast);

        window.setTimeout(() => {
            toast.classList.add('is-visible');
        }, 10);

        window.setTimeout(() => {
            toast.classList.remove('is-visible');
            window.setTimeout(() => {
                toast.remove();
            }, 240);
        }, 1100);
    }

    function flyToCart(button, productCard) {
        if (!cartCountEl) {
            return;
        }

        const startRect = button.getBoundingClientRect();
        const cartRect = cartCountEl.getBoundingClientRect();
        const flyer = document.createElement('span');
        flyer.className = 'cart-flyer';
        flyer.textContent = '1';
        flyer.setAttribute('aria-hidden', 'true');

        const startX = startRect.left + startRect.width / 2;
        const startY = startRect.top + startRect.height / 2;
        const endX = cartRect.left + cartRect.width / 2;
        const endY = cartRect.top + cartRect.height / 2;
        const translateX = endX - startX;
        const translateY = endY - startY;
        const distance = Math.max(Math.hypot(translateX, translateY), 180);
        const scale = Math.max(0.55, Math.min(1, 180 / distance));

        flyer.style.left = `${startX}px`;
        flyer.style.top = `${startY}px`;
        flyer.style.setProperty('--fly-x', `${translateX}px`);
        flyer.style.setProperty('--fly-y', `${translateY}px`);
        flyer.style.setProperty('--fly-scale', `${scale}`);

        document.body.appendChild(flyer);

        requestAnimationFrame(() => {
            flyer.classList.add('is-flying');
        });

        window.setTimeout(() => {
            flyer.remove();
        }, 900);
    }
});
