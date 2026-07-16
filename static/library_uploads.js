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

  function currentWorkingLabel() {
    return document.body.getAttribute('data-working-label') || 'Working';
  }

  function setPageError(message) {
    var notice = document.querySelector('[data-page-error]');
    var text = document.querySelector('[data-page-error-text]');
    if (!notice || !text) return;
    if (!message) {
      notice.hidden = true;
      text.textContent = '';
      return;
    }
    text.textContent = message;
    notice.hidden = false;
    notice.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function animateWorkingLabel(element, baseLabel) {
    if (!element) return function () {};
    var frames = [baseLabel + '.', baseLabel + '..', baseLabel + '...'];
    var index = 0;
    element.textContent = frames[0];
    var timer = window.setInterval(function () {
      index = (index + 1) % frames.length;
      element.textContent = frames[index];
    }, 450);
    return function () {
      window.clearInterval(timer);
    };
  }

  function showFeedbackWorking(label) {
    var panel = document.querySelector('[data-feedback-panel]');
    if (!panel) return function () {};
    var working = panel.querySelector('[data-feedback-working]');
    var content = panel.querySelector('[data-feedback-content]');
    var message = working && working.querySelector('[data-working-message]');
    if (content) content.hidden = true;
    if (working) working.hidden = false;
    panel.classList.add('is-working');
    panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return animateWorkingLabel(message, label || currentWorkingLabel());
  }

  function hideFeedbackWorking() {
    var panel = document.querySelector('[data-feedback-panel]');
    if (!panel) return;
    var working = panel.querySelector('[data-feedback-working]');
    var content = panel.querySelector('[data-feedback-content]');
    if (working) working.hidden = true;
    if (content) content.hidden = false;
    panel.classList.remove('is-working');
  }

  function showPromptsWorking(form, label) {
    var working = form.querySelector('[data-prompts-working]');
    var message = working && working.querySelector('[data-working-message]');
    if (working) working.hidden = false;
    return animateWorkingLabel(message, label || currentWorkingLabel());
  }

  function hidePromptsWorking(form) {
    var working = form && form.querySelector('[data-prompts-working]');
    if (working) working.hidden = true;
  }

  function resetWorkingButton(form) {
    var button = form && form.querySelector('[data-working-button]');
    if (!button) return;
    var label = button.getAttribute('data-default-label') || 'Submit';
    button.removeAttribute('aria-busy');
    button.innerHTML = label + ' <span data-working-arrow>&rarr;</span>';
  }

  function renderPromptResults(data, options) {
    var shouldScroll = !(options && options.scroll === false);
    var section = document.querySelector('[data-prompt-output]');
    var grid = document.querySelector('[data-prompt-grid]');
    var message = document.querySelector('[data-prompt-message]');
    var note = document.querySelector('[data-prompt-output-note]');
    var downloadAll = document.querySelector('[data-prompt-download-all]');
    if (!section || !grid) return;

    section.hidden = !(data.prompt_cards && data.prompt_cards.length);
    if (message) message.textContent = data.prompt_message || 'PI-style prompts ready';
    if (downloadAll) {
      if (data.prompt_download_urls && data.prompt_download_urls.all) {
        downloadAll.href = data.prompt_download_urls.all;
        downloadAll.hidden = false;
      } else {
        downloadAll.hidden = true;
      }
    }
    grid.innerHTML = '';
    (data.prompt_cards || []).forEach(function (card) {
      var article = document.createElement('article');
      article.className = 'prompt-card';
      var preview = card.preview_html || ('<span class="prompt-segment">' + escapeHtml(card.preview || '') + '</span>');
      var href = (data.prompt_download_urls && data.prompt_download_urls[card.mode]) || '#';
      article.innerHTML =
        '<span class="prompt-card-kicker">Reusable prompt</span>' +
        '<h3></h3>' +
        '<p>' + preview + '</p>' +
        '<a class="prompt-download-link" href="' + href + '">Download TXT <span>&darr;</span></a>';
      article.querySelector('h3').textContent = card.label || card.mode;
      grid.appendChild(article);
    });
    if (note) {
      if (data.prompt_output_location) {
        note.innerHTML = 'Saved local TXT files to <code></code>. Regenerating this same PI library and mode updates the existing TXT file.';
        note.querySelector('code').textContent = data.prompt_output_location;
        if (data.prompt_run_location) {
          note.appendChild(document.createTextNode(' Downloadable run copy: '));
          var code = document.createElement('code');
          code.textContent = data.prompt_run_location;
          note.appendChild(code);
          note.appendChild(document.createTextNode('.'));
        }
      } else {
        note.textContent = '';
      }
    }
    if (shouldScroll && data.prompt_cards && data.prompt_cards.length) {
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderFeedbackResult(data) {
    var panel = document.querySelector('[data-feedback-panel]');
    var content = panel && panel.querySelector('[data-feedback-content]');
    var subtitle = document.querySelector('[data-feedback-subtitle]');
    if (!panel || !content) return;
    hideFeedbackWorking();
    content.classList.remove('feedback-content-empty');
    content.innerHTML =
      '<div class="feedback-meta"><span data-feedback-mentor></span><span data-feedback-filename></span></div>' +
      '<details class="feedback-expand" open>' +
      '<summary>Show full feedback</summary>' +
      '<div class="answer markdown-body" data-feedback-answer></div>' +
      '</details>';
    content.querySelector('[data-feedback-mentor]').textContent = 'Feedback from ' + (data.mentor_name || 'mentor');
    content.querySelector('[data-feedback-filename]').textContent = data.filename || '';
    content.querySelector('[data-feedback-answer]').innerHTML = data.output_html || escapeHtml(data.output || '');
    if (subtitle) subtitle.textContent = data.filename ? ('Reviewing ' + data.filename) : 'Your feedback will appear here after an upload.';
    panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function updateProviderLabels(providerLabel, workingLabel, provider) {
    if (providerLabel) {
      document.body.setAttribute('data-provider-label', providerLabel);
      document.querySelectorAll('[data-provider-status-text]').forEach(function (node) {
        node.textContent = providerLabel;
      });
    }
    if (workingLabel) {
      document.body.setAttribute('data-working-label', workingLabel);
      document.querySelectorAll('[data-working-form]').forEach(function (form) {
        form.setAttribute('data-working-label', workingLabel);
      });
    }
    var badge = document.querySelector('[data-provider-badge]');
    if (badge && provider) {
      if (provider === 'ollama') badge.textContent = 'Local Qwen extraction';
      else if (provider === 'openai') badge.textContent = 'OpenAI extraction';
      else if (provider === 'claude' || provider === 'anthropic') badge.textContent = 'Claude extraction';
      else badge.textContent = 'Deterministic local extraction';
    }
  }

  function syncSettingsGroups(form) {
    var provider = (form.querySelector('[data-settings-provider]') || {}).value || 'demo';
    form.querySelectorAll('[data-settings-group]').forEach(function (group) {
      group.hidden = group.getAttribute('data-settings-group') !== provider;
    });
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

    function updatePromptMentorCount(form) {
      if (!form) return;
      var count = form.querySelector('.prompt-mentor-section .mentor-count');
      if (!count) return;
      var total = form.querySelectorAll('[data-prompt-mentor-card]:not([data-create-mentor-card])').length;
      count.textContent = total + (total === 1 ? ' library' : ' libraries');
    }

    function bindPromptMentorInput(input) {
      if (!input || input.getAttribute('data-prompt-mentor-bound') === 'true') return;
      input.setAttribute('data-prompt-mentor-bound', 'true');
      input.addEventListener('change', function () { handleMentorSelectionChange(input); });
    }

    function ensurePromptMentorCard(mentorId, meta) {
      if (!mentorId) return null;
      var form = document.querySelector('.prompt-library-form');
      var grid = form && form.querySelector('[data-prompt-mentor-cards]');
      if (!form || !grid) return null;
      var radio = grid.querySelector('input[name="selected_prompt_mentor"][value="' + mentorId + '"]');
      if (radio) {
        radio.checked = true;
        bindPromptMentorInput(radio);
        updatePromptMentorCards(form);
        toggleMentorCreator(form);
        toggleDeleteMentorButton(form);
        return radio.closest('[data-prompt-mentor-card]');
      }

      var name = (meta && meta.name) || mentorId;
      var description = (meta && meta.description) || 'Stored reference files and generated prompts for this mentor.';
      var status = (meta && meta.status) || 'PI-style library';
      var initials = (meta && meta.initials) || feedbackMentorInitials(name);

      grid.querySelectorAll('input[name="selected_prompt_mentor"]').forEach(function (input) {
        input.checked = false;
      });

      var label = document.createElement('label');
      label.className = 'mentor-card selected';
      label.setAttribute('role', 'radio');
      label.setAttribute('aria-checked', 'true');
      label.setAttribute('data-prompt-mentor-card', '');
      label.setAttribute('data-mentor-deletable', meta && meta.deletable === false ? 'false' : 'true');

      radio = document.createElement('input');
      radio.className = 'visually-hidden-file';
      radio.type = 'radio';
      radio.name = 'selected_prompt_mentor';
      radio.value = mentorId;
      radio.checked = true;
      bindPromptMentorInput(radio);

      var avatar = document.createElement('span');
      avatar.className = 'mentor-avatar';
      avatar.setAttribute('aria-hidden', 'true');
      avatar.textContent = initials;

      var copy = document.createElement('span');
      copy.className = 'mentor-copy';
      var statusNode = document.createElement('span');
      statusNode.className = 'mentor-status';
      statusNode.innerHTML = '<i></i>';
      statusNode.appendChild(document.createTextNode(status));
      var nameNode = document.createElement('strong');
      nameNode.textContent = name;
      var descriptionNode = document.createElement('small');
      descriptionNode.textContent = description;
      copy.appendChild(statusNode);
      copy.appendChild(nameNode);
      copy.appendChild(descriptionNode);

      var selected = document.createElement('span');
      selected.className = 'mentor-selected';
      selected.setAttribute('aria-hidden', 'true');
      selected.innerHTML = '&#10003;';

      label.appendChild(radio);
      label.appendChild(avatar);
      label.appendChild(copy);
      label.appendChild(selected);

      var createCard = grid.querySelector('[data-create-mentor-card]');
      if (createCard) grid.insertBefore(label, createCard);
      else grid.appendChild(label);

      updatePromptMentorCards(form);
      toggleMentorCreator(form);
      toggleDeleteMentorButton(form);
      updatePromptMentorCount(form);
      return label;
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
      if (button) {
        var selectedMentor = selectedMentorValue(form);
        var checked = form.querySelector('input[name="selected_prompt_mentor"]:checked');
        var selectedCard = checked && checked.closest('[data-prompt-mentor-card]');
        var isDeletable = selectedCard && selectedCard.getAttribute('data-mentor-deletable') !== 'false';
        button.hidden = !selectedMentor || !isDeletable;
        button.value = selectedMentor;
      }
    }

    function clearStoredFileDisplays(form) {
      if (!form) return;
      form.querySelectorAll('[data-stored-files]').forEach(function (list) {
        list.textContent = '';
        list.hidden = true;
      });
    }

    function updateStoredFileDisplays(form, storedFiles) {
      if (!form) return;
      form.querySelectorAll('[data-stored-files]').forEach(function (list) {
        var mode = list.getAttribute('data-stored-files');
        var files = (storedFiles && storedFiles[mode]) || [];
        list.textContent = '';
        if (!files.length) {
          list.hidden = true;
          return;
        }
        list.hidden = false;
        files.forEach(function (filename) {
          var item = document.createElement('span');
          item.className = 'stored-file-item';
          item.innerHTML =
            '<span class="selected-file-name stored-file-name"></span>' +
            '<button class="stored-file-delete" type="submit" formaction="/delete-reference-file" formmethod="post" formnovalidate name="delete_reference_file" value="" aria-label=""></button>';
          item.querySelector('.stored-file-name').textContent = filename;
          var button = item.querySelector('button');
          button.value = mode + '|' + filename;
          button.setAttribute('aria-label', 'Delete ' + filename);
          button.textContent = '×';
          list.appendChild(item);
        });
      });
    }

    function updateLibraryNote(name) {
      var note = document.querySelector('[data-prompt-library-note]');
      if (!note) return;
      if (name) {
        note.innerHTML = 'Active library: <strong data-active-library-name></strong>. Uploads accumulate here and prompt TXT files update each time you generate.';
        note.querySelector('[data-active-library-name]').textContent = name;
      } else {
        note.textContent = 'Create a named library or select an existing one. Its reference files and generated prompts stay together on this computer.';
      }
    }

    function syncUrlQuery(params) {
      if (!(window.history && window.history.replaceState)) return;
      var url = new URL(window.location.href);
      Object.keys(params).forEach(function (key) {
        var value = params[key];
        if (value) url.searchParams.set(key, value);
        else url.searchParams.delete(key);
      });
      window.history.replaceState(null, '', url.pathname + url.search + url.hash);
    }

    function selectFeedbackMentor(mentorId, meta) {
      document.querySelectorAll('[data-feedback-mentor-card]').forEach(function (card) {
        var selected = card.getAttribute('data-mentor-id') === mentorId;
        card.classList.toggle('selected', selected);
        if (selected) card.setAttribute('aria-current', 'true');
        else card.removeAttribute('aria-current');
        var mark = card.querySelector('[data-mentor-selected-mark]');
        if (mark) mark.innerHTML = selected ? '&#10003;' : '&rarr;';
      });
      document.querySelectorAll('[data-feedback-mentor-input]').forEach(function (input) {
        input.value = mentorId;
      });
      document.querySelectorAll('[data-feedback-prompt-mentor-input]').forEach(function (input) {
        input.value = meta && meta.source === 'library' ? mentorId : '';
      });
      document.querySelectorAll('[data-feedback-style-name]').forEach(function (node) {
        node.textContent = (meta && meta.name) || mentorId;
      });
      document.querySelectorAll('[data-feedback-style-extra]').forEach(function (node) {
        node.textContent = meta && meta.source === 'library' && meta.description
          ? ' — ' + meta.description
          : '';
      });
      syncUrlQuery({
        mentor: mentorId,
        prompt_mentor: meta && meta.source === 'library' ? mentorId : (new URL(window.location.href)).searchParams.get('prompt_mentor') || ''
      });
    }

    function feedbackMentorInitials(name) {
      var words = String(name || '').toUpperCase().match(/[A-Z0-9]+/g) || [];
      if (!words.length) return 'PI';
      if (words.length === 1) return words[0].slice(0, 2);
      return words.slice(0, 2).map(function (word) { return word.charAt(0); }).join('');
    }

    function updateFeedbackMentorCount() {
      var count = document.querySelector('.feedback-mentor-section .mentor-count');
      if (!count) return;
      var total = document.querySelectorAll('[data-feedback-mentor-card]').length;
      count.textContent = total + (total === 1 ? ' mentor' : ' mentors');
    }

    function bindFeedbackMentorCard(card) {
      if (!card || card.getAttribute('data-feedback-mentor-bound') === 'true') return;
      card.setAttribute('data-feedback-mentor-bound', 'true');
      card.addEventListener('click', function () {
        selectFeedbackMentor(card.getAttribute('data-mentor-id'), {
          name: card.getAttribute('data-mentor-name'),
          source: card.getAttribute('data-mentor-source'),
          description: card.getAttribute('data-mentor-description')
        });
      });
    }

    function ensureFeedbackMentorCard(mentorId, meta) {
      if (!mentorId) return null;
      var grid = document.querySelector('[data-feedback-mentor-cards]');
      if (!grid) return null;
      var card = grid.querySelector('[data-feedback-mentor-card][data-mentor-id="' + mentorId + '"]');
      if (card) {
        bindFeedbackMentorCard(card);
        return card;
      }

      var name = (meta && meta.name) || mentorId;
      var description = (meta && meta.description) || 'Generated and ready for feedback.';
      var status = (meta && meta.status) || 'PI-style library';
      var initials = (meta && meta.initials) || feedbackMentorInitials(name);

      var empty = grid.querySelector('[data-feedback-mentor-empty]');
      if (empty) empty.remove();

      card = document.createElement('button');
      card.type = 'button';
      card.className = 'mentor-card';
      card.setAttribute('role', 'listitem');
      card.setAttribute('data-feedback-mentor-card', '');
      card.setAttribute('data-mentor-id', mentorId);
      card.setAttribute('data-mentor-name', name);
      card.setAttribute('data-mentor-source', 'library');
      card.setAttribute('data-mentor-description', description);

      var avatar = document.createElement('span');
      avatar.className = 'mentor-avatar';
      avatar.setAttribute('aria-hidden', 'true');
      avatar.textContent = initials;

      var copy = document.createElement('span');
      copy.className = 'mentor-copy';
      var statusNode = document.createElement('span');
      statusNode.className = 'mentor-status';
      statusNode.innerHTML = '<i></i>';
      statusNode.appendChild(document.createTextNode(status));
      var nameNode = document.createElement('strong');
      nameNode.textContent = name;
      var descriptionNode = document.createElement('small');
      descriptionNode.textContent = description;
      copy.appendChild(statusNode);
      copy.appendChild(nameNode);
      copy.appendChild(descriptionNode);

      var selected = document.createElement('span');
      selected.className = 'mentor-selected';
      selected.setAttribute('aria-hidden', 'true');
      selected.setAttribute('data-mentor-selected-mark', '');
      selected.innerHTML = '&rarr;';

      card.appendChild(avatar);
      card.appendChild(copy);
      card.appendChild(selected);
      grid.appendChild(card);
      bindFeedbackMentorCard(card);
      updateFeedbackMentorCount();
      return card;
    }

    function activateGeneratedFeedbackMentor(data) {
      if (!data || !data.selected_prompt_mentor) return;
      var mentorId = data.selected_prompt_mentor;
      var mentorName = data.selected_prompt_mentor_name || mentorId;
      var mentorMeta = data.mentors && data.mentors[mentorId]
        ? data.mentors[mentorId]
        : { name: mentorName, source: 'library', status: 'PI-style library', description: 'Generated and ready for feedback.' };
      mentorMeta.name = mentorMeta.name || mentorName;
      mentorMeta.source = 'library';
      ensurePromptMentorCard(mentorId, mentorMeta);
      var card = ensureFeedbackMentorCard(mentorId, mentorMeta);
      if (card) {
        selectFeedbackMentor(mentorId, {
          name: card.getAttribute('data-mentor-name') || mentorName,
          source: 'library',
          description: card.getAttribute('data-mentor-description') || ''
        });
        return;
      }
      document.querySelectorAll('[data-feedback-mentor-input]').forEach(function (input) {
        input.value = mentorId;
      });
      document.querySelectorAll('[data-feedback-prompt-mentor-input]').forEach(function (input) {
        input.value = mentorId;
      });
      document.querySelectorAll('[data-feedback-style-name]').forEach(function (node) {
        node.textContent = mentorName;
      });
      document.querySelectorAll('[data-feedback-style-extra]').forEach(function (node) {
        node.textContent = ' — PI-style library';
      });
    }

    function selectFeedbackType(typeKey) {
      document.querySelectorAll('[data-type-choice]').forEach(function (choice) {
        var selected = choice.getAttribute('data-type-key') === typeKey;
        choice.classList.toggle('selected', selected);
        if (selected) choice.setAttribute('aria-current', 'true');
        else choice.removeAttribute('aria-current');
        var mark = choice.querySelector('[data-type-check]');
        if (mark) mark.innerHTML = selected ? '&#10003;' : '&rarr;';
      });
      document.querySelectorAll('[data-upload-panel]').forEach(function (panel) {
        panel.hidden = panel.getAttribute('data-upload-panel') !== typeKey;
      });
      var prompt = document.querySelector('[data-choose-prompt]');
      var privacy = document.querySelector('[data-feedback-privacy]');
      if (prompt) prompt.hidden = Boolean(typeKey);
      if (privacy) privacy.hidden = !typeKey;
      syncUrlQuery({ type: typeKey || '' });
    }

    function handleMentorSelectionChange(input) {
      var form = input.closest('form');
      updatePromptMentorCards(form);
      toggleMentorCreator(form);
      toggleDeleteMentorButton(form);
      var slug = input.value;

      if (!slug) {
        clearStoredFileDisplays(form);
        updateLibraryNote('');
        renderPromptResults({
          prompt_cards: [],
          prompt_download_urls: {},
          prompt_output_location: '',
          prompt_run_location: '',
          prompt_message: ''
        }, { scroll: false });
        syncUrlQuery({ prompt_mentor: '' });
        return;
      }

      fetch('/api/library/' + encodeURIComponent(slug), {
        headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }
      }).then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok, data: data };
        });
      }).then(function (result) {
        if (!result.ok) {
          setPageError((result.data && result.data.error) || 'Could not load that library.');
          return;
        }
        updateStoredFileDisplays(form, result.data.stored_prompt_files || {});
        updateLibraryNote(result.data.name || slug);
        renderPromptResults(result.data, { scroll: false });
        var feedbackCard = document.querySelector('[data-feedback-mentor-card][data-mentor-id="' + slug + '"]');
        if (feedbackCard) {
          selectFeedbackMentor(slug, {
            name: result.data.name || slug,
            source: 'library',
            description: feedbackCard.getAttribute('data-mentor-description') || ''
          });
        } else {
          syncUrlQuery({ prompt_mentor: slug, mentor: slug });
        }
      }).catch(function () {
        setPageError('Could not load that library.');
      });
    }

    document.querySelectorAll('.prompt-library-form input[name="selected_prompt_mentor"]').forEach(function (input) {
      var form = input.closest('form');
      bindPromptMentorInput(input);
      updatePromptMentorCards(form);
      toggleMentorCreator(form);
      toggleDeleteMentorButton(form);
    });

    document.querySelectorAll('[data-feedback-mentor-card]').forEach(bindFeedbackMentorCard);

    document.querySelectorAll('[data-type-choice]').forEach(function (choice) {
      choice.addEventListener('click', function () {
        selectFeedbackType(choice.getAttribute('data-type-key'));
      });
    });

    document.querySelectorAll('[data-ajax-form]').forEach(function (form) {
      form.addEventListener('submit', function (event) {
        if (event.submitter && event.submitter.getAttribute('formaction')) {
          return;
        }
        if (!form.checkValidity()) {
          return;
        }
        event.preventDefault();
        if (form.getAttribute('data-working-active') === 'true') {
          return;
        }

        var label = form.getAttribute('data-working-label') || currentWorkingLabel();
        var target = form.getAttribute('data-working-target');
        var button = form.querySelector('[data-working-button]');
        var stopButtonAnim = function () {};
        var stopTargetAnim = function () {};

        form.setAttribute('data-working-active', 'true');
        form.classList.add('is-working');
        setPageError('');

        if (button) {
          button.setAttribute('aria-busy', 'true');
          button.innerHTML = '<span data-working-message>' + label + '...</span><span class="working-button-spinner" aria-hidden="true"></span>';
          stopButtonAnim = animateWorkingLabel(button.querySelector('[data-working-message]'), label);
        }
        if (target === 'feedback') {
          stopTargetAnim = showFeedbackWorking(label);
        } else if (target === 'prompts') {
          stopTargetAnim = showPromptsWorking(form, label);
        }

        var body = new FormData(form);
        fetch(form.getAttribute('action'), {
          method: 'POST',
          body: body,
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
          }
        }).then(function (response) {
          return response.json().then(function (data) {
            return { ok: response.ok, status: response.status, data: data };
          }).catch(function () {
            return { ok: false, status: response.status, data: { error: 'Unexpected response from the server.' } };
          });
        }).then(function (result) {
          stopButtonAnim();
          stopTargetAnim();
          form.removeAttribute('data-working-active');
          form.classList.remove('is-working');
          hidePromptsWorking(form);
          hideFeedbackWorking();
          resetWorkingButton(form);

          if (!result.ok) {
            setPageError((result.data && result.data.error) || 'Something went wrong.');
            return;
          }

          if (target === 'prompts') {
            renderPromptResults(result.data);
            activateGeneratedFeedbackMentor(result.data);
            if (result.data.selected_prompt_mentor && window.history && window.history.replaceState) {
              syncUrlQuery({
                prompt_mentor: result.data.selected_prompt_mentor,
                mentor: result.data.selected_mentor || result.data.selected_prompt_mentor
              });
            }
          } else if (target === 'feedback') {
            renderFeedbackResult(result.data);
          }
          if (result.data.provider_label || result.data.working_label) {
            updateProviderLabels(result.data.provider_label, result.data.working_label, result.data.model_provider);
          }
        }).catch(function () {
          stopButtonAnim();
          stopTargetAnim();
          form.removeAttribute('data-working-active');
          form.classList.remove('is-working');
          hidePromptsWorking(form);
          hideFeedbackWorking();
          resetWorkingButton(form);
          setPageError('We could not reach the Promptly server.');
        });
      });
    });

    var settingsDialog = document.querySelector('[data-settings-dialog]');
    var settingsForm = document.querySelector('[data-settings-form]');
    document.querySelectorAll('[data-open-settings]').forEach(function (button) {
      button.addEventListener('click', function () {
        if (!settingsDialog) return;
        syncSettingsGroups(settingsForm);
        if (typeof settingsDialog.showModal === 'function') {
          settingsDialog.showModal();
        } else {
          settingsDialog.setAttribute('open', 'open');
        }
      });
    });

    if (settingsForm) {
      syncSettingsGroups(settingsForm);
      var providerSelect = settingsForm.querySelector('[data-settings-provider]');
      if (providerSelect) {
        providerSelect.addEventListener('change', function () { syncSettingsGroups(settingsForm); });
      }
      settingsForm.addEventListener('submit', function (event) {
        var submitter = event.submitter;
        if (submitter && submitter.value === 'cancel') {
          return;
        }
        event.preventDefault();
        var message = settingsForm.querySelector('[data-settings-message]');
        var payload = {};
        new FormData(settingsForm).forEach(function (value, key) {
          payload[key] = value;
        });
        fetch('/api/settings', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(payload)
        }).then(function (response) {
          return response.json().then(function (data) {
            return { ok: response.ok, data: data };
          });
        }).then(function (result) {
          if (!result.ok) {
            if (message) {
              message.hidden = false;
              message.textContent = (result.data && result.data.error) || 'Could not save settings.';
              message.classList.add('error');
            }
            return;
          }
          updateProviderLabels(result.data.provider_label, result.data.working_label, result.data.model_provider);
          if (message) {
            message.hidden = false;
            message.classList.remove('error');
            message.textContent = 'Settings saved on this computer.';
          }
          window.setTimeout(function () {
            if (typeof settingsDialog.close === 'function') settingsDialog.close();
          }, 650);
        }).catch(function () {
          if (message) {
            message.hidden = false;
            message.classList.add('error');
            message.textContent = 'Could not save settings.';
          }
        });
      });
    }
  });
}());
