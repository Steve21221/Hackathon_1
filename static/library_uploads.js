(function () {
  function formatFileList(files) {
    return Array.from(files).map(function (file) { return file.name; });
  }

  function updateCard(input) {
    var card = input.closest('.reference-choice');
    if (!card) return;

    var files = formatFileList(input.files || []);
    var summary = card.querySelector('[data-file-summary]');
    var list = card.querySelector('[data-file-list]');

    card.classList.toggle('has-files', files.length > 0);
    if (summary) {
      summary.textContent = files.length ? files.length + ' file' + (files.length > 1 ? 's' : '') + ' selected' : 'No files selected yet';
    }
    if (list) {
      list.textContent = '';
      files.forEach(function (name) {
        var item = document.createElement('span');
        item.className = 'selected-file-name';
        item.textContent = name;
        list.appendChild(item);
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.reference-choice input[type="file"][multiple]').forEach(function (input) {
      input.addEventListener('change', function () { updateCard(input); });
      updateCard(input);
    });
  });
}());
