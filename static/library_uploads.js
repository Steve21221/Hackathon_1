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

    function selectedMentorValue(form) {
      var radio = form && form.querySelector('input[name="selected_prompt_mentor"]:checked');
      return radio ? radio.value : '';
    }

    function updatePromptMentorCards(form) {
      if (!form) return;
      form.querySelectorAll('[data-prompt-mentor-card]').forEach(function (card) {
        var radio = card.querySelector('input[name="selected_prompt_mentor"]');
        var isSelected = Boolean(radio && radio.checked);
        card.classList.toggle('selected', isSelected);
        card.setAttribute('aria-checked', isSelected ? 'true' : 'false');
      });
    }

    function toggleMentorCreator(form) {
      if (!form) return;
      var creator = form.querySelector('[data-mentor-creator]');
      if (!creator) return;
      var input = creator.querySelector('input[name="prompt_mentor_name"]');
      var hasSelectedMentor = Boolean(selectedMentorValue(form));

      creator.hidden = hasSelectedMentor;
      if (input) {
        if (hasSelectedMentor) {
          input.removeAttribute('required');
        } else {
          input.setAttribute('required', 'required');
        }
      }
    }

    function toggleDeleteMentorButton(form) {
      if (!form) return;
      var button = form.querySelector('[data-delete-mentor-button]');
      if (button) button.hidden = !selectedMentorValue(form);
    }

    function clearStoredFileDisplays(form) {
      if (!form) return;
      form.querySelectorAll('.stored-file-list').forEach(function (list) {
        list.textContent = '';
        list.hidden = true;
      });
    }

    function handleMentorSelectionChange(input) {
      var form = input.closest('form');
      updatePromptMentorCards(form);
      toggleMentorCreator(form);
      toggleDeleteMentorButton(form);
      var wrapper = input.closest('[data-prompt-mentor-cards]');
      var libraryUrl = (wrapper && wrapper.getAttribute('data-mentor-home-url')) || '/prompt-library';
      if (input.value) {
        window.location.assign(libraryUrl + '?prompt_mentor=' + encodeURIComponent(input.value));
        return;
      }
      clearStoredFileDisplays(form);
      if (window.history && window.history.replaceState) {
        window.history.replaceState(null, '', libraryUrl);
      }
    }

    document.querySelectorAll('input[name="selected_prompt_mentor"]').forEach(function (input) {
      var form = input.closest('form');
      input.addEventListener('change', function () { handleMentorSelectionChange(input); });
      updatePromptMentorCards(form);
      toggleMentorCreator(form);
      toggleDeleteMentorButton(form);
    });
  });
}());
