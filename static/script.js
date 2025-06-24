// document.addEventListener("DOMContentLoaded", () => {
//   const defaultVisitor = localStorage.getItem("defaultVisitor");
//   if (defaultVisitor) {
//     document.querySelectorAll('input[name="visitor"]').forEach(input => {
//       input.value = defaultVisitor;
//     });
//   }
// });

function getDefaultVisitor(form) {
  const defaultVisitor = localStorage.getItem("defaultVisitor");
  const input = form.querySelector('input[name="visitor"]');
  if (defaultVisitor) {
    input.value = defaultVisitor;
  }
  toggleAddButton(input);
}

function storeDefaultVisitor(form) {
  const input = form.querySelector('input[name="visitor"]');
  if (input && input.value.trim()) {
    localStorage.setItem("defaultVisitor", input.value.trim());
  }
}

function toggleAddButton(input) {
  const button = input.form.querySelector('button');
  if (input.value.trim() !== '') {
    button.classList.remove('hidden');
  } else {
    button.classList.add('hidden');
  }
}
