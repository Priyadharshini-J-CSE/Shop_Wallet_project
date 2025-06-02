/**
 * ShopWallet - Shortened JavaScript
 * Handles cart management, payment processing, and UI interactions
 */

// Cart Management - Using Django session-based cart
// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeCurrentPage();
});

// Cart Operations
function addToCart(id) {
    try {
        // Use Django's server-side cart management
        window.location.href = `/store/add/${id}/`;
    } catch (error) {
        console.error('Error adding item to cart:', error);
        showToast('Error adding item to cart. Please try again.', 'error');
    }
}

function removeFromCart(productId) {
    try {
        // Use Django's server-side cart management
        window.location.href = `/store/remove/${productId}/`;
    } catch (error) {
        console.error('Error removing item from cart:', error);
        showToast('Error removing item from cart. Please try again.', 'error');
    }
}

function updateQuantity(productId, change) {
    try {
        // Create a form to send POST request to Django
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/store/update/${productId}/`;

        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (csrfToken) {
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = csrfToken;
            form.appendChild(csrfInput);
        }

        // Add change value
        const changeInput = document.createElement('input');
        changeInput.type = 'hidden';
        changeInput.name = 'change';
        changeInput.value = change;
        form.appendChild(changeInput);

        document.body.appendChild(form);
        form.submit();
    } catch (error) {
        console.error('Error updating quantity:', error);
        showToast('Error updating quantity. Please try again.', 'error');
    }
}

function clearCart() {
    try {
        // Use Django's server-side cart management
        window.location.href = `/store/clear/`;
    } catch (error) {
        console.error('Error clearing cart:', error);
        showToast('Error clearing cart. Please try again.', 'error');
    }
}

// UI Rendering Functions
function loadCartItems() {
    const itemsContainer = document.getElementById("cart-items");
    if (!itemsContainer) return;

    itemsContainer.innerHTML = '';

    if (cart.length === 0) {
        itemsContainer.innerHTML = '<li class="empty-cart-message">Your cart is empty</li>';
        updateCartTotal(0);
        return;
    }

    let total = 0;

    cart.forEach((item, index) => {
        const cartItem = document.createElement("li");
        cartItem.className = "cart-item";
        cartItem.innerHTML = `
            <div class="cart-item-info">
                <img src="${escapeHTML(item.img)}" alt="${escapeHTML(item.name)}" class="cart-item-thumbnail">
                <span class="cart-item-name">${escapeHTML(item.name)}</span>
            </div>
            <span class="cart-item-price">₹${item.price.toFixed(2)}</span>
            <button type="button" class="cart-item-remove" aria-label="Remove ${escapeHTML(item.name)}" onclick="removeFromCart(${index})">
                <i class="fas fa-times"></i>
            </button>
        `;
        itemsContainer.appendChild(cartItem);
        total += item.price;
    });

    updateCartTotal(total);
}

function updateCartTotal(total) {
    const totalElement = document.getElementById("total");
    if (totalElement) totalElement.textContent = total.toFixed(2);

    const totalField = document.getElementById("cart-total-field");
    if (totalField) totalField.value = total.toFixed(2);
}

function loadCartSummary() {
    const summaryItems = document.getElementById('summary-items');
    if (!summaryItems) return;

    if (cart.length === 0) {
        summaryItems.innerHTML = '<p class="empty-summary">No items in cart</p>';
        updatePaymentTotals(0);
        return;
    }

    let html = '';
    let total = 0;

    cart.forEach(item => {
        html += `
            <div class="summary-item">
                <span class="summary-item-name">${escapeHTML(item.name)}</span>
                <span class="summary-item-price">₹${item.price.toFixed(2)}</span>
            </div>
        `;
        total += item.price;
    });

    summaryItems.innerHTML = html;
    updatePaymentTotals(total);
}

function updatePaymentTotals(total) {
    document.querySelectorAll('#order-total, #payment-amount').forEach(el => {
        el.textContent = total.toFixed(2);
    });

    const cartTotalField = document.getElementById('cart-total-field');
    if (cartTotalField) cartTotalField.value = total.toFixed(2);

    updatePaymentButtonStatus();
}

// Payment Functions
function updatePaymentButtonStatus() {
    const paymentMethod = document.getElementById('payment-method');
    const paymentButton = document.getElementById('payment-button');

    if (!paymentMethod || !paymentButton) return;

    if (paymentMethod.value === 'wallet') {
        const cartTotal = parseFloat(document.getElementById('cart-total-field').value);
        const walletBalanceElement = document.querySelector('.balance-amount');

        if (walletBalanceElement) {
            const walletBalance = parseFloat(walletBalanceElement.textContent.replace('₹', ''));

            if (cartTotal > walletBalance) {
                paymentButton.disabled = true;
                paymentButton.classList.add('disabled');
                return;
            }
        }
    }

    paymentButton.disabled = false;
    paymentButton.classList.remove('disabled');
}

function handlePaymentMethodChange(select) {
    const methodDetails = document.getElementById('payment-method-details');
    if (!methodDetails) return;

    const method = select.value;
    const cartTotal = parseFloat(document.getElementById('cart-total-field')?.value || 0);

    let walletBalance = 0;
    const walletBalanceElement = document.querySelector('.balance-amount');
    if (walletBalanceElement) {
        walletBalance = parseFloat(walletBalanceElement.textContent.replace('₹', ''));
    }

    const templates = {
        wallet: `
            <div class="wallet-payment-info">
                <p><i class="fas fa-info-circle"></i> Payment will be deducted from your wallet balance.</p>
                ${cartTotal > walletBalance ?
                '<p class="insufficient-funds"><i class="fas fa-exclamation-triangle"></i> Insufficient wallet balance! Please recharge or select another payment method.</p>' : ''}
            </div>
        `,
        upi: `
            <div class="form-group">
                <label for="upi-id"><i class="fas fa-at"></i> UPI ID</label>
                <input type="text" id="upi-id" name="upi_id" pattern="[a-zA-Z0-9_.]+@[a-zA-Z0-9]+"
                    placeholder="yourname@bankname" required aria-describedby="upi-format-help">
                <small id="upi-format-help" class="form-help">Format: username@bankname</small>
            </div>
            <div class="payment-security">
                <i class="fas fa-shield-alt"></i> Your payment details are securely encrypted
            </div>
        `,
        card: `
            <div class="form-group">
                <label for="card-number"><i class="far fa-credit-card"></i> Card Number</label>
                <input type="text" id="card-number" name="card_number"
                    pattern="[0-9]{4}\\s?[0-9]{4}\\s?[0-9]{4}\\s?[0-9]{4}"
                    placeholder="1234 5678 9012 3456" maxlength="19"
                    required aria-describedby="card-format-help"
                    oninput="formatCardNumber(this)">
                <small id="card-format-help" class="form-help">16 digits, spaces will be added automatically</small>
            </div>
            <div class="form-row">
                <div class="form-group half">
                    <label for="expiry"><i class="far fa-calendar-alt"></i> Expiry</label>
                    <input type="text" id="expiry" name="expiry"
                        pattern="(0[1-9]|1[0-2])\\/([0-9]{2})"
                        placeholder="MM/YY" maxlength="5"
                        required aria-describedby="expiry-format-help"
                        oninput="formatExpiry(this)">
                    <small id="expiry-format-help" class="form-help">Format: MM/YY</small>
                </div>
                <div class="form-group half">
                    <label for="cvv"><i class="fas fa-lock"></i> CVV</label>
                    <input type="password" id="cvv" name="cvv"
                        pattern="[0-9]{3,4}" placeholder="123"
                        maxlength="4" required aria-describedby="cvv-format-help">
                    <small id="cvv-format-help" class="form-help">3-4 digits on back of card</small>
                </div>
            </div>
            <div class="form-group">
                <label for="card-name"><i class="far fa-user"></i> Cardholder Name</label>
                <input type="text" id="card-name" name="card_name"
                    placeholder="John Doe" required>
            </div>
            <div class="payment-security">
                <i class="fas fa-shield-alt"></i> Your payment details are securely encrypted
            </div>
        `,
        netbanking: `
            <div class="form-group">
                <label for="bank-select"><i class="fas fa-university"></i> Select Bank</label>
                <select id="bank-select" name="bank" required>
                    <option value="">-- Select Bank --</option>
                    <option value="sbi">State Bank of India</option>
                    <option value="hdfc">HDFC Bank</option>
                    <option value="icici">ICICI Bank</option>
                    <option value="axis">Axis Bank</option>
                    <option value="pnb">Punjab National Bank</option>
                    <option value="bob">Bank of Baroda</option>
                    <option value="other">Other Bank</option>
                </select>
            </div>
            <div class="payment-security">
                <i class="fas fa-shield-alt"></i> You will be redirected to your bank's secure payment page
            </div>
        `
    };

    methodDetails.innerHTML = templates[method] || '';
    updatePaymentButtonStatus();
}

// Input Formatting Functions
function formatCardNumber(input) {
    let value = input.value.replace(/\D/g, '');
    let formattedValue = '';

    for (let i = 0; i < value.length; i++) {
        if (i > 0 && i % 4 === 0) formattedValue += ' ';
        formattedValue += value[i];
    }

    input.value = formattedValue;
}

function formatExpiry(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length > 2) {
        input.value = value.substring(0, 2) + '/' + value.substring(2);
    } else {
        input.value = value;
    }
}

// Form Validation Functions
function validatePaymentForm(event) {
    const method = document.getElementById('payment-method').value;

    if (method === 'wallet') {
        const cartTotal = parseFloat(document.getElementById('cart-total-field').value);
        const walletBalanceElement = document.querySelector('.balance-amount');

        if (walletBalanceElement) {
            const walletBalance = parseFloat(walletBalanceElement.textContent.replace('₹', ''));

            if (cartTotal > walletBalance) {
                event.preventDefault();
                showToast('Insufficient wallet balance. Please recharge or select another payment method.', 'error');
                return false;
            }
        }
    } else if (method === 'card') {
        // Basic card validation
        const cardNumber = document.getElementById('card-number').value.replace(/\s/g, '');
        if (cardNumber.length !== 16 || !/^\d+$/.test(cardNumber)) {
            event.preventDefault();
            showToast('Please enter a valid 16-digit card number', 'error');
            return false;
        }

        const expiryField = document.getElementById('expiry');
        if (expiryField) {
            const expiry = expiryField.value;
            const currentDate = new Date();
            const currentYear = currentDate.getFullYear() % 100;
            const currentMonth = currentDate.getMonth() + 1;

            const [expiryMonth, expiryYear] = expiry.split('/').map(part => parseInt(part, 10));

            if (isNaN(expiryMonth) || isNaN(expiryYear) ||
                expiryMonth < 1 || expiryMonth > 12 ||
                (expiryYear < currentYear || (expiryYear === currentYear && expiryMonth < currentMonth))) {
                event.preventDefault();
                showToast('Card has expired or date is invalid', 'error');
                return false;
            }
        }
    }

    // Show loading state
    const paymentButton = document.getElementById('payment-button');
    if (paymentButton) {
        paymentButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        paymentButton.disabled = true;
    }

    return true;
}

function validateRechargeForm(event) {
    const amountField = document.getElementById('recharge-amount');
    if (!amountField) return true;

    const amount = parseFloat(amountField.value);

    if (isNaN(amount) || amount <= 0) {
        event.preventDefault();
        showToast('Please enter a valid amount greater than 0', 'error');
        return false;
    }

    return true;
}

// Utility Functions
function showToast(message, type = 'success') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById("toast-container");
    if (!toastContainer) {
        toastContainer = document.createElement("div");
        toastContainer.id = "toast-container";
        toastContainer.style.cssText = "position: fixed; bottom: 20px; right: 20px; z-index: 1000;";
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    // Set icon based on type
    let icon = type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle';

    toast.innerHTML = `<i class="fas fa-${icon}"></i><span>${escapeHTML(message)}</span>`;

    toast.style.cssText = `
        background-color: ${type === 'success' ? 'var(--success, #28a745)' :
                           type === 'error' ? 'var(--danger, #dc3545)' :
                           'var(--info, #17a2b8)'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin-top: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        gap: 10px;
        opacity: 0;
        transform: translateY(20px);
        transition: opacity 0.3s ease, transform 0.3s ease;
    `;

    toastContainer.appendChild(toast);

    // Trigger animation
    setTimeout(() => {
        toast.style.opacity = 1;
        toast.style.transform = 'translateY(0)';
    }, 10);

    // Auto-hide toast after 3 seconds
    setTimeout(() => {
        toast.style.opacity = 0;
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.parentNode?.removeChild(toast), 300);
    }, 3000);
}

function toggleHistory() {
    const historyContent = document.getElementById('history-content');
    const historyToggleIcon = document.getElementById('history-toggle-icon');
    const historyToggleBtn = document.getElementById('history-toggle-btn');

    if (!historyContent || !historyToggleIcon || !historyToggleBtn) return;

    const isExpanded = historyToggleBtn.getAttribute('aria-expanded') === 'true';

    historyContent.hidden = isExpanded;
    historyToggleIcon.className = `fas fa-chevron-${isExpanded ? 'down' : 'up'}`;
    historyToggleBtn.setAttribute('aria-expanded', isExpanded ? 'false' : 'true');
}

function loadTransactionHistory() {
    const transactionList = document.getElementById('transaction-list');
    if (!transactionList) return;

    // Sample data - in production this would come from an API
    const transactions = [
        { date: '2025-04-24', description: 'Wallet Recharge', amount: 50, type: 'credit' },
        { date: '2025-04-23', description: 'Purchase: T-Shirt', amount: 15, type: 'debit' }
    ];

    let html = transactions.length === 0 ?
        '<tr><td colspan="3">No transactions found</td></tr>' :
        transactions.map(tx => `
            <tr>
                <td>${tx.date}</td>
                <td>${escapeHTML(tx.description)}</td>
                <td class="amount-${tx.type}">${tx.type === 'credit' ? '+' : '-'}₹${tx.amount.toFixed(2)}</td>
            </tr>
        `).join('');

    transactionList.innerHTML = html;
}

function escapeHTML(str) {
    if (!str || typeof str !== 'string') return '';

    const escapeMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    };

    return str.replace(/[&<>"']/g, match => escapeMap[match]);
}

// Page Initialization
function initializeCurrentPage() {
    // Cart page initialization - Django handles cart data
    if (document.getElementById('cart-items')) {
        // Add event listener for clear cart button
        const clearCartBtn = document.querySelector('a[href*="clear"]');
        if (clearCartBtn) {
            clearCartBtn.addEventListener('click', function(e) {
                e.preventDefault();
                clearCart();
            });
        }
    }

    // Payment page initialization
    if (document.getElementById('summary-items')) {
        const paymentMethodSelect = document.getElementById('payment-method');
        if (paymentMethodSelect) {
            paymentMethodSelect.addEventListener('change', function() {
                handlePaymentMethodChange(this);
            });
            handlePaymentMethodChange(paymentMethodSelect);
        }

        document.getElementById('payment-form')?.addEventListener('submit', validatePaymentForm);
        document.getElementById('recharge-form')?.addEventListener('submit', validateRechargeForm);

        loadTransactionHistory();
    }

    // Products page initialization
    document.querySelectorAll('.add-to-cart-btn').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.id;
            if (productId) addToCart(productId);
        });
    });
}
