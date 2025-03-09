// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
  // Ensure modals are hidden by default
  const registrationModal = document.getElementById("registerModal");
  const loginModal = document.getElementById("loginModal");
  if (registrationModal) registrationModal.style.display = "none";
  if (loginModal) loginModal.style.display = "none";
});

function openModal() {
  const registrationModal = document.getElementById("registerModal");
  if (registrationModal) {
    registrationModal.style.display = "flex";
  }
}

function closeModal() {
  const registrationModal = document.getElementById("registerModal");
  if (registrationModal) {
    registrationModal.style.display = "none";
  }
}

function showLoginModal() {
  closeModal();
  const loginModal = document.getElementById("loginModal");
  if (loginModal) {
    loginModal.style.display = "flex";
  }
}

function closeLoginModal() {
  const loginModal = document.getElementById("loginModal");
  if (loginModal) {
    loginModal.style.display = "none";
  }
}

function openRegistrationModalFromLogin() {
  closeLoginModal();
  openModal();
}

function toggleAccountDetails(event) {
  event.preventDefault();
  const accountDetails = document.getElementById("accountDetails");
  if (accountDetails) {
    accountDetails.style.display = accountDetails.style.display === "none" ? "block" : "none";
  }
}

function toggleProfileDetails(event) {
  event.preventDefault();
  const profileDetails = document.getElementById("profileDetails");
  if (profileDetails) {
    profileDetails.style.display = profileDetails.style.display === "none" ? "block" : "none";
  }
}

function logout() {
  fetch('/logout').then(() => {
    window.location.reload();
  });
}

// Close modals when clicking outside
window.onclick = function(event) {
  const registrationModal = document.getElementById("registerModal");
  const loginModal = document.getElementById("loginModal");
  const accountDetails = document.getElementById("accountDetails");
  
  if (event.target === registrationModal) {
    closeModal();
  }
  if (event.target === loginModal) {
    closeLoginModal();
  }
  if (accountDetails && !event.target.matches('.account-initials') && 
      !event.target.matches('a[onclick="toggleProfileDetails(event)"]')) {
    accountDetails.style.display = "none";
  }
};