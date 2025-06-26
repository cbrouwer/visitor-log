// Toggle the visibility of the add button based on input
function toggleAddButton(input) {
  const button = input.form.querySelector('button[type="submit"]');
  if (input.value.trim() !== '') {
    button.classList.remove('hidden');
  } else {
    button.classList.add('hidden');
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
  }
}
