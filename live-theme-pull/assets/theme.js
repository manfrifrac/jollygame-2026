document.addEventListener('DOMContentLoaded', function() {
  // Login Modal Logic
  const loginModal = document.getElementById('LoginModal');
  const openLoginBtn = document.getElementById('OpenLoginModal');
  const closeLoginBtn = document.getElementById('CloseLoginModal');
  const switchAuthBtn = document.getElementById('SwitchAuthMode');
  const loginView = document.getElementById('LoginView');
  const registerView = document.getElementById('RegisterView');
  const switchText = document.getElementById('SwitchText');

  if (openLoginBtn) {
    openLoginBtn.addEventListener('click', () => {
      loginModal.classList.remove('hidden');
      loginModal.classList.add('flex');
    });
  }

  if (closeLoginBtn) {
    closeLoginBtn.addEventListener('click', () => {
      loginModal.classList.add('hidden');
      loginModal.classList.remove('flex');
    });
  }

  if (switchAuthBtn) {
    switchAuthBtn.addEventListener('click', () => {
      if (loginView.classList.contains('hidden')) {
        loginView.classList.remove('hidden');
        registerView.classList.add('hidden');
        switchText.textContent = 'Non sei ancora registrato?';
        switchAuthBtn.textContent = 'Registrati Ora';
      } else {
        loginView.classList.add('hidden');
        registerView.classList.remove('hidden');
        switchText.textContent = 'Hai già un account?';
        switchAuthBtn.textContent = 'Vai al Login';
      }
    });
  }

  // Mobile Menu Logic
  const mobileMenuToggle = document.getElementById('MobileMenuToggle');
  const mobileMenu = document.getElementById('MobileMenu');

  if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener('click', () => {
      mobileMenu.classList.toggle('hidden');
    });
  }
});
