if (!customElements.get('product-form')) {
  customElements.define(
    'product-form',
    class ProductForm extends HTMLElement {
      constructor() {
        super();
        this.form = this.querySelector('form');
        this.form.addEventListener('submit', this.onSubmitHandler.bind(this));
        this.submitButton = this.querySelector('[type="submit"]');
      }

      onSubmitHandler(evt) {
        evt.preventDefault();
        if (this.submitButton.classList.contains('loading')) return;

        this.submitButton.classList.add('loading');
        this.submitButton.setAttribute('aria-disabled', true);

        const loadingSpinner = this.querySelector('.loading__spinner');
        if (loadingSpinner) loadingSpinner.classList.remove('hidden');

        const formData = new FormData(this.form);
        formData.append('sections', 'cart-icon-bubble,cart-notification-product,cart-notification-button');
        formData.append('sections_url', window.location.pathname);

        fetch('/cart/add.js', {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
          },
          body: formData
        })
        .then((response) => response.json())
        .then((response) => {
          if (response.status) {
            alert(response.description || response.message);
            return;
          }
          
          // Redirect to cart instead of just showing notification
          window.location = '/cart';
        })
        .catch((e) => {
          console.error('Add to cart error:', e);
        })
        .finally(() => {
          this.submitButton.classList.remove('loading');
          this.submitButton.removeAttribute('aria-disabled');
          if (loadingSpinner) loadingSpinner.classList.add('hidden');
        });
      }
    }
  );
}
