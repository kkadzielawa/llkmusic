(function () {
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(';').shift();
        }
        return '';
    }

    function createButton(label, title, action) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'llk-editor-button';
        button.textContent = label;
        button.title = title;
        button.addEventListener('click', action);
        return button;
    }

    function uploadMedia(file) {
        const formData = new FormData();
        formData.append('file', file);

        return fetch('/admin/blog/media-upload/', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        }).then((response) => response.json().then((data) => {
            if (!response.ok) {
                throw new Error(data.error || 'Media upload failed.');
            }
            return data;
        }));
    }

    function escapeAttribute(value) {
        return String(value).replace(/[&<>"']/g, (character) => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;',
        }[character]));
    }

    function cleanEditorHtml(editor) {
        const clone = editor.cloneNode(true);
        clone.querySelectorAll('.is-selected-media').forEach((node) => {
            node.classList.remove('is-selected-media');
        });
        clone.querySelectorAll('[contenteditable]').forEach((node) => {
            node.removeAttribute('contenteditable');
        });
        return clone.innerHTML.trim();
    }

    function insertHtml(editor, html) {
        editor.focus();
        document.execCommand('insertHTML', false, html);
    }

    function insertMediaHtml(editor, html) {
        const mediaHtml = [
            html.replace('<figure ', '<figure contenteditable="false" '),
            '<p><br></p>',
        ].join('');
        insertHtml(editor, mediaHtml);
    }

    function getSelectedMedia(editor) {
        const selection = window.getSelection();
        if (!selection || !selection.rangeCount) {
            return null;
        }

        let node = selection.anchorNode;
        if (node && node.nodeType === Node.TEXT_NODE) {
            node = node.parentElement;
        }

        if (!node || !editor.contains(node)) {
            return null;
        }

        const media = node.closest('figure, img, iframe, video, audio');
        if (!media || !editor.contains(media)) {
            return null;
        }

        return media.closest('figure') || media;
    }

    function applyMediaSize(editor, size, fallbackMedia) {
        const media = fallbackMedia || getSelectedMedia(editor);
        if (!media) {
            return;
        }

        media.classList.remove('media-size-small', 'media-size-medium', 'media-size-large', 'media-size-full');
        media.classList.add(`media-size-${size}`);
        syncEditorMedia(editor);
    }

    function syncEditorMedia(editor) {
        editor.dispatchEvent(new Event('input', { bubbles: true }));
    }

    function extractIframeSrc(input) {
        const match = input.match(/<iframe[^>]+src=["']([^"']+)["']/i);
        return match ? match[1] : input;
    }

    function toYoutubeEmbedUrl(url) {
        const match = url.match(
            /(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([^&?/]+)/
        );
        if (!match) {
            return null;
        }

        return `https://www.youtube.com/embed/${match[1]}?rel=0`;
    }

    function wrapEmbedUrl(url) {
        if (!url) {
            return '';
        }

        let embedUrl = extractIframeSrc(url.trim());
        const youtubeEmbedUrl = toYoutubeEmbedUrl(embedUrl);
        const vimeoMatch = embedUrl.match(/vimeo\.com\/(\d+)/);

        if (youtubeEmbedUrl) {
            embedUrl = youtubeEmbedUrl;
        } else if (vimeoMatch) {
            embedUrl = `https://player.vimeo.com/video/${vimeoMatch[1]}`;
        }

        return [
            '<figure class="media-embed media-size-large">',
            `<iframe src="${escapeAttribute(embedUrl)}" title="Embedded media" loading="lazy" `,
            'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" ',
            'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>',
            '</figure>',
        ].join('');
    }

    function initEditor(textarea) {
        const wrapper = document.createElement('div');
        wrapper.className = 'llk-editor';

        const toolbar = document.createElement('div');
        toolbar.className = 'llk-editor-toolbar';

        const editor = document.createElement('div');
        editor.className = 'llk-editor-canvas';
        editor.contentEditable = 'true';
        editor.innerHTML = textarea.value || '<p></p>';
        editor.setAttribute('aria-label', 'Blog post body editor');

        const status = document.createElement('p');
        status.className = 'llk-editor-status';
        status.setAttribute('role', 'status');

        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*,audio/*';
        fileInput.hidden = true;
        let selectedMedia = null;

        const syncTextarea = () => {
            textarea.value = (
                editor.dataset.mode === 'html' ? editor.textContent : cleanEditorHtml(editor)
            ).trim();
        };

        const exec = (command, value) => {
            editor.focus();
            document.execCommand(command, false, value || null);
            syncTextarea();
        };

        toolbar.append(
            createButton('P', 'Paragraph', () => exec('formatBlock', 'p')),
            createButton('H2', 'Heading 2', () => exec('formatBlock', 'h2')),
            createButton('H3', 'Heading 3', () => exec('formatBlock', 'h3')),
            createButton('B', 'Bold', () => exec('bold')),
            createButton('I', 'Italic', () => exec('italic')),
            createButton('Quote', 'Blockquote', () => exec('formatBlock', 'blockquote')),
            createButton('Bullets', 'Bulleted list', () => exec('insertUnorderedList')),
            createButton('Numbers', 'Numbered list', () => exec('insertOrderedList')),
            createButton('Link', 'Insert link', () => {
                const url = window.prompt('Paste the link URL');
                if (url) {
                    exec('createLink', url);
                }
            }),
            createButton('Image/Audio', 'Upload image or audio', () => fileInput.click()),
            createButton('Video', 'Embed YouTube, Vimeo, or iframe URL', () => {
                const url = window.prompt('Paste a YouTube, Vimeo, or embed URL');
                insertMediaHtml(editor, wrapEmbedUrl(url));
                syncTextarea();
            }),
            createButton('Small', 'Make selected media small', () => applyMediaSize(editor, 'small', selectedMedia)),
            createButton('Medium', 'Make selected media medium', () => applyMediaSize(editor, 'medium', selectedMedia)),
            createButton('Large', 'Make selected media large', () => applyMediaSize(editor, 'large', selectedMedia)),
            createButton('HTML', 'Toggle HTML source', () => {
                const showingHtml = editor.dataset.mode === 'html';
                if (showingHtml) {
                    editor.innerHTML = editor.textContent;
                    editor.dataset.mode = 'visual';
                } else {
                    editor.textContent = editor.innerHTML;
                    editor.dataset.mode = 'html';
                }
                syncTextarea();
            }),
        );

        fileInput.addEventListener('change', () => {
            const file = fileInput.files && fileInput.files[0];
            if (!file) {
                return;
            }

            status.textContent = 'Uploading...';
            uploadMedia(file)
                .then((data) => {
                    if (data.type === 'audio') {
                        insertMediaHtml(editor, `<figure class="media-size-large"><audio controls src="${escapeAttribute(data.location)}"></audio></figure>`);
                    } else {
                        insertMediaHtml(editor, `<figure class="media-size-large"><img src="${escapeAttribute(data.location)}" alt=""></figure>`);
                    }
                    status.textContent = 'Uploaded.';
                    syncTextarea();
                })
                .catch((error) => {
                    status.textContent = error.message;
                })
                .finally(() => {
                    fileInput.value = '';
                });
        });

        editor.addEventListener('input', syncTextarea);
        editor.addEventListener('blur', syncTextarea);
        editor.addEventListener('click', (event) => {
            const media = event.target.closest('figure, img, iframe, video, audio');
            if (!media || !editor.contains(media)) {
                return;
            }

            if (selectedMedia) {
                selectedMedia.classList.remove('is-selected-media');
            }
            selectedMedia = media.closest('figure') || media;
            selectedMedia.classList.add('is-selected-media');
        });

        const form = textarea.closest('form');
        if (form) {
            form.addEventListener('submit', syncTextarea);
        }

        textarea.classList.add('llk-editor-source');
        textarea.hidden = true;
        wrapper.append(toolbar, editor, status, fileInput);
        textarea.parentNode.insertBefore(wrapper, textarea.nextSibling);
    }

    function initEditors() {
        document.querySelectorAll('textarea.rich-blog-editor').forEach(initEditor);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initEditors);
    } else {
        initEditors();
    }
}());
