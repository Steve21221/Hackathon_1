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

    function toggleMentorCreator(select) {
      var form = select.closest('form');
      if (!form) return;
      var creator = form.querySelector('[data-mentor-creator]');
      if (!creator) return;
      var input = creator.querySelector('input[name="prompt_mentor_name"]');

      creator.hidden = Boolean(select.value);
      if (input) {
        if (select.value) {
          input.removeAttribute('required');
        } else {
          input.setAttribute('required', 'required');
        }
      }
    }

    function toggleDeleteMentorButton(select) {
      var form = select.closest('form');
      if (!form) return;
      var button = form.querySelector('[data-delete-mentor-button]');
      if (!button) return;
      button.hidden = !select.value;
    }

    function clearStoredFileDisplays(form) {
      if (!form) return;
      form.querySelectorAll('.stored-file-list').forEach(function (list) {
        list.textContent = '';
        list.hidden = true;
      });
    }

    function handleMentorSelectionChange(select) {
      toggleMentorCreator(select);
      toggleDeleteMentorButton(select);
      var form = select.closest('form');
      if (select.value) {
        var homeUrl = select.getAttribute('data-mentor-home-url') || '/';
        window.location.assign(homeUrl + '?prompt_mentor=' + encodeURIComponent(select.value) + '#prompt-library');
        return;
      }
      clearStoredFileDisplays(form);
      if (window.history && window.history.replaceState) {
        window.history.replaceState(null, '', (select.getAttribute('data-mentor-home-url') || '/') + '#prompt-library');
      }
    }

    document.querySelectorAll('[data-selected-mentor]').forEach(function (select) {
      select.addEventListener('change', function () { handleMentorSelectionChange(select); });
      toggleMentorCreator(select);
      toggleDeleteMentorButton(select);
    });
  });
}());
