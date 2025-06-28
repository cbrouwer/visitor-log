// Toggle the visibility of the add button based on input
function toggleAddButton(input) {
  const button = input.form.querySelector('button[type="submit"]');
  if (input.value.trim() !== '') {
    button.classList.remove('hidden');
    // Pause auto-refresh when starting to type in a new entry
    const dayContainer = input.closest('[hx-trigger]');
    if (dayContainer && window.htmx) {
      htmx.trigger(dayContainer, 'htmx:abort');
      dayContainer._refreshPaused = true;
    }
  } else {
    button.classList.add('hidden');
    // Resume auto-refresh if the field is cleared
    const dayContainer = input.closest('[hx-trigger]');
    if (dayContainer && window.htmx) {
      dayContainer._refreshPaused = false;
      htmx.trigger(dayContainer, 'refresh');
    }
  }
}

// Show the edit form and hide the display
function editVisitor(button) {
  const container = button.closest('.flex-1').parentElement;
  const displayDiv = container.querySelector('.visitor-display');
  const visitorText = displayDiv.querySelector('.whitespace-pre-line').textContent.replace('• ', '').trim();
  const visitorId = button.getAttribute('data-visitor-id');
  const editDiv = container.nextElementSibling;
  
  if (displayDiv && editDiv && editDiv.classList.contains('visitor-edit')) {
    displayDiv.classList.add('hidden');
    editDiv.classList.remove('hidden');
    const textarea = editDiv.querySelector('textarea[name="visitor"]');
    if (textarea) {
      // Pause auto-refresh when starting to edit
      const dayContainer = container.closest('[hx-trigger]');
      if (dayContainer && window.htmx) {
        htmx.trigger(dayContainer, 'htmx:abort');
        dayContainer._refreshPaused = true;
      }
      
      textarea.value = visitorText;
      textarea.focus();
      textarea.select();
    }
  }
}

// Cancel editing and show the display
function cancelEdit(button) {
  const form = button.closest('form');
  const editDiv = form.closest('.visitor-edit');
  const container = editDiv.previousElementSibling;
  const displayDiv = container.querySelector('.visitor-display');
  
  if (editDiv && displayDiv) {
    editDiv.classList.add('hidden');
    displayDiv.classList.remove('hidden');
    
    // Resume auto-refresh when canceling edit
    const dayContainer = container.closest('[hx-trigger]');
    if (dayContainer && window.htmx) {
      dayContainer._refreshPaused = false;
      // Manually trigger a refresh
      htmx.trigger(dayContainer, 'refresh');
    }
  }
}

// Handle form submission to re-enable auto-refresh
document.body.addEventListener('htmx:afterRequest', function(evt) {
  if (evt.detail.successful && evt.detail.requestConfig.verb === 'post') {
    // Find the day container and resume auto-refresh after successful save
    const form = evt.target;
    const dayContainer = form.closest('[hx-trigger]');
    if (dayContainer && window.htmx) {
      dayContainer._refreshPaused = false;
      // Manually trigger a refresh
      htmx.trigger(dayContainer, 'refresh');
    }
  }
});

// Global handler to prevent auto-refresh when editing
document.body.addEventListener('htmx:beforeRequest', function(evt) {
  // Only handle auto-refresh requests (triggered by the timer)
  if (evt.detail.elt && evt.detail.elt.hasAttribute('hx-trigger') && 
      evt.detail.elt.getAttribute('hx-trigger').startsWith('every')) {
    const dayContainer = evt.detail.elt.closest && evt.detail.elt.closest('[hx-trigger]');
    if (dayContainer && dayContainer._refreshPaused) {
      evt.preventDefault();
      return false;
    }
  }
});
